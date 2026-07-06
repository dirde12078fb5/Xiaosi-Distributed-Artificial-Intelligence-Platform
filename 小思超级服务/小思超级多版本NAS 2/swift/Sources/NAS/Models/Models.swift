import Foundation

struct ServerConfig: Codable {
    var host: String = "0.0.0.0"
    var port: Int = 8089
    var language: String = "zh_CN"
}

struct StorageVolume: Codable {
    var name: String
    var path: String
    var quota_gb: Int?
    var used_gb: Double?
    var available_gb: Double?
}

struct StorageConfig: Codable {
    var volumes: [StorageVolume] = []
}

struct SMBConfig: Codable {
    var enabled: Bool = true
    var port: Int = 445
    var workgroup: String = "WORKGROUP"
}

struct PushTarget: Codable {
    var name: String
    var ip: String
    var port: Int
}

struct PushConfig: Codable {
    var targets: [PushTarget] = []
}

struct I18nConfig: Codable {
    var `default`: String = "zh_CN"
    var supported: [String] = []
}

struct Config: Codable {
    var server: ServerConfig = ServerConfig()
    var storage: StorageConfig = StorageConfig()
    var smb: SMBConfig = SMBConfig()
    var push: PushConfig = PushConfig()
    var i18n: I18nConfig = I18nConfig()
    var data_dir: String = "nas_data"
    var receive_dir: String = "nas_data/received"
}

struct User: Codable {
    var username: String
    var password: String
    var role: String = "user"
    var created_at: String
}

struct SMBShare: Codable {
    var name: String
    var path: String
    var readonly: Bool = false
    var users: [String] = []
}

struct APIResponse: Codable {
    var success: Bool
    var message: String?
    var data: Codable?
}

struct PushStatus: Codable {
    var id: String
    var source_ip: String
    var folder: String
    var file_count: Int
    var status: String
    var timestamp: String
}