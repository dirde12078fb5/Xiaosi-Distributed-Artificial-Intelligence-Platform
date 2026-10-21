package com.xiaosi.nas.service;

import com.xiaosi.nas.entity.FileInfo;
import com.xiaosi.nas.entity.Volume;
import com.xiaosi.nas.repository.FileInfoRepository;
import com.xiaosi.nas.repository.VolumeRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.io.IOException;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.stream.Stream;

@Service
@RequiredArgsConstructor
public class StorageService {

    private final VolumeRepository volumeRepository;
    private final FileInfoRepository fileInfoRepository;

    @Value("${nas.storage-root:./storage}")
    private String storageRoot;

    public List<Volume> getAllVolumes() {
        return volumeRepository.findAll();
    }

    public Optional<Volume> getVolumeById(Long id) {
        return volumeRepository.findById(id);
    }

    public Optional<Volume> getVolumeByName(String name) {
        return volumeRepository.findByName(name);
    }

    @Transactional
    public Volume createVolume(Volume volume) {
        if (volumeRepository.findByName(volume.getName()).isPresent()) {
            throw new IllegalArgumentException("存储卷名称已存在");
        }
        
        Path volumePath = Paths.get(storageRoot, volume.getName());
        try {
            Files.createDirectories(volumePath);
            volume.setPath(volumePath.toString());
            volume.setAvailableSize(volume.getTotalSize());
        } catch (IOException e) {
            throw new RuntimeException("无法创建存储卷目录: " + e.getMessage());
        }
        
        return volumeRepository.save(volume);
    }

    @Transactional
    public Volume updateVolume(Long id, Volume volumeDetails) {
        Volume volume = volumeRepository.findById(id)
            .orElseThrow(() -> new IllegalArgumentException("存储卷不存在"));
        
        volume.setRaidLevel(volumeDetails.getRaidLevel());
        volume.setIsEncrypted(volumeDetails.getIsEncrypted());
        volume.setIsCompressed(volumeDetails.getIsCompressed());
        volume.setHealthStatus(volumeDetails.getHealthStatus());
        
        return volumeRepository.save(volume);
    }

    @Transactional
    public void deleteVolume(Long id) {
        Volume volume = volumeRepository.findById(id)
            .orElseThrow(() -> new IllegalArgumentException("存储卷不存在"));
        
        try {
            Path volumePath = Paths.get(volume.getPath());
            Files.walkFileTree(volumePath, new SimpleFileVisitor<>() {
                @Override
                public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                    Files.delete(file);
                    return FileVisitResult.CONTINUE;
                }
                
                @Override
                public FileVisitResult postVisitDirectory(Path dir, IOException exc) throws IOException {
                    Files.delete(dir);
                    return FileVisitResult.CONTINUE;
                }
            });
        } catch (IOException e) {
            // 忽略删除错误
        }
        
        volumeRepository.deleteById(id);
    }

    public List<FileInfo> listFiles(Long volumeId, String dirPath) {
        Volume volume = volumeRepository.findById(volumeId)
            .orElseThrow(() -> new IllegalArgumentException("存储卷不存在"));
        
        Path fullPath = Paths.get(volume.getPath(), dirPath);
        if (!Files.exists(fullPath)) {
            throw new IllegalArgumentException("目录不存在");
        }
        
        try (Stream<Path> paths = Files.list(fullPath)) {
            return paths.map(path -> {
                FileInfo info = new FileInfo();
                info.setName(path.getFileName().toString());
                info.setPath(path.toString());
                info.setIsDirectory(Files.isDirectory(path));
                try {
                    info.setSize(Files.size(path));
                    info.setMimeType(Files.probeContentType(path));
                } catch (IOException e) {
                    // 忽略
                }
                info.setVolumeId(volumeId);
                return info;
            }).toList();
        } catch (IOException e) {
            throw new RuntimeException("无法读取目录: " + e.getMessage());
        }
    }

    @Transactional
    public FileInfo createDirectory(Long volumeId, String path) {
        Volume volume = volumeRepository.findById(volumeId)
            .orElseThrow(() -> new IllegalArgumentException("存储卷不存在"));
        
        Path fullPath = Paths.get(volume.getPath(), path);
        try {
            Files.createDirectories(fullPath);
            
            FileInfo dir = new FileInfo();
            dir.setName(fullPath.getFileName().toString());
            dir.setPath(path);
            dir.setIsDirectory(true);
            dir.setVolumeId(volumeId);
            dir.setType("directory");
            
            return fileInfoRepository.save(dir);
        } catch (IOException e) {
            throw new RuntimeException("无法创建目录: " + e.getMessage());
        }
    }

    @Transactional
    public void deleteFile(Long volumeId, String path) {
        Volume volume = volumeRepository.findById(volumeId)
            .orElseThrow(() -> new IllegalArgumentException("存储卷不存在"));
        
        Path fullPath = Paths.get(volume.getPath(), path);
        try {
            Files.deleteIfExists(fullPath);
            fileInfoRepository.findByPath(path).ifPresent(fileInfoRepository::delete);
        } catch (IOException e) {
            throw new RuntimeException("无法删除文件: " + e.getMessage());
        }
    }

    public Optional<FileInfo> getFileInfo(Long id) {
        return fileInfoRepository.findById(id);
    }

    public long getVolumeUsage(Long volumeId) {
        return fileInfoRepository.findByVolumeId(volumeId).stream()
            .mapToLong(f -> f.getSize() != null ? f.getSize() : 0)
            .sum();
    }

    public void updateVolumeSize(Long volumeId) {
        volumeRepository.findById(volumeId).ifPresent(volume -> {
            long usedSize = getVolumeUsage(volumeId);
            volume.setUsedSize(usedSize);
            volume.setAvailableSize(volume.getTotalSize() - usedSize);
            volumeRepository.save(volume);
        });
    }
}