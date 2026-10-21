package com.xiaosi.nas.entity;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "shares")
public class Share {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true, nullable = false)
    private String name;

    @Column(nullable = false)
    private String path;

    @Column(name = "volume_id")
    private Long volumeId;

    @Column(name = "owner_id")
    private Long ownerId;

    @Column(name = "share_type")
    private String shareType;

    @Column(name = "is_public")
    private Boolean isPublic = false;

    @Column(name = "read_only")
    private Boolean readOnly = false;

    @Column(name = "max_connections")
    private Integer maxConnections = 10;

    @Column(name = "valid_from")
    private LocalDateTime validFrom;

    @Column(name = "valid_until")
    private LocalDateTime validUntil;

    @Column(name = "access_password")
    private String accessPassword;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}