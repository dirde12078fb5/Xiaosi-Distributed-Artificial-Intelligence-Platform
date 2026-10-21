import Foundation

class SMBManager {
    static let shared = SMBManager()

    private var shares: [SMBShare] = []
    private let dataFile: String

    private init() {
        dataFile = ConfigManager.shared.dataDir + "/shares.json"
        loadShares()
    }

    private func loadShares() {
        if FileManager.default.fileExists(atPath: dataFile) {
            do {
                let data = try Data(contentsOf: URL(fileURLWithPath: dataFile))
                shares = try JSONDecoder().decode([SMBShare].self, from: data)
            } catch {
                shares = []
                saveShares()
            }
        }
    }

    private func saveShares() {
        do {
            let data = try JSONEncoder().encode(shares)
            try data.write(to: URL(fileURLWithPath: dataFile))
        } catch {
            print("❌ 保存共享数据失败: \(error)")
        }
    }

    func listShares() -> [SMBShare] {
        return shares
    }

    func createShare(name: String, path: String, readonly: Bool, users: [String]) -> SMBShare? {
        if shares.contains { $0.name == name } {
            return nil
        }

        do {
            if !FileManager.default.fileExists(atPath: path) {
                try FileManager.default.createDirectory(atPath: path, withIntermediateDirectories: true)
            }

            let share = SMBShare(name: name, path: path, readonly: readonly, users: users)
            shares.append(share)
            saveShares()
            return share
        } catch {
            print("❌ 创建共享失败: \(error)")
            return nil
        }
    }

    func deleteShare(name: String) -> Bool {
        let index = shares.firstIndex { $0.name == name }
        if let idx = index {
            shares.remove(at: idx)
            saveShares()
            return true
        }
        return false
    }
}