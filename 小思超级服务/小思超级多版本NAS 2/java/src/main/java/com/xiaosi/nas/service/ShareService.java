package com.xiaosi.nas.service;

import com.xiaosi.nas.entity.Share;
import com.xiaosi.nas.repository.ShareRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ShareService {

    private final ShareRepository shareRepository;

    public List<Share> getAllShares() {
        return shareRepository.findAll();
    }

    public List<Share> getSharesByOwner(Long ownerId) {
        return shareRepository.findByOwnerId(ownerId);
    }

    public List<Share> getPublicShares() {
        return shareRepository.findByIsPublicTrue();
    }

    public Optional<Share> getShareById(Long id) {
        return shareRepository.findById(id);
    }

    public Optional<Share> getShareByName(String name) {
        return shareRepository.findByName(name);
    }

    @Transactional
    public Share createShare(Share share) {
        if (share.getName() == null || share.getName().isEmpty()) {
            share.setName("share-" + UUID.randomUUID().toString().substring(0, 8));
        }
        
        if (shareRepository.findByName(share.getName()).isPresent()) {
            throw new IllegalArgumentException("共享名称已存在");
        }
        
        return shareRepository.save(share);
    }

    @Transactional
    public Share updateShare(Long id, Share shareDetails) {
        Share share = shareRepository.findById(id)
            .orElseThrow(() -> new IllegalArgumentException("共享不存在"));
        
        share.setPath(shareDetails.getPath());
        share.setShareType(shareDetails.getShareType());
        share.setIsPublic(shareDetails.getIsPublic());
        share.setReadOnly(shareDetails.getReadOnly());
        share.setMaxConnections(shareDetails.getMaxConnections());
        share.setAccessPassword(shareDetails.getAccessPassword());
        
        return shareRepository.save(share);
    }

    @Transactional
    public void deleteShare(Long id) {
        shareRepository.deleteById(id);
    }

    public boolean isValidShare(Long id, String password) {
        return shareRepository.findById(id)
            .map(share -> {
                if (!share.getIsPublic() && share.getAccessPassword() != null) {
                    return share.getAccessPassword().equals(password);
                }
                return share.getIsPublic() || password != null;
            })
            .orElse(false);
    }

    public boolean isShareValid(Long id) {
        return shareRepository.findById(id)
            .map(share -> {
                LocalDateTime now = LocalDateTime.now();
                boolean validFrom = share.getValidFrom() == null || now.isAfter(share.getValidFrom());
                boolean validUntil = share.getValidUntil() == null || now.isBefore(share.getValidUntil());
                return validFrom && validUntil;
            })
            .orElse(false);
    }

    public List<Share> getSharesByVolume(Long volumeId) {
        return shareRepository.findByVolumeId(volumeId);
    }
}