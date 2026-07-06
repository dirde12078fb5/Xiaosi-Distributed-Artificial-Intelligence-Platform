import Foundation

class StorageManager {
    static let shared = StorageManager()

    private var volumes: [StorageVolume] = []
    private let dataFile: String

    private init() {
        dataFile = ConfigManager.shared.dataDir + "/volumes.json"
        loadVolumes()
    }

    private func loadVolumes() {
        do {
            if FileManager.default.fileExists(atPath: dataFile) {
                let data = try Data(contentsOf: URL(fileURLWithPath: dataFile))
                volumes = try JSONDecoder().decode([StorageVolume].self, from: data)
            } else {
                volumes = ConfigManager.shared.config.storage.volumes
                saveVolumes()
            }
        } catch {
            volumes = ConfigManager.shared.config.storage.volumes
            saveVolumes()
        }
    }

    private func saveVolumes() {
        do {
            let data = try JSONEncoder().encode(volumes)
            try data.write(to: URL(fileURLWithPath: dataFile))
        } catch {
            print("❌ 保存存储卷数据失败: \(error)")
        }
    }

    func listVolumes() -> [StorageVolume] {
        for var volume in volumes {
            let attrs = try? FileManager.default.attributesOfFileSystem(forPath: volume.path)
            volume.used_gb = (attrs?[.systemSize] as? UInt64 ?? 0) / 1024 / 1024 / 1024
            volume.available_gb = (attrs?[.systemFreeSize] as? UInt64 ?? 0) / 1024 / 1024 / 1024
        }
        return volumes
    }

    func createVolume(name: String, path: String, quota_gb: Int?) -> StorageVolume? {
        do {
            if !FileManager.default.fileExists(atPath: path) {
                try FileManager.default.createDirectory(atPath: path, withIntermediateDirectories: true)
            }

            let volume = StorageVolume(name: name, path: path, quota_gb: quota_gb)
            volumes.append(volume)
            saveVolumes()
            return volume
        } catch {
            print("❌ 创建存储卷失败: \(error)")
            return nil
        }
    }

    func deleteVolume(name: String) -> Bool {
        let index = volumes.firstIndex { $0.name == name }
        if let idx = index {
            volumes.remove(at: idx)
            saveVolumes()
            return true
        }
        return false
    }
}