package com.xiaosi.nas.repository;

import com.xiaosi.nas.entity.PushNotification;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface PushNotificationRepository extends JpaRepository<PushNotification, Long> {
    List<PushNotification> findByUserIdOrderByCreatedAtDesc(Long userId);
    List<PushNotification> findByUserIdAndIsReadFalse(Long userId);
    Long countByUserIdAndIsReadFalse(Long userId);
}