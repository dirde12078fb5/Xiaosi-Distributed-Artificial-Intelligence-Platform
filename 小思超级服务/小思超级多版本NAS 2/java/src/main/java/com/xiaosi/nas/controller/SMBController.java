package com.xiaosi.nas.controller;

import com.xiaosi.nas.entity.SMBConfig;
import com.xiaosi.nas.service.SMBService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/smb")
@RequiredArgsConstructor
public class SMBController {

    private final SMBService smbService;

    @GetMapping("/configs")
    public ResponseEntity<List<SMBConfig>> getAllConfigs() {
        return ResponseEntity.ok(smbService.getAllConfigs());
    }

    @GetMapping("/configs/active")
    public ResponseEntity<SMBConfig> getActiveConfig() {
        return smbService.getActiveConfig()
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/configs/{id}")
    public ResponseEntity<SMBConfig> getConfig(@PathVariable Long id) {
        return smbService.getConfigById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping("/configs")
    public ResponseEntity<?> createConfig(@RequestBody SMBConfig config) {
        try {
            SMBConfig created = smbService.createConfig(config);
            return ResponseEntity.ok(created);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    @PutMapping("/configs/{id}")
    public ResponseEntity<?> updateConfig(@PathVariable Long id, @RequestBody SMBConfig config) {
        try {
            SMBConfig updated = smbService.updateConfig(id, config);
            return ResponseEntity.ok(updated);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    @PutMapping("/configs/{id}/activate")
    public ResponseEntity<Void> activateConfig(@PathVariable Long id) {
        smbService.setActiveConfig(id);
        return ResponseEntity.ok().build();
    }

    @DeleteMapping("/configs/{id}")
    public ResponseEntity<Void> deleteConfig(@PathVariable Long id) {
        smbService.deleteConfig(id);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/configs/{id}/smb.conf")
    public ResponseEntity<Map<String, String>> generateSmbConf(@PathVariable Long id) {
        return smbService.getConfigById(id)
            .map(config -> ResponseEntity.ok(Map.of("content", smbService.generateSmbConf(config))))
            .orElse(ResponseEntity.notFound().build());
    }
}