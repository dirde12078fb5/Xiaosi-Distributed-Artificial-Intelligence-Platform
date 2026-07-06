package com.xiaosi.nas.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import jakarta.annotation.PostConstruct;
import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class ConfigService {

    @Value("${nas.config-path:../config/config.json}")
    private String configPath;

    private final ObjectMapper objectMapper = new ObjectMapper();
    private Map<String, Object> config = new HashMap<>();

    @PostConstruct
    public void init() {
        loadConfig();
    }

    public void loadConfig() {
        File file = new File(configPath);
        if (file.exists()) {
            try {
                config = objectMapper.readValue(file, Map.class);
                log.info("配置文件加载成功: {}", configPath);
            } catch (IOException e) {
                log.error("加载配置文件失败: {}", e.getMessage());
                config = new HashMap<>();
            }
        } else {
            log.warn("配置文件不存在: {}", configPath);
        }
    }

    public void saveConfig() {
        try {
            File file = new File(configPath);
            file.getParentFile().mkdirs();
            objectMapper.writerWithDefaultPrettyPrinter().writeValue(file, config);
            log.info("配置文件保存成功: {}", configPath);
        } catch (IOException e) {
            log.error("保存配置文件失败: {}", e.getMessage());
            throw new RuntimeException("保存配置文件失败: " + e.getMessage());
        }
    }

    public Map<String, Object> getConfig() {
        return new HashMap<>(config);
    }

    @SuppressWarnings("unchecked")
    public <T> T get(String key, T defaultValue) {
        String[] keys = key.split("\\.");
        Map<String, Object> current = config;
        
        for (int i = 0; i < keys.length - 1; i++) {
            Object value = current.get(keys[i]);
            if (value instanceof Map) {
                current = (Map<String, Object>) value;
            } else {
                return defaultValue;
            }
        }
        
        Object result = current.get(keys[keys.length - 1]);
        return result != null ? (T) result : defaultValue;
    }

    @SuppressWarnings("unchecked")
    public void set(String key, Object value) {
        String[] keys = key.split("\\.");
        Map<String, Object> current = config;
        
        for (int i = 0; i < keys.length - 1; i++) {
            current = (Map<String, Object>) current.computeIfAbsent(keys[i], k -> new HashMap<>());
        }
        
        current.put(keys[keys.length - 1], value);
    }

    public void updateConfig(Map<String, Object> newConfig) {
        config.clear();
        config.putAll(newConfig);
        saveConfig();
    }
}