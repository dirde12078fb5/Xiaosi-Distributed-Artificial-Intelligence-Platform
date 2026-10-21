package com.xiaosi.nas.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/public")
@RequiredArgsConstructor
public class PublicController {

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        return ResponseEntity.ok(Map.of(
            "status", "healthy",
            "service", "xiaosi-nas",
            "version", "1.0.0",
            "timestamp", System.currentTimeMillis()
        ));
    }

    @GetMapping("/info")
    public ResponseEntity<Map<String, Object>> info() {
        return ResponseEntity.ok(Map.of(
            "name", "Xiaosi NAS Service",
            "description", "分布式NAS服务平台",
            "version", "1.0.0",
            "features", Map.of(
                "storage", true,
                "users", true,
                "shares", true,
                "smb", true,
                "push", true,
                "monitoring", true
            )
        ));
    }
}