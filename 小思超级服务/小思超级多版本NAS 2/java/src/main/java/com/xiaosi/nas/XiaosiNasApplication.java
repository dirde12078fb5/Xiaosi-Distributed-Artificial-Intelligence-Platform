package com.xiaosi.nas;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class XiaosiNasApplication {

    public static void main(String[] args) {
        SpringApplication.run(XiaosiNasApplication.class, args);
    }
}