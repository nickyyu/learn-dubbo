package com.risk.sync.function;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.risk.sync.model.BlacklistSyncEvent;
import org.apache.flink.api.common.functions.RichFlatMapFunction;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.util.Collector;

public class DebeziumParserFunction extends RichFlatMapFunction<String, BlacklistSyncEvent> {

    // 必须为 transient，不可被 Flink 跨网络序列化
    private transient ObjectMapper objectMapper;

    @Override
    public void open(Configuration parameters) throws Exception {
        // 在 TaskManager 线程中实例化 Jackson ObjectMapper
        this.objectMapper = new ObjectMapper();
    }

    @Override
    public void flatMap(String value, Collector<BlacklistSyncEvent> out) throws Exception {
        JsonNode rootNode = objectMapper.readTree(value);
        if (rootNode == null || !rootNode.has("op") || rootNode.get("op").isNull()) {
            return;
        }

        String op = rootNode.get("op").asText();
        JsonNode dataNode;
        String syncAction;

        // 判断 CDC 操作动作
        if ("d".equals(op)) {
            dataNode = rootNode.get("before"); // 删除操作拿旧数据
            syncAction = "DELETE";
        } else {
            dataNode = rootNode.get("after");  // 新增/更新/全量读拿新数据
            syncAction = "UPSERT";
        }

        // 清洗与映射
        if (dataNode != null && !dataNode.isNull()) {
            String idCard = dataNode.hasNonNull("id_card") ? dataNode.get("id_card").asText() : null;
            String riskType = dataNode.hasNonNull("risk_type") ? dataNode.get("risk_type").asText() : null;
            String reason = dataNode.hasNonNull("reason") ? dataNode.get("reason").asText() : null;
            long createTime = dataNode.hasNonNull("create_time") ? dataNode.get("create_time").asLong() : 0L;

            if (idCard != null && !idCard.trim().isEmpty()) {
                out.collect(new BlacklistSyncEvent(syncAction, idCard.trim(), riskType, reason, createTime));
            }
        }
    }
}

package com.risk.sync.model;

import java.io.Serializable;

public class BlacklistSyncEvent implements Serializable {
    public String syncAction; // "UPSERT" 或 "DELETE"
    public String idCard;
    public String riskType;
    public String reason;
    public long createTime;

    public BlacklistSyncEvent() {} // Jackson 反序列化需要无参构造

    public BlacklistSyncEvent(String syncAction, String idCard, String riskType, String reason, long createTime) {
        this.syncAction = syncAction;
        this.idCard = idCard;
        this.riskType = riskType;
        this.reason = reason;
        this.createTime = createTime;
    }
}

package com.risk.sync.function;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.risk.sync.model.BlacklistSyncEvent;
import org.apache.flink.api.java.utils.ParameterTool;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.streaming.api.functions.sink.RichSinkFunction;
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;
import redis.clients.jedis.JedisPoolConfig;

public class JedisSinkFunction extends RichSinkFunction<BlacklistSyncEvent> {

    private transient JedisPool jedisPool;
    private transient ObjectMapper objectMapper;
    private static final String REDIS_KEY_PREFIX = "risk:blacklist:idcard:";

    @Override
    public void open(Configuration parameters) throws Exception {
        this.objectMapper = new ObjectMapper();

        ParameterTool globalParams = (ParameterTool) getRuntimeContext()
                .getExecutionConfig().getGlobalJobParameters();

        String host = globalParams.getRequired("redis.host");
        int port = globalParams.getInt("redis.port", 6379);
        String password = globalParams.get("redis.password", "");
        int db = globalParams.getInt("redis.db", 0);

        JedisPoolConfig poolConfig = new JedisPoolConfig();
        poolConfig.setMaxTotal(50);
        poolConfig.setMaxIdle(10);
        poolConfig.setTestOnBorrow(true);

        if (password.isEmpty()) {
            jedisPool = new JedisPool(poolConfig, host, port, 5000);
        } else {
            jedisPool = new JedisPool(poolConfig, host, port, 5000, password, db);
        }
    }

    @Override
    public void invoke(BlacklistSyncEvent event, Context context) throws Exception {
        String redisKey = REDIS_KEY_PREFIX + event.idCard;

        try (Jedis jedis = jedisPool.getResource()) {
            if ("DELETE".equals(event.syncAction)) {
                jedis.del(redisKey);
            } else if ("UPSERT".equals(event.syncAction)) {
                // 将 POJO 序列化为 JSON 写入 Redis
                String jsonString = objectMapper.writeValueAsString(event);
                jedis.set(redisKey, jsonString);
            }
        }
    }

    @Override
    public void close() throws Exception {
        if (jedisPool != null && !jedisPool.isClosed()) {
            jedisPool.close();
        }
    }
}

package com.risk.sync;

import com.alibaba.nacos.api.NacosFactory;
import com.alibaba.nacos.api.config.ConfigService;
import com.risk.sync.function.DebeziumParserFunction;
import com.risk.sync.function.JedisSinkFunction;
import com.risk.sync.model.BlacklistSyncEvent;
import com.ververica.cdc.connectors.mysql.source.MySqlSource;
import com.ververica.cdc.debezium.JsonDebeziumDeserializationSchema;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.java.utils.ParameterTool;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.util.Properties;

public class BlacklistSyncJob {

    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        // 1. 本地引导配置加载
        ParameterTool cliParams = ParameterTool.fromArgs(args);
        String envName = cliParams.get("env", "prd");
        
        System.out.println("====== 加载环境引导: application-" + envName + ".properties ======");
        ParameterTool bootstrapParams;
        try (InputStream is = BlacklistSyncJob.class.getClassLoader()
                .getResourceAsStream("application-" + envName + ".properties")) {
            bootstrapParams = ParameterTool.fromPropertiesFile(is);
        }

        // 2. Nacos 远程配置拉取
        Properties nacosProps = new Properties();
        nacosProps.put("serverAddr", bootstrapParams.getRequired("nacos.server-addr"));
        nacosProps.put("namespace", bootstrapParams.getRequired("nacos.namespace"));

        ConfigService configService = NacosFactory.createConfigService(nacosProps);
        String remoteConfig = configService.getConfig(
                bootstrapParams.getRequired("nacos.data-id"),
                bootstrapParams.getRequired("nacos.group"),
                5000
        );

        ParameterTool remoteParams = ParameterTool.fromPropertiesFile(
                new ByteArrayInputStream(remoteConfig.getBytes("UTF-8")));

        // 3. 全局参数合并与注册
        ParameterTool globalParams = bootstrapParams.mergeWith(remoteParams).mergeWith(cliParams);
        env.getConfig().setGlobalJobParameters(globalParams);

        // 验证: 打印拿到的 Kafka 备用配置
        System.out.println("成功加载 Nacos 配置，包含 Kafka 节点: " + globalParams.get("kafka.bootstrap.servers"));

        // 4. 构建 MySQL CDC Source
        MySqlSource<String> mySqlSource = MySqlSource.<String>builder()
                .hostname(globalParams.getRequired("mysql.host"))
                .port(globalParams.getInt("mysql.port", 3306))
                .databaseList(globalParams.getRequired("mysql.db"))
                .tableList(globalParams.getRequired("mysql.table"))
                .username(globalParams.getRequired("mysql.user"))
                .password(globalParams.getRequired("mysql.password"))
                // false: 不包含 Debezium 冗余的 schema 元数据，仅输出核心数据负载
                .deserializer(new JsonDebeziumDeserializationSchema(false))
                .build();

        // 5. 数据流处理拓扑
        DataStream<String> cdcRawStream = env.fromSource(
                mySqlSource,
                WatermarkStrategy.noWatermarks(), // CDC 到 Redis 侧不需要容忍乱序的水印
                "MySQL Blacklist Source"
        );

        DataStream<BlacklistSyncEvent> cleanStream = cdcRawStream
                .flatMap(new DebeziumParserFunction())
                .name("Jackson Parse & Clean");

        cleanStream
                .addSink(new JedisSinkFunction())
                .name("Redis Jedis Sink");

        // 6. 开启 Checkpoint 保障 exactly-once
        env.enableCheckpointing(60000);

        env.execute("MySQL Blacklist to Redis Sync Job - " + envName);
    }
}