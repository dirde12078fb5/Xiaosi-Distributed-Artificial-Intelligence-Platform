package com.xiaosi.nas.controller;

import com.xiaosi.nas.service.ConfigService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/config")
@RequiredArgsConstructor
public class ConfigController {

    private final ConfigService configService;

    @GetMapping
    public ResponseEntity<Map<String, Object>> getConfig() {
        return ResponseEntity.ok(configService.getConfig());
    }

    @GetMapping("/reload")
    public ResponseEntity<Map<String, String>> reloadConfig() {
        configService.loadConfig();
        return ResponseEntity.ok(Map.of("message", "配置已重新加载"));
    }

    @PutMapping
    public ResponseEntity<Map<String, String>> updateConfig(@RequestBody Map<String, Object> config) {
        configService.updateConfig(config);
        return ResponseEntity.ok(Map.of("message", "配置已更新"));
    }

    @GetMapping("/{key}")
    public ResponseEntity<Map<String, Object>> getConfigValue(@PathVariable String key) {
        Object value = configService.get(key, null);
        if (value == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(Map.of("key", key, "value", value));
    }

    @PutMapping("/{key}")
    public ResponseEntity<Map<String, String>> setConfigValue(
        @PathVariable String key,
        @RequestBody Map<String, Object> request
    ) {
        configService.set(key, request.get("value"));
        configService.saveConfig();
        return ResponseEntity.ok(Map.of("message", "配置项已更新"));
    }
}