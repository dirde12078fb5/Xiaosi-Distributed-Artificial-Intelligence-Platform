package com.xiaosi.nas.service;

import com.xiaosi.nas.entity.SMBConfig;
import com.xiaosi.nas.repository.SMBConfigRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;
import java.util.Optional;

@Slf4j
@Service
@RequiredArgsConstructor
public class SMBService {

    private final SMBConfigRepository smbConfigRepository;

    public List<SMBConfig> getAllConfigs() {
        return smbConfigRepository.findAll();
    }

    public Optional<SMBConfig> getActiveConfig() {
        return smbConfigRepository.findByIsActiveTrue();
    }

    public Optional<SMBConfig> getConfigById(Long id) {
        return smbConfigRepository.findById(id);
    }

    @Transactional
    public SMBConfig createConfig(SMBConfig config) {
        if (smbConfigRepository.findByName(config.getName()).isPresent()) {
            throw new IllegalArgumentException("SMB配置名称已存在");
        }
        return smbConfigRepository.save(config);
    }

    @Transactional
    public SMBConfig updateConfig(Long id, SMBConfig configDetails) {
        SMBConfig config = smbConfigRepository.findById(id)
            .orElseThrow(() -> new IllegalArgumentException("SMB配置不存在"));
        
        config.setWorkgroup(configDetails.getWorkgroup());
        config.setServerString(configDetails.getServerString());
        config.setBindInterface(configDetails.getBindInterface());
        config.setMaxProtocol(configDetails.getMaxProtocol());
        config.setMinProtocol(configDetails.getMinProtocol());
        config.setLogLevel(configDetails.getLogLevel());
        
        return smbConfigRepository.save(config);
    }

    @Transactional
    public void setActiveConfig(Long id) {
        smbConfigRepository.findAll().forEach(config -> {
            config.setIsActive(false);
            smbConfigRepository.save(config);
        });
        
        smbConfigRepository.findById(id).ifPresent(config -> {
            config.setIsActive(true);
            smbConfigRepository.save(config);
        });
    }

    @Transactional
    public void deleteConfig(Long id) {
        smbConfigRepository.deleteById(id);
    }

    public String generateSmbConf(SMBConfig config) {
        StringBuilder sb = new StringBuilder();
        sb.append("[global]\n");
        sb.append("   workgroup = ").append(config.getWorkgroup()).append("\n");
        sb.append("   server string = ").append(config.getServerString()).append("\n");
        
        if (config.getBindInterface() != null) {
            sb.append("   bind interfaces only = yes\n");
            sb.append("   interfaces = ").append(config.getBindInterface()).append("\n");
        }
        
        sb.append("   max protocol = ").append(config.getMaxProtocol() != null ? config.getMaxProtocol() : "SMB3").append("\n");
        sb.append("   min protocol = ").append(config.getMinProtocol() != null ? config.getMinProtocol() : "SMB2").append("\n");
        sb.append("   log level = ").append(config.getLogLevel()).append("\n");
        sb.append("   security = user\n");
        
        return sb.toString();
    }
}