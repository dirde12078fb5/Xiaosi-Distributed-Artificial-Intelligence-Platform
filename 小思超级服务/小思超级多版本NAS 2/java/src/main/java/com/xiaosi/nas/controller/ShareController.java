package com.xiaosi.nas.controller;

import com.xiaosi.nas.entity.Share;
import com.xiaosi.nas.service.ShareService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/shares")
@RequiredArgsConstructor
public class ShareController {

    private final ShareService shareService;

    @GetMapping
    public ResponseEntity<List<Share>> getAllShares() {
        return ResponseEntity.ok(shareService.getAllShares());
    }

    @GetMapping("/public")
    public ResponseEntity<List<Share>> getPublicShares() {
        return ResponseEntity.ok(shareService.getPublicShares());
    }

    @GetMapping("/{id}")
    public ResponseEntity<Share> getShare(@PathVariable Long id) {
        return shareService.getShareById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/owner/{ownerId}")
    public ResponseEntity<List<Share>> getSharesByOwner(@PathVariable Long ownerId) {
        return ResponseEntity.ok(shareService.getSharesByOwner(ownerId));
    }

    @GetMapping("/volume/{volumeId}")
    public ResponseEntity<List<Share>> getSharesByVolume(@PathVariable Long volumeId) {
        return ResponseEntity.ok(shareService.getSharesByVolume(volumeId));
    }

    @PostMapping
    public ResponseEntity<?> createShare(@RequestBody Share share) {
        try {
            Share created = shareService.createShare(share);
            return ResponseEntity.ok(created);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    @PutMapping("/{id}")
    public ResponseEntity<?> updateShare(@PathVariable Long id, @RequestBody Share share) {
        try {
            Share updated = shareService.updateShare(id, share);
            return ResponseEntity.ok(updated);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteShare(@PathVariable Long id) {
        shareService.deleteShare(id);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/{id}/validate")
    public ResponseEntity<Map<String, Object>> validateShare(
        @PathVariable Long id,
        @RequestBody(required = false) Map<String, String> request
    ) {
        String password = request != null ? request.get("password") : null;
        boolean isValid = shareService.isValidShare(id, password);
        boolean isTimeValid = shareService.isShareValid(id);
        
        return ResponseEntity.ok(Map.of(
            "valid", isValid && isTimeValid,
            "passwordValid", isValid,
            "timeValid", isTimeValid
        ));
    }
}