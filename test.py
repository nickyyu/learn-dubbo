import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

public class OrderEvent {
    public String uid;
    public String orderId;
    public Long createTime; 
    public String op;       

    public static OrderEvent fromCdcJson(String jsonStr) {
        try {
            // Gson 解析入口
            JsonObject root = JsonParser.parseString(jsonStr).getAsJsonObject();
            
            // 提取操作类型 (op)
            String op = getStringSafe(root, "op");
            
            // 获取 after 节点
            JsonElement afterElement = root.get("after");
            if (afterElement != null && !afterElement.isJsonNull()) {
                JsonObject after = afterElement.getAsJsonObject();
                
                OrderEvent event = new OrderEvent();
                event.op = op;
                
                // 使用安全辅助方法提取业务字段
                event.uid = getStringSafe(after, "Fuid");
                event.orderId = getStringSafe(after, "Frc_order_id");
                event.createTime = getLongSafe(after, "Fcreate_time");
                
                // 数据完整性校验，必须包含风控核心三要素才向下游发送
                if (event.uid != null && event.orderId != null && event.createTime != null) {
                    return event;
                }
            }
        } catch (Exception e) {
            // 生产环境建议：将抛出异常的 jsonStr 发送到 Side Output (侧输出流) 或打入 Error Logger
        }
        return null;
    }

    // ================== 辅助安全提取方法 ==================

    /**
     * 安全提取 String 字段，防止 NullPointerException
     */
    private static String getStringSafe(JsonObject obj, String key) {
        JsonElement element = obj.get(key);
        return (element != null && !element.isJsonNull()) ? element.getAsString() : null;
    }

    /**
     * 安全提取 Long 字段，防止 NullPointerException
     */
    private static Long getLongSafe(JsonObject obj, String key) {
        JsonElement element = obj.get(key);
        return (element != null && !element.isJsonNull()) ? element.getAsLong() : null;
    }
}





import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;

import java.time.Duration;

public class UserOrderVelocityJob {

    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.enableCheckpointing(60000); 

        // 假设 CDC 数据已经进入 Kafka
        KafkaSource<String> kafkaSource = KafkaSource.<String>builder()
                .setBootstrapServers("your_kafka_broker:9092")
                .setTopics("mysql_cdc_t_rc_order_info")
                .setGroupId("flink-risk-order-velocity")
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new SimpleStringSchema())
                .build();

        env.fromSource(kafkaSource, WatermarkStrategy.noWatermarks(), "MySQL CDC Source")
                .map(OrderEvent::fromCdcJson)
                .filter(event -> event != null)
                // 风控场景：通常我们只统计进件/下单动作，即使最终失败，申请行为本身也代表了风险意图
                // 但如果明确需要排除物理删除的数据，可以加一句：.filter(event -> !"d".equals(event.op))
                .assignTimestampsAndWatermarks(
                        WatermarkStrategy.<OrderEvent>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                                .withTimestampAssigner((event, timestamp) -> event.createTime)
                )
                // 按 Fuid 分组计算
                .keyBy(event -> event.uid)
                // 接入 24 小时去重统计
                .process(new SlidingOrderDistinctProcessFunction())
                .print("Velocity Result");

        env.execute("Risk Feature: User 24H Order Count");
    }
}



import org.apache.flink.api.common.state.MapState;
import org.apache.flink.api.common.state.MapStateDescriptor;
import org.apache.flink.api.common.typeinfo.Types;
import org.apache.flink.api.java.tuple.Tuple2;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.streaming.api.functions.KeyedProcessFunction;
import org.apache.flink.util.Collector;

import java.util.Iterator;
import java.util.Map;

/**
 * 输出：Tuple2<String, Integer> -> <Fuid, 近24小时的去重订单数>
 */
public class SlidingOrderDistinctProcessFunction extends KeyedProcessFunction<String, OrderEvent, Tuple2<String, Integer>> {

    // 状态：记录该 UID 下，每个 OrderId 对应的创建时间
    private transient MapState<String, Long> orderState;

    private static final long WINDOW_SIZE_MS = 24 * 60 * 60 * 1000L;

    @Override
    public void open(Configuration parameters) throws Exception {
        MapStateDescriptor<String, Long> descriptor = new MapStateDescriptor<>(
                "uid-order-state",
                Types.STRING,
                Types.LONG
        );
        orderState = getRuntimeContext().getMapState(descriptor);
    }

    @Override
    public void processElement(OrderEvent value, Context ctx, Collector<Tuple2<String, Integer>> out) throws Exception {
        long currentEventTime = value.createTime;
        
        // Flink CDC UPDATE 消息放大处理：
        // 即使一条订单被 UPDATE 多次，由于 Map 的 Key 相同，它只会更新 Value（或者幂等写入），
        // 从而完美实现 "去重" 目标。
        orderState.put(value.orderId, currentEventTime);

        // 注册 24 小时后的定时器，用于精准踢出过期订单
        ctx.timerService().registerEventTimeTimer(currentEventTime + WINDOW_SIZE_MS);

        // 输出最新聚合特征
        out.collect(Tuple2.of(value.uid, getOrderCount()));
    }

    @Override
    public void onTimer(long timestamp, OnTimerContext ctx, Collector<Tuple2<String, Integer>> out) throws Exception {
        long cutoffTime = timestamp - WINDOW_SIZE_MS;

        Iterator<Map.Entry<String, Long>> iterator = orderState.iterator();
        boolean stateChanged = false;

        while (iterator.hasNext()) {
            Map.Entry<String, Long> entry = iterator.next();
            // 如果该订单的创建时间已经落后于 24 小时前，则将其从状态中剔除
            if (entry.getValue() <= cutoffTime) {
                iterator.remove();
                stateChanged = true;
            }
        }

        // 仅在数据过期导致总数发生变化时，才向下游发送最新的特征值
        if (stateChanged) {
            out.collect(Tuple2.of(ctx.getCurrentKey(), getOrderCount()));
        }
    }

    private int getOrderCount() throws Exception {
        int count = 0;
        // MapState.keys() 的迭代在 RocksDB 后端下只会在反序列化 Key 时产生开销，
        // 考虑到单用户的 24 小时订单量通常在个位数到十位数级别，这里的性能损耗微乎其微。
        for (String ignored : orderState.keys()) {
            count++;
        }
        return count;
    }
}