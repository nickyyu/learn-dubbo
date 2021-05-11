package org.nickyu;

import java.util.concurrent.CountDownLatch;

/**
 * Hello world!
 *
 */
public class ZookeeperBootstrap
{
    public static void main( String[] args )
    {
       new EmbeddedZooKeeper(2181,false).start();
        try {
            new CountDownLatch(1).await();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }
}
