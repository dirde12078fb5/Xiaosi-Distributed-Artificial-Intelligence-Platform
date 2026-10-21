package com.xiaosi.nas.entity;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "volumes")
public class Volume {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true, nullable = false)
    private String name;

    @Column(nullable = false)
    private String path;

    @Column(name = "total_size")
    private Long totalSize;

    @Column(name = "used_size")
    private Long usedSize = 0L;

    @Column(name = "available_size")
    private Long availableSize;

    @Column(nullable = false)
    private String filesystem;

    @Column(name = "mount_point")
    private String mountPoint;

    @Column(name = "is_encrypted")
    private Boolean isEncrypted = false;

    @Column(name = "is_compressed")
    private Boolean isCompressed = false;

    @Column(name = "raid_level")
    private String raidLevel;

    @Column(name = "health_status")
    private String healthStatus = "healthy";

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