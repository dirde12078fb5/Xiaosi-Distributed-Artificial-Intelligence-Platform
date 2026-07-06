package com.xiaosi.nas.entity;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "files")
public class FileInfo {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Column(nullable = false)
    private String path;

    @Column(nullable = false)
    private String type;

    private Long size;

    @Column(name = "volume_id")
    private Long volumeId;

    @Column(name = "owner_id")
    private Long ownerId;

    @Column(name = "is_directory")
    private Boolean isDirectory = false;

    @Column(name = "mime_type")
    private String mimeType;

    @Column(name = "file_hash")
    private String fileHash;

    @Column(name = "version_count")
    private Integer versionCount = 0;

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