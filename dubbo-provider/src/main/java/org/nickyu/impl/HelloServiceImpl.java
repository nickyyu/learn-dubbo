package org.nickyu.impl;

import org.apache.dubbo.config.annotation.DubboService;
import org.nickyu.api.HelloService;

@DubboService
public class HelloServiceImpl implements HelloService {
    @Override
    public String say(String name) {
        return "annotation :hello,"+name;
    }
}
