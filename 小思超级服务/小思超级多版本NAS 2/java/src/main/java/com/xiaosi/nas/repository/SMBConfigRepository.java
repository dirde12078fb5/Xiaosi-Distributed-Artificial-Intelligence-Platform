package com.xiaosi.nas.repository;

import com.xiaosi.nas.entity.SMBConfig;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;

@Repository
public interface SMBConfigRepository extends JpaRepository<SMBConfig, Long> {
    Optional<SMBConfig> findByName(String name);
    Optional<SMBConfig> findByIsActiveTrue();
    List<SMBConfig> findByIsActiveTrueOrderByCreatedAtDesc();
}