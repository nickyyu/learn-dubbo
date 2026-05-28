import org.apache.flink.api.common.state.MapState;
import org.apache.flink.api.common.state.MapStateDescriptor;
import org.apache.flink.api.common.typeinfo.Types;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.runtime.state.hashmap.HashMapStateBackend;
import org.apache.flink.state.api.SavepointReader;
import org.apache.flink.state.api.functions.KeyedStateReaderFunction;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.util.Collector;

import java.util.Map;

/**
 * 离线分析 Flink Job 状态快照的完整示例
 */
public class ReadCreditExitStateJob {

    public static void main(String[] args) throws Exception {
        // 1. 初始化执行环境 (State Processor API 本质上运行的是一个普通的 Flink 作业)
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        
        // 可选：如果是本地调试，可以把并行度设为 1 方便看日志
        env.setParallelism(1);

        // 2. 指定您的 Savepoint 或 Checkpoint 的绝对路径
        String savepointPath = "file:///path/to/your/savepoint_or_checkpoint_dir";

        // 3. 加载快照数据
        // 注意：这里的 StateBackend 只是用于在读取时反序列化状态数据，
        // 即使您生产环境用的是 RocksDB，这里用 HashMapStateBackend 读取通常也会更快且兼容
        SavepointReader savepoint = SavepointReader.read(env, savepointPath, new HashMapStateBackend());

        // 4. 读取指定算子的 Keyed State
        // 参数1："credit-exit-operator" 是您在原业务代码中给 process 算子设置的 uid()
        // 参数2：自定义的状态读取解析逻辑
        DataStream<String> stateStream = savepoint.readKeyedState(
                "credit-exit-operator",
                new CreditExitStateReader()
        );

        // 5. 将结果输出（可以是 print、写入本地文件，或写入 MySQL 方便排查）
        stateStream.print();

        // 6. 触发执行
        env.execute("Analyze MapState from Savepoint");
    }

    /**
     * 自定义读取函数：输入泛型为 <Key 的类型, 输出的分析结果类型>
     * 假设流的 Key 是用户的 UID (String)
     */
    public static class CreditExitStateReader extends KeyedStateReaderFunction<String, String> {

        // 声明与您业务代码中一模一样的 MapState
        private transient MapState<Long, Integer> creditExitBucketState;

        @Override
        public void open(Configuration parameters) {
            // 这里的名称 "creditExitBucketState" 必须与您原业务代码中定义的状态名称一字不差！
            MapStateDescriptor<Long, Integer> descriptor = new MapStateDescriptor<>(
                    "creditExitBucketState",
                    Types.LONG,
                    Types.INT
            );
            creditExitBucketState = getRuntimeContext().getMapState(descriptor);
        }

        @Override
        public void readKey(String key, Context ctx, Collector<String> out) throws Exception {
            // key 就是用户的 UID
            StringBuilder sb = new StringBuilder();
            sb.append("发现用户状态 -> UID: ").append(key).append(" | 内部桶数据: {");
            
            boolean first = true;
            // 遍历并解析黑盒中的 MapState 数据
            for (Map.Entry<Long, Integer> entry : creditExitBucketState.entries()) {
                if (!first) {
                    sb.append(", ");
                }
                sb.append("桶时间戳(").append(entry.getKey()).append("): ")
                  .append("退出次数(").append(entry.getValue()).append(")");
                first = false;
            }
            sb.append("}");
            
            // 将拼接好的易读字符串发往下游
            out.collect(sb.toString());
        }
    }
}