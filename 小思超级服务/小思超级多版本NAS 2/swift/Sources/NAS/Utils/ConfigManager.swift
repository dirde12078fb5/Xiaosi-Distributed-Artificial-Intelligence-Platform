import Foundation

class ConfigManager {
    static let shared = ConfigManager()

    var config: Config
    private let configFile: String

    private init() {
        let fileManager = FileManager.default
        let currentPath = fileManager.currentDirectoryPath
        configFile = URL(fileURLWithPath: currentPath)
            .deletingLastPathComponent()
            .appendingPathComponent("config")
            .appendingPathComponent("config.json")
            .path

        config = Config()

        if !fileManager.fileExists(atPath: configFile) {
            saveConfig()
        } else {
            loadConfig()
        }

        createDataDirectories()
    }

    private func loadConfig() {
        do {
            let data = try Data(contentsOf: URL(fileURLWithPath: configFile))
            config = try JSONDecoder().decode(Config.self, from: data)
            print("✅ 配置文件加载成功: \(configFile)")
        } catch {
            print("⚠️ 配置文件加载失败，使用默认配置: \(error)")
            saveConfig()
        }
    }

    func saveConfig() {
        do {
            let data = try JSONEncoder().encode(config)
            let json = try JSONSerialization.jsonObject(with: data)
            let prettyData = try JSONSerialization.data(withJSONObject: json, options: .prettyPrinted)
            try prettyData.write(to: URL(fileURLWithPath: configFile))
            print("✅ 配置文件已保存")
        } catch {
            print("❌ 保存配置失败: \(error)")
        }
    }

    private func createDataDirectories() {
        let fileManager = FileManager.default
        let dirs = [dataDir, receiveDir]

        for dir in dirs {
            if !fileManager.fileExists(atPath: dir) {
                try? fileManager.createDirectory(atPath: dir, withIntermediateDirectories: true)
                print("📁 创建目录: \(dir)")
            }
        }
    }

    var dataDir: String {
        return config.data_dir
    }

    var receiveDir: String {
        return config.receive_dir
    }
}