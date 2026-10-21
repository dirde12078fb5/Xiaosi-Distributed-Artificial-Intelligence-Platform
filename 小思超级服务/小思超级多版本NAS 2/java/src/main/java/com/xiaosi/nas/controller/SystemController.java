package com.xiaosi.nas.controller;

import com.xiaosi.nas.service.SystemService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/system")
@RequiredArgsConstructor
public class SystemController {

    private final SystemService systemService;

    @GetMapping("/info")
    public ResponseEntity<Map<String, Object>> getSystemInfo() {
        return ResponseEntity.ok(systemService.getSystemInfo());
    }

    @GetMapping("/cpu")
    public ResponseEntity<Map<String, Object>> getCpuInfo() {
        return ResponseEntity.ok(systemService.getCpuInfo());
    }

    @GetMapping("/memory")
    public ResponseEntity<Map<String, Object>> getMemoryInfo() {
        return ResponseEntity.ok(systemService.getMemoryInfo());
    }

    @GetMapping("/disks")
    public ResponseEntity<List<Map<String, Object>>> getDiskInfo() {
        return ResponseEntity.ok(systemService.getDiskInfo());
    }

    @GetMapping("/network")
    public ResponseEntity<Map<String, Object>> getNetworkInfo() {
        return ResponseEntity.ok(systemService.getNetworkInfo());
    }

    @GetMapping("/metrics")
    public ResponseEntity<Map<String, Object>> getMetrics() {
        return ResponseEntity.ok(Map.of(
            "cpuUsage", systemService.getCpuUsage(),
            "memoryUsage", systemService.getMemoryUsage()
        ));
    }
}