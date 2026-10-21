package com.xiaosi.nas.controller;

import com.xiaosi.nas.entity.FileInfo;
import com.xiaosi.nas.entity.Volume;
import com.xiaosi.nas.service.StorageService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/storage")
@RequiredArgsConstructor
public class StorageController {

    private final StorageService storageService;

    @GetMapping("/volumes")
    public ResponseEntity<List<Volume>> getAllVolumes() {
        return ResponseEntity.ok(storageService.getAllVolumes());
    }

    @GetMapping("/volumes/{id}")
    public ResponseEntity<Volume> getVolume(@PathVariable Long id) {
        return storageService.getVolumeById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping("/volumes")
    public ResponseEntity<?> createVolume(@RequestBody Volume volume) {
        try {
            Volume created = storageService.createVolume(volume);
            return ResponseEntity.ok(created);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    @PutMapping("/volumes/{id}")
    public ResponseEntity<?> updateVolume(@PathVariable Long id, @RequestBody Volume volume) {
        try {
            Volume updated = storageService.updateVolume(id, volume);
            return ResponseEntity.ok(updated);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    @DeleteMapping("/volumes/{id}")
    public ResponseEntity<Void> deleteVolume(@PathVariable Long id) {
        storageService.deleteVolume(id);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/volumes/{id}/files")
    public ResponseEntity<List<FileInfo>> listFiles(
        @PathVariable Long id,
        @RequestParam(required = false, defaultValue = "") String path
    ) {
        try {
            return ResponseEntity.ok(storageService.listFiles(id, path));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().build();
        }
    }

    @PostMapping("/volumes/{id}/directories")
    public ResponseEntity<?> createDirectory(
        @PathVariable Long id,
        @RequestBody Map<String, String> request
    ) {
        try {
            FileInfo dir = storageService.createDirectory(id, request.get("path"));
            return ResponseEntity.ok(dir);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    @DeleteMapping("/volumes/{volumeId}/files")
    public ResponseEntity<?> deleteFile(
        @PathVariable Long volumeId,
        @RequestParam String path
    ) {
        try {
            storageService.deleteFile(volumeId, path);
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    @GetMapping("/volumes/{id}/usage")
    public ResponseEntity<Map<String, Object>> getVolumeUsage(@PathVariable Long id) {
        return storageService.getVolumeById(id)
            .map(volume -> ResponseEntity.ok(Map.of(
                "total", volume.getTotalSize(),
                "used", volume.getUsedSize(),
                "available", volume.getAvailableSize(),
                "usagePercent", volume.getTotalSize() > 0 
                    ? (double) volume.getUsedSize() / volume.getTotalSize() * 100 
                    : 0
            )))
            .orElse(ResponseEntity.notFound().build());
    }
}