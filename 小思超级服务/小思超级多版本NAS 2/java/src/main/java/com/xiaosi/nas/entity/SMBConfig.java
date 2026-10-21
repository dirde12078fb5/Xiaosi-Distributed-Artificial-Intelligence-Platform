package com.xiaosi.nas.entity;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "smb_configs")
public class SMBConfig {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true, nullable = false)
    private String name;

    @Column(nullable = false)
    private String workgroup;

    @Column(name = "server_string")
    private String serverString;

    @Column(name = "bind_interface")
    private String bindInterface;

    @Column(name = "max_protocol")
    private String maxProtocol;

    @Column(name = "min_protocol")
    private String minProtocol;

    @Column(name = "log_level")
    private Integer logLevel = 1;

    @Column(name = "is_active")
    private Boolean isActive = true;

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