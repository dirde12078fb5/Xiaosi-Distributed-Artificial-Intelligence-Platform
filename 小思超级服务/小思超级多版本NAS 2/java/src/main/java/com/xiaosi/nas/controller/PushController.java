package com.xiaosi.nas.controller;

import com.xiaosi.nas.entity.PushNotification;
import com.xiaosi.nas.service.PushService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/notifications")
@RequiredArgsConstructor
public class PushController {

    private final PushService pushService;

    @GetMapping("/user/{userId}")
    public ResponseEntity<List<PushNotification>> getUserNotifications(@PathVariable Long userId) {
        return ResponseEntity.ok(pushService.getUserNotifications(userId));
    }

    @GetMapping("/user/{userId}/unread")
    public ResponseEntity<List<PushNotification>> getUnreadNotifications(@PathVariable Long userId) {
        return ResponseEntity.ok(pushService.getUnreadNotifications(userId));
    }

    @GetMapping("/user/{userId}/count")
    public ResponseEntity<Map<String, Long>> getUnreadCount(@PathVariable Long userId) {
        return ResponseEntity.ok(Map.of("count", pushService.getUnreadCount(userId)));
    }

    @PostMapping
    public ResponseEntity<PushNotification> createNotification(@RequestBody Map<String, Object> request) {
        Long userId = Long.parseLong(request.get("userId").toString());
        String title = request.get("title").toString();
        String message = request.get("message").toString();
        String type = request.getOrDefault("type", "info").toString();
        
        PushNotification notification = pushService.createNotification(userId, title, message, type);
        return ResponseEntity.ok(notification);
    }

    @PutMapping("/{id}/read")
    public ResponseEntity<Void> markAsRead(@PathVariable Long id) {
        pushService.markAsRead(id);
        return ResponseEntity.ok().build();
    }

    @PutMapping("/user/{userId}/read-all")
    public ResponseEntity<Void> markAllAsRead(@PathVariable Long userId) {
        pushService.markAllAsRead(userId);
        return ResponseEntity.ok().build();
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteNotification(@PathVariable Long id) {
        pushService.deleteNotification(id);
        return ResponseEntity.ok().build();
    }

    @DeleteMapping("/user/{userId}/clear")
    public ResponseEntity<Void> clearUserNotifications(@PathVariable Long userId) {
        pushService.clearUserNotifications(userId);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/broadcast")
    public ResponseEntity<Void> broadcastNotification(@RequestBody Map<String, String> request) {
        pushService.broadcastNotification(
            request.get("title"),
            request.get("message"),
            request.getOrDefault("type", "info")
        );
        return ResponseEntity.ok().build();
    }
}