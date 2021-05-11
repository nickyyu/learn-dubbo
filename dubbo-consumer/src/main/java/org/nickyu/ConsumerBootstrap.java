package org.nickyu;

import org.nickyu.action.AnnotationAction;
import org.nickyu.config.ConsumerConfiguration;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;

/**
 * Hello world!
 *
 */
public class ConsumerBootstrap
{
    public static void main( String[] args )
    {
        AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(ConsumerConfiguration.class);
        context.start();

        final AnnotationAction annotationAction = (AnnotationAction) context.getBean("annotationAction");
        System.out.println("hello : " + annotationAction.doSay("world"));
    }
}
