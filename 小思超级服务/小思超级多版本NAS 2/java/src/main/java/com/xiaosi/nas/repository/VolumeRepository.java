package com.xiaosi.nas.repository;

import com.xiaosi.nas.entity.Volume;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;

@Repository
public interface VolumeRepository extends JpaRepository<Volume, Long> {
    Optional<Volume> findByName(String name);
    List<Volume> findByHealthStatus(String healthStatus);
}