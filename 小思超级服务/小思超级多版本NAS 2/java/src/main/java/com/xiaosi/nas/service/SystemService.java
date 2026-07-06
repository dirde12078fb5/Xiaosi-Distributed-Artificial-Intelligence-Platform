package com.xiaosi.nas.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import oshi.SystemInfo;
import oshi.hardware.CentralProcessor;
import oshi.hardware.GlobalMemory;
import oshi.software.os.FileSystem;
import oshi.software.os.OSFileStore;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class SystemService {

    private final SystemInfo systemInfo = new SystemInfo();

    public Map<String, Object> getSystemInfo() {
        Map<String, Object> info = new HashMap<>();
        
        info.put("os", systemInfo.getOperatingSystem().toString());
        info.put("cpu", getCpuInfo());
        info.put("memory", getMemoryInfo());
        info.put("disks", getDiskInfo());
        
        return info;
    }

    public Map<String, Object> getCpuInfo() {
        Map<String, Object> cpuInfo = new HashMap<>();
        
        CentralProcessor processor = systemInfo.getHardware().getProcessor();
        cpuInfo.put("processorName", processor.getProcessorIdentifier().getName());
        cpuInfo.put("logicalCores", processor.getLogicalProcessorCount());
        cpuInfo.put("physicalCores", processor.getPhysicalProcessorCount());
        
        double cpuLoad = processor.getSystemLoadAverage(1)[0];
        cpuInfo.put("systemLoad", cpuLoad >= 0 ? cpuLoad : 0);
        
        return cpuInfo;
    }

    public Map<String, Object> getMemoryInfo() {
        Map<String, Object> memoryInfo = new HashMap<>();
        
        GlobalMemory memory = systemInfo.getHardware().getMemory();
        long total = memory.getTotal();
        long available = memory.getAvailable();
        long used = total - available;
        
        memoryInfo.put("total", total);
        memoryInfo.put("used", used);
        memoryInfo.put("available", available);
        memoryInfo.put("usagePercent", (double) used / total * 100);
        
        return memoryInfo;
    }

    public List<Map<String, Object>> getDiskInfo() {
        FileSystem fileSystem = systemInfo.getOperatingSystem().getFileSystem();
        
        return fileSystem.getFileStores().stream()
            .map(store -> {
                Map<String, Object> disk = new HashMap<>();
                disk.put("name", store.getName());
                disk.put("mount", store.getMount());
                disk.put("total", store.getTotalSpace());
                disk.put("free", store.getFreeSpace());
                disk.put("used", store.getTotalSpace() - store.getFreeSpace());
                disk.put("usable", store.getUsableSpace());
                disk.put("type", store.getType());
                return disk;
            })
            .toList();
    }

    public Map<String, Object> getNetworkInfo() {
        Map<String, Object> networkInfo = new HashMap<>();
        
        systemInfo.getHardware().getNetworkIFs().forEach(nic -> {
            Map<String, Object> iface = new HashMap<>();
            iface.put("name", nic.getName());
            iface.put("displayName", nic.getDisplayName());
            iface.put("ipv4", nic.getIPv4addr());
            iface.put("ipv6", nic.getIPv6addr());
            iface.put("mac", nic.getMacaddr());
            iface.put("bytesSent", nic.getBytesSent());
            iface.put("bytesRecv", nic.getBytesRecv());
            networkInfo.put(nic.getName(), iface);
        });
        
        return networkInfo;
    }

    public double getCpuUsage() {
        CentralProcessor processor = systemInfo.getHardware().getProcessor();
        double load = processor.getSystemLoadAverage(1)[0];
        return load >= 0 ? load / processor.getLogicalProcessorCount() * 100 : 0;
    }

    public double getMemoryUsage() {
        GlobalMemory memory = systemInfo.getHardware().getMemory();
        return (double) (memory.getTotal() - memory.getAvailable()) / memory.getTotal() * 100;
    }
}