package com.xiaosi.nas.service;

import com.xiaosi.nas.entity.PushNotification;
import com.xiaosi.nas.repository.PushNotificationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class PushService {

    private final PushNotificationRepository notificationRepository;
    private final SimpMessagingTemplate messagingTemplate;

    public List<PushNotification> getUserNotifications(Long userId) {
        return notificationRepository.findByUserIdOrderByCreatedAtDesc(userId);
    }

    public List<PushNotification> getUnreadNotifications(Long userId) {
        return notificationRepository.findByUserIdAndIsReadFalse(userId);
    }

    public Long getUnreadCount(Long userId) {
        return notificationRepository.countByUserIdAndIsReadFalse(userId);
    }

    public Optional<PushNotification> getNotificationById(Long id) {
        return notificationRepository.findById(id);
    }

    @Transactional
    public PushNotification createNotification(Long userId, String title, String message, String type) {
        PushNotification notification = new PushNotification();
        notification.setUserId(userId);
        notification.setTitle(title);
        notification.setMessage(message);
        notification.setType(type);
        
        PushNotification saved = notificationRepository.save(notification);
        
        // 通过WebSocket推送
        messagingTemplate.convertAndSendToUser(
            userId.toString(),
            "/queue/notifications",
            saved
        );
        
        return saved;
    }

    @Transactional
    public void markAsRead(Long id) {
        notificationRepository.findById(id).ifPresent(notification -> {
            notification.setIsRead(true);
            notification.setReadAt(LocalDateTime.now());
            notificationRepository.save(notification);
        });
    }

    @Transactional
    public void markAllAsRead(Long userId) {
        notificationRepository.findByUserIdAndIsReadFalse(userId).forEach(notification -> {
            notification.setIsRead(true);
            notification.setReadAt(LocalDateTime.now());
            notificationRepository.save(notification);
        });
    }

    @Transactional
    public void deleteNotification(Long id) {
        notificationRepository.deleteById(id);
    }

    @Transactional
    public void clearUserNotifications(Long userId) {
        List<PushNotification> notifications = notificationRepository.findByUserIdOrderByCreatedAtDesc(userId);
        notificationRepository.deleteAll(notifications);
    }

    // 批量推送
    public void broadcastNotification(String title, String message, String type) {
        messagingTemplate.convertAndSend("/topic/notifications", 
            new NotificationBroadcast(title, message, type));
    }

    public record NotificationBroadcast(String title, String message, String type) {}
}