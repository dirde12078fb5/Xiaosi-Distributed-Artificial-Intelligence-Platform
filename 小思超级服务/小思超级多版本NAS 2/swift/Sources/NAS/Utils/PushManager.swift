import Foundation
import NIO
import NIOHTTP1

class PushManager {
    static let shared = PushManager()

    private var pushHistory: [PushStatus] = []
    private let historyFile: String

    private init() {
        historyFile = ConfigManager.shared.dataDir + "/push_history.json"
        loadHistory()
    }

    private func loadHistory() {
        if FileManager.default.fileExists(atPath: historyFile) {
            do {
                let data = try Data(contentsOf: URL(fileURLWithPath: historyFile))
                pushHistory = try JSONDecoder().decode([PushStatus].self, from: data)
            } catch {
                pushHistory = []
                saveHistory()
            }
        }
    }

    private func saveHistory() {
        do {
            let data = try JSONEncoder().encode(pushHistory)
            try data.write(to: URL(fileURLWithPath: historyFile))
        } catch {
            print("❌ 保存推送历史失败: \(error)")
        }
    }

    func getTargets() -> [PushTarget] {
        return ConfigManager.shared.config.push.targets
    }

    func addTarget(name: String, ip: String, port: Int) -> PushTarget {
        let target = PushTarget(name: name, ip: ip, port: port)
        ConfigManager.shared.config.push.targets.append(target)
        ConfigManager.shared.saveConfig()
        return target
    }

    func getPushHistory() -> [PushStatus] {
        return pushHistory
    }

    func receiveFile(folder: String, filepath: String, fileData: Data) -> Bool {
        let receiveDir = ConfigManager.shared.receiveDir
        let fullPath = receiveDir + "/" + folder + "/" + filepath

        do {
            let directoryPath = URL(fileURLWithPath: fullPath).deletingLastPathComponent().path
            if !FileManager.default.fileExists(atPath: directoryPath) {
                try FileManager.default.createDirectory(atPath: directoryPath, withIntermediateDirectories: true)
            }
            try fileData.write(to: URL(fileURLWithPath: fullPath))
            print("✅ 接收文件成功: \(fullPath)")
            return true
        } catch {
            print("❌ 接收文件失败: \(error)")
            return false
        }
    }
}