import Foundation
import CommonCrypto

class UserManager {
    static let shared = UserManager()

    private var users: [User] = []
    private let dataFile: String

    private init() {
        dataFile = ConfigManager.shared.dataDir + "/users.json"
        loadUsers()
    }

    private func loadUsers() {
        if FileManager.default.fileExists(atPath: dataFile) {
            do {
                let data = try Data(contentsOf: URL(fileURLWithPath: dataFile))
                users = try JSONDecoder().decode([User].self, from: data)
            } catch {
                users = []
                saveUsers()
            }
        }
    }

    private func saveUsers() {
        do {
            let data = try JSONEncoder().encode(users)
            try data.write(to: URL(fileURLWithPath: dataFile))
        } catch {
            print("❌ 保存用户数据失败: \(error)")
        }
    }

    private func hashPassword(_ password: String) -> String {
        let data = password.data(using: .utf8)!
        var digest = [UInt8](repeating: 0, count: Int(CC_SHA256_DIGEST_LENGTH))
        _ = data.withUnsafeBytes {
            CC_SHA256($0.baseAddress, CC_LONG(data.count), &digest)
        }
        return digest.map { String(format: "%02x", $0) }.joined()
    }

    func listUsers() -> [User] {
        return users.map { user in
            var u = user
            u.password = "***"
            return u
        }
    }

    func createUser(username: String, password: String, role: String) -> User? {
        if users.contains { $0.username == username } {
            return nil
        }

        let hashedPassword = hashPassword(password)
        let user = User(
            username: username,
            password: hashedPassword,
            role: role,
            created_at: ISO8601DateFormatter().string(from: Date())
        )
        users.append(user)
        saveUsers()
        return user
    }

    func deleteUser(username: String) -> Bool {
        let index = users.firstIndex { $0.username == username }
        if let idx = index {
            users.remove(at: idx)
            saveUsers()
            return true
        }
        return false
    }
}