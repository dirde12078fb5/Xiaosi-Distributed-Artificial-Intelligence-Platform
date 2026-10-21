package com.xiaosi.nas.repository;

import com.xiaosi.nas.entity.FileInfo;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;

@Repository
public interface FileInfoRepository extends JpaRepository<FileInfo, Long> {
    Optional<FileInfo> findByPath(String path);
    List<FileInfo> findByOwnerId(Long ownerId);
    List<FileInfo> findByVolumeId(Long volumeId);
    List<FileInfo> findByIsDirectoryTrue();
}