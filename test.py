<?xml version="1.0" encoding="UTF-8"?>
<!-- monitorInterval="30" 意味着修改此文件无需重启任务，30秒后自动热加载生效 -->
<Configuration status="WARN" monitorInterval="30">
    
    <Appenders>
        <!-- 控制台输出格式：增加了 %c{1.} 使得长包名折叠，日志看起来更整洁 -->
        <Console name="Console" target="SYSTEM_OUT">
            <PatternLayout pattern="%d{yyyy-MM-dd HH:mm:ss.SSS} [%t] %-5level %c{1.} - %msg%n"/>
        </Console>
    </Appenders>

    <Loggers>
        <!-- ========================================================= -->
        <!-- 1. 【降噪区】压制那些极其吵闹，且不出错就不需要关心的组件 -->
        <!-- ========================================================= -->
        
        <!-- 压制 Nacos 心跳和长轮询 -->
        <Logger name="com.alibaba.nacos" level="WARN" additivity="false">
            <AppenderRef ref="Console"/>
        </Logger>
        
        <!-- 压制 Kafka 底层网络消费者不断 Fetch 数据的日志 -->
        <Logger name="org.apache.kafka.clients" level="WARN" additivity="false">
            <AppenderRef ref="Console"/>
        </Logger>
        
        <!-- 压制 Zookeeper 客户端的常规连接日志 (如果 Flink 启用了 HA) -->
        <Logger name="org.apache.zookeeper" level="WARN" additivity="false">
            <AppenderRef ref="Console"/>
        </Logger>

        <!-- ========================================================= -->
        <!-- 2. 【核心关注区】确保关键引擎链路的日志清晰可见 -->
        <!-- ========================================================= -->
        
        <!-- 保留 Flink CDC 的 INFO 日志：能清晰看到它正在读哪个表的哪个 binlog 位点 -->
        <Logger name="com.ververica.cdc" level="INFO" additivity="false">
            <AppenderRef ref="Console"/>
        </Logger>

        <!-- 保留 Flink Checkpoint 的 INFO 日志：能监控每次状态快照是否成功和耗时 -->
        <Logger name="org.apache.flink.runtime.checkpoint" level="INFO" additivity="false">
            <AppenderRef ref="Console"/>
        </Logger>

        <!-- 保留 Flink 任务调度与 TaskManager 生命周期的核心日志 -->
        <Logger name="org.apache.flink.runtime.executiongraph" level="INFO" additivity="false">
            <AppenderRef ref="Console"/>
        </Logger>
        <Logger name="org.apache.flink.runtime.taskmanager" level="INFO" additivity="false">
            <AppenderRef ref="Console"/>
        </Logger>

        <!-- ========================================================= -->
        <!-- 3. 【业务防漏区】全局兜底设置 -->
        <!-- ========================================================= -->
        
        <!-- 你自己写的业务代码 (com.risk.sync) 会走这里的级别 -->
        <!-- 如果你想单独调试你的清洗逻辑，可以把这里改成 DEBUG -->
        <Logger name="com.risk.sync" level="INFO" additivity="false">
            <AppenderRef ref="Console"/>
        </Logger>

        <!-- 全局 Root 兜底配置：其余未匹配到的类统一按 INFO 输出 -->
        <Root level="INFO">
            <AppenderRef ref="Console"/>
        </Root>
    </Loggers>
</Configuration>