<?xml version="1.0" encoding="UTF-8"?>
<Configuration status="WARN">

    <!-- 1. 定义全局变量，方便统一修改 -->
    <Properties>
        <!-- 【极其重要】这里改成你服务器上实际的日志目录路径 -->
        <Property name="LOG_HOME">/app/logs/flink/fkxt</Property>
        <Property name="APP_NAME">risk-feature-job</Property>
    </Properties>

    <Appenders>
        <!-- 2. 配置滚动文件归档策略 -->
        <RollingFile name="RollingFile" 
                     fileName="${LOG_HOME}/${APP_NAME}.log"
                     filePattern="${LOG_HOME}/$${date:yyyy-MM}/${APP_NAME}-%d{yyyy-MM-dd}-%i.log.gz">
            
            <PatternLayout pattern="%d{yyyy-MM-dd HH:mm:ss.SSS} [%t] %-5level %logger{36} - %msg%n"/>
            
            <Policies>
                <!-- 策略一：按天归档（配合 filePattern 里的 %d{yyyy-MM-dd} 使用） -->
                <TimeBasedTriggeringPolicy interval="1" modulate="true"/>
                <!-- 策略二：如果一天内日志太多，单文件超过 100MB，自动触发切分 (-%i 会递增) -->
                <SizeBasedTriggeringPolicy size="100 MB"/>
            </Policies>
            
            <!-- 3. 配置日志保留与自动清理策略 -->
            <DefaultRolloverStrategy max="50">
                <!-- 自动删除 ${LOG_HOME} 目录下，15天前的 .gz 压缩包 -->
                <Delete basePath="${LOG_HOME}" maxDepth="2">
                    <IfFileName glob="*/${APP_NAME}-*.log.gz"/>
                    <IfLastModified age="15d"/>
                </Delete>
            </DefaultRolloverStrategy>
        </RollingFile>
    </Appenders>

    <Loggers>
        <Root level="INFO">
            <!-- 指向上面配置的 RollingFile -->
            <AppenderRef ref="RollingFile"/>
        </Root>

        <!-- 业务代码，生产环境建议改成 INFO，只记录关键节点，避免日志疯狂刷盘影响性能 -->
        <Logger name="com.ymbank.fkxt.sdk.stream" level="INFO" additivity="false">
            <AppenderRef ref="RollingFile"/>
        </Logger>

        <!-- 屏蔽底层组件的啰嗦日志 -->
        <Logger name="org.apache.flink" level="INFO" additivity="false">
            <AppenderRef ref="RollingFile"/>
        </Logger>
        <Logger name="org.apache.kafka" level="WARN" additivity="false">
            <AppenderRef ref="RollingFile"/>
        </Logger>
    </Loggers>
</Configuration>



<build>
    <plugins>
        <!-- Java 编译器插件 -->
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-compiler-plugin</artifactId>
            <version>3.8.1</version>
            <configuration>
                <source>1.8</source> <!-- 确保与你的 JDK 版本一致 -->
                <target>1.8</target>
            </configuration>
        </plugin>

        <!-- Shade 胖包插件 -->
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-shade-plugin</artifactId>
            <version>3.2.4</version>
            <executions>
                <execution>
                    <phase>package</phase>
                    <goals>
                        <goal>shade</goal>
                    </goals>
                    <configuration>
                        <artifactSet>
                            <excludes>
                                <!-- 排除不必要的元数据，减小包体积 -->
                                <exclude>org.apache.flink:force-shading</exclude>
                                <exclude>com.google.code.findbugs:jsr305</exclude>
                                <exclude>org.slf4j:*</exclude>
                                <exclude>log4j:*</exclude>
                            </excludes>
                        </artifactSet>
                        <filters>
                            <!-- 过滤掉签名文件，防止报 Invalid signature 错误 -->
                            <filter>
                                <artifact>*:*</artifact>
                                <excludes>
                                    <exclude>META-INF/*.SF</exclude>
                                    <exclude>META-INF/*.DSA</exclude>
                                    <exclude>META-INF/*.RSA</exclude>
                                </excludes>
                            </filter>
                        </filters>
                        <transformers>
                            <!-- 合并 SPI 文件（非常关键，否则 MySQL 驱动可能会报错） -->
                            <transformer implementation="org.apache.maven.plugins.shade.resource.ServicesResourceTransformer"/>
                            <!-- 指定你的启动主类，这样提交任务时就不用手敲类名了 -->
                            <transformer implementation="org.apache.maven.plugins.shade.resource.ManifestResourceTransformer">
                                <mainClass>com.ymbank.fkxt.sdk.stream.MetricJob</mainClass> <!-- 【改这里！】换成你自己的 Main 类全路径 -->
                            </transformer>
                        </transformers>
                    </configuration>
                </execution>
            </executions>
        </plugin>
    </plugins>
</build>