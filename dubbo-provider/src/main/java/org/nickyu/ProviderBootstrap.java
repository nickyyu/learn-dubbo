package org.nickyu;

import org.nickyu.config.ProviderConfiguration;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;

import java.util.concurrent.CountDownLatch;

/**
 * Hello world!
 *
 */
public class ProviderBootstrap
{
    private static Logger logger = LoggerFactory.getLogger(ProviderBootstrap.class);

    public static void main( String[] args ) throws InterruptedException {
        AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(ProviderConfiguration.class);
        context.start();

        logger.info("dubbo service started.");
        new CountDownLatch(1).await();
    }
}
