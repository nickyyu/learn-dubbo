// 1. 清洗后的源数据模型
public class UserDeviceEvent {
    public String fuid;
    public String deviceId;
    public long eventTime;
    
    public UserDeviceEvent(String fuid, String deviceId, long eventTime) {
        this.fuid = fuid;
        this.deviceId = deviceId;
        this.eventTime = eventTime;
    }
}

// 2. 统计结果模型
public class UserDeviceMetric {
    public String fuid;
    public long distinctDeviceCount;
    public long updateTime; // 记录计算出的真实时间

    public UserDeviceMetric(String fuid, long distinctDeviceCount, long updateTime) {
        this.fuid = fuid;
        this.distinctDeviceCount = distinctDeviceCount;
        this.updateTime = updateTime;
    }
}



import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.functions.FlatMapFunction;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.connector.jdbc.JdbcConnectionOptions;
import org.apache.flink.connector.jdbc.JdbcExecutionOptions;
import org.apache.flink.connector.jdbc.JdbcSink;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.util.Collector;

import java.time.Duration;

public class DeviceFingerprintMetricJob {

    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        // 生产环境必须开启 Checkpoint 保障 Exactly-Once
        env.enableCheckpointing(10000); 

        // 1. 构建 Kafka Source (FLIP-27 规范)
        KafkaSource<String> kafkaSource = KafkaSource.<String>builder()
                .setBootstrapServers("127.0.0.1:9092")
                .setTopics("cdc_app_event_topic")
                .setGroupId("risk_metric_group")
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new SimpleStringSchema())
                .build();

        // 2. 接入数据并进行 JSON 解析与清洗
        DataStream<UserDeviceEvent> parsedStream = env
                .fromSource(kafkaSource, WatermarkStrategy.noWatermarks(), "Kafka Source")
                .flatMap(new CdcJsonParser())
                .name("Parse CDC JSON");

        // 3. 分配时间戳与水位线 (容忍 3 秒乱序)
        DataStream<UserDeviceEvent> watermarkedStream = parsedStream
                .assignTimestampsAndWatermarks(
                        WatermarkStrategy.<UserDeviceEvent>forBoundedOutOfOrderness(Duration.ofSeconds(3))
                                .withTimestampAssigner((event, timestamp) -> event.eventTime)
                );

        // 4. 核心计算：按 UID 分组，使用 ProcessFunction 计算近 24 小时去重设备数
        DataStream<UserDeviceMetric> metricStream = watermarkedStream
                .keyBy(event -> event.fuid)
                .process(new RollingDeviceCountFunction())
                .name("Calculate 24H Distinct Devices");

        // 5. 写入 MySQL (达成“5秒出结果”的核心：微批 Upsert)
        metricStream.addSink(
                JdbcSink.sink(
                        // 使用 ON DUPLICATE KEY UPDATE 实现结果的不断刷新
                        "INSERT INTO user_device_metric_24h (fuid, device_count, update_time) " +
                        "VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE " +
                        "device_count = VALUES(device_count), update_time = VALUES(update_time)",
                        (statement, metric) -> {
                            statement.setString(1, metric.fuid);
                            statement.setLong(2, metric.distinctDeviceCount);
                            statement.setLong(3, metric.updateTime);
                        },
                        JdbcExecutionOptions.builder()
                                .withBatchSize(1000)
                                // 【关键性能配置】：每 5 秒强制刷写一次到 MySQL，满足实时性要求且不压垮 DB
                                .withBatchIntervalMs(5000) 
                                .withMaxRetries(3)
                                .build(),
                        new JdbcConnectionOptions.JdbcConnectionOptionsBuilder()
                                .withUrl("jdbc:mysql://127.0.0.1:3306/risk_db?rewriteBatchedStatements=true")
                                .withDriverName("com.mysql.cj.jdbc.Driver")
                                .withUsername("root")
                                .withPassword("123456")
                                .build()
                )
        ).name("MySQL Upsert Sink");

        env.execute("24H User Device Fingerprint Metric Job");
    }

    // --- 内部类实现 ---

    /**
     * 步骤 A：解析 Flink CDC 产生的复杂 JSON
     */
    public static class CdcJsonParser implements FlatMapFunction<String, UserDeviceEvent> {
        private transient ObjectMapper mapper;

        @Override
        public void flatMap(String value, Collector<UserDeviceEvent> out) throws Exception {
            if (mapper == null) mapper = new ObjectMapper();
            
            JsonNode root = mapper.readTree(value);
            // 过滤掉 Delete 操作，只处理 Create/Update/Read 快照
            if (!root.has("op") || "d".equals(root.get("op").asText())) return;
            if (!root.has("after") || root.get("after").isNull()) return;

            JsonNode after = root.get("after");
            String fuid = after.get("Fuid").asText();
            
            // 解析嵌套的 Fbusiness_info JSON 提取指纹
            // 假设埋点里的指纹 Key 叫 "device_fp"
            String bizInfoStr = after.get("Fbusiness_info").asText();
            JsonNode bizInfo = mapper.readTree(bizInfoStr);
            if (!bizInfo.has("device_fp")) return; 
            String deviceId = bizInfo.get("device_fp").asText();

            // 假设 Fcreate_time 抽取出来是长整型的时间戳 (毫秒)
            long eventTime = after.get("Fcreate_time").asLong();

            out.collect(new UserDeviceEvent(fuid, deviceId, eventTime));
        }
    }
}


import org.apache.flink.api.common.state.MapState;
import org.apache.flink.api.common.state.MapStateDescriptor;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.streaming.api.functions.KeyedProcessFunction;
import org.apache.flink.util.Collector;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

public class RollingDeviceCountFunction extends KeyedProcessFunction<String, UserDeviceEvent, UserDeviceMetric> {

    // 状态：存储该用户使用过的各个设备，以及最后一次使用的时间戳
    // Key: deviceId, Value: lastEventTime
    private transient MapState<String, Long> deviceTimeState;
    private static final long TWENTY_FOUR_HOURS_MS = 24 * 60 * 60 * 1000L;

    @Override
    public void open(Configuration parameters) {
        MapStateDescriptor<String, Long> descriptor = 
                new MapStateDescriptor<>("device-time-state", String.class, Long.class);
        deviceTimeState = getRuntimeContext().getMapState(descriptor);
    }

    @Override
    public void processElement(UserDeviceEvent event, Context ctx, Collector<UserDeviceMetric> out) throws Exception {
        long currentEventTime = event.eventTime;
        
        // 1. 更新该设备的最后活跃时间
        deviceTimeState.put(event.deviceId, currentEventTime);

        // 2. 注册一个 24 小时后的定时器，用于自动清理过期设备
        // 注意：如果该设备后续又有新活跃，时间被覆盖，定时器依然会触发，但我们在 onTimer 中会做条件校验
        ctx.timerService().registerEventTimeTimer(currentEventTime + TWENTY_FOUR_HOURS_MS);

        // 3. 计算当前窗口内（基于最新的 Watermark 向前推 24 小时）的去重设备数
        long count = calculateActiveDevices(ctx.timerService().currentWatermark());
        
        // 4. 立即向下游发射最新结果
        out.collect(new UserDeviceMetric(event.fuid, count, System.currentTimeMillis()));
    }

    @Override
    public void onTimer(long timestamp, OnTimerContext ctx, Collector<UserDeviceMetric> out) throws Exception {
        // 定时器触发，意味着有设备可能超过 24 小时未活跃了，执行物理清理
        long currentWatermark = ctx.timerService().currentWatermark();
        long threshold = currentWatermark - TWENTY_FOUR_HOURS_MS;
        
        List<String> expiredDevices = new ArrayList<>();
        long activeCount = 0;

        Iterator<Map.Entry<String, Long>> iterator = deviceTimeState.entries().iterator();
        while (iterator.hasNext()) {
            Map.Entry<String, Long> entry = iterator.next();
            if (entry.getValue() <= threshold) {
                // 已经 24 小时没见过这个设备了，标记删除
                expiredDevices.add(entry.getKey());
            } else {
                activeCount++;
            }
        }

        for (String deviceId : expiredDevices) {
            deviceTimeState.remove(deviceId);
        }

        // 当有过期的设备被真正移除时，意味着指标发生变化，触发一次计算下发给 MySQL
        if (!expiredDevices.isEmpty()) {
            out.collect(new UserDeviceMetric(ctx.getCurrentKey(), activeCount, System.currentTimeMillis()));
        }
    }

    /**
     * 辅助方法：遍历状态，计算仍处于 24 小时窗口内的有效设备数
     */
    private long calculateActiveDevices(long currentWatermark) throws Exception {
        long count = 0;
        long threshold = currentWatermark - TWENTY_FOUR_HOURS_MS;
        for (Long lastActiveTime : deviceTimeState.values()) {
            // 只统计 24 小时内活跃过的设备
            if (lastActiveTime > threshold) {
                count++;
            }
        }
        return count;
    }
}


<properties>
    <maven.compiler.source>11</maven.compiler.source>
    <maven.compiler.target>11</maven.compiler.target>
    <flink.version>1.20.0</flink.version>
</properties>

<dependencies>
    <!-- Flink 1.20 核心依赖 -->
    <dependency>
        <groupId>org.apache.flink</groupId>
        <artifactId>flink-streaming-java</artifactId>
        <version>${flink.version}</version>
        <scope>provided</scope>
    </dependency>
    <dependency>
        <groupId>org.apache.flink</groupId>
        <artifactId>flink-clients</artifactId>
        <version>${flink.version}</version>
        <scope>provided</scope>
    </dependency>

    <!-- Flink 官方 Kafka 连接器 (1.20 专属版本) -->
    <dependency>
        <groupId>org.apache.flink</groupId>
        <artifactId>flink-connector-kafka</artifactId>
        <version>3.3.0-1.20</version>
    </dependency>

    <!-- Flink 官方 JDBC 连接器 (3.2.0 版本完美兼容 1.19/1.20) -->
    <dependency>
        <groupId>org.apache.flink</groupId>
        <artifactId>flink-connector-jdbc</artifactId>
        <version>3.2.0-1.19</version>
    </dependency>

    <!-- MySQL 官方驱动 -->
    <dependency>
        <groupId>com.mysql</groupId>
        <artifactId>mysql-connector-j</artifactId>
        <version>8.3.0</version>
    </dependency>

    <!-- Jackson JSON 处理 -->
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
        <version>2.15.2</version>
    </dependency>
</dependencies>