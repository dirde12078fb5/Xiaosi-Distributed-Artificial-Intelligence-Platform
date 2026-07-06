package com.xiaosi.nas.repository;

import com.xiaosi.nas.entity.Share;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;

@Repository
public interface ShareRepository extends JpaRepository<Share, Long> {
    Optional<Share> findByName(String name);
    List<Share> findByOwnerId(Long ownerId);
    List<Share> findByVolumeId(Long volumeId);
    List<Share> findByIsPublicTrue();
}