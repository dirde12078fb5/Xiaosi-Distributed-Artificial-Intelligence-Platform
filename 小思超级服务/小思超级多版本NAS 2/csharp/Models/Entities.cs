namespace NasServer.Models;

public class NasConfig
{
    public ServerConfig Server { get; set; } = new();
    public StorageConfig Storage { get; set; } = new();
    public SmbConfig Smb { get; set; } = new();
    public PushConfig Push { get; set; } = new();
    public string DataDir { get; set; } = "nas_data";
    public string ReceiveDir { get; set; } = "nas_data/received";
}

public class ServerConfig
{
    public string Host { get; set; } = "0.0.0.0";
    public int Port { get; set; } = 8085;
    public string Language { get; set; } = "zh_CN";
}

public class StorageConfig
{
    public List<Volume> Volumes { get; set; } = new();
}

public class SmbConfig
{
    public bool Enabled { get; set; } = true;
    public int Port { get; set; } = 445;
    public string Workgroup { get; set; } = "WORKGROUP";
}

public class PushConfig
{
    public List<PushTarget> Targets { get; set; } = new();
}

public class Volume
{
    public string Name { get; set; } = string.Empty;
    public string Path { get; set; } = string.Empty;
    public long QuotaGb { get; set; } = 1000;
    public DateTime CreatedAt { get; set; } = DateTime.Now;
}

public class User
{
    public string Username { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; } = DateTime.Now;
}

public class SmbShare
{
    public string Name { get; set; } = string.Empty;
    public string Path { get; set; } = string.Empty;
    public string Permissions { get; set; } = "rw";
    public DateTime CreatedAt { get; set; } = DateTime.Now;
}

public class PushTarget
{
    public string Name { get; set; } = string.Empty;
    public string Address { get; set; } = string.Empty;
    public int Port { get; set; } = 8080;
}

public class PushRecord
{
    public string Id { get; set; } = Guid.NewGuid().ToString();
    public string Folder { get; set; } = string.Empty;
    public string Target { get; set; } = string.Empty;
    public string Status { get; set; } = "pending";
    public int FilesCount { get; set; }
    public DateTime StartTime { get; set; } = DateTime.Now;
    public DateTime? EndTime { get; set; }
}

public class ApiResponse<T>
{
    public bool Success { get; set; }
    public string Message { get; set; } = string.Empty;
    public T? Data { get; set; }
    public string Language { get; set; } = "zh_CN";
}

public class I18nData
{
    public string AppName { get; set; } = string.Empty;
    public string Welcome { get; set; } = string.Empty;
    public ApiTranslations Api { get; set; } = new();
    public StatusTranslations Status { get; set; } = new();
    public MenuTranslations Menu { get; set; } = new();
}

public class ApiTranslations
{
    public StorageTranslations Storage { get; set; } = new();
    public UserTranslations Users { get; set; } = new();
    public SmbTranslations Smb { get; set; } = new();
    public IpTranslations Ip { get; set; } = new();
    public PushTranslations Push { get; set; } = new();
}

public class StorageTranslations
{
    public string Volumes { get; set; } = string.Empty;
    public string CreateVolume { get; set; } = string.Empty;
    public string DeleteVolume { get; set; } = string.Empty;
    public string VolumeName { get; set; } = string.Empty;
    public string VolumePath { get; set; } = string.Empty;
    public string Quota { get; set; } = string.Empty;
}

public class UserTranslations
{
    public string Users { get; set; } = string.Empty;
    public string CreateUser { get; set; } = string.Empty;
    public string DeleteUser { get; set; } = string.Empty;
    public string Username { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
}

public class SmbTranslations
{
    public string Shares { get; set; } = string.Empty;
    public string CreateShare { get; set; } = string.Empty;
    public string DeleteShare { get; set; } = string.Empty;
    public string ShareName { get; set; } = string.Empty;
    public string SharePath { get; set; } = string.Empty;
}

public class IpTranslations
{
    public string LocalIp { get; set; } = string.Empty;
    public string ScanDevices { get; set; } = string.Empty;
}

public class PushTranslations
{
    public string PushFolder { get; set; } = string.Empty;
    public string PushTargets { get; set; } = string.Empty;
    public string AddTarget { get; set; } = string.Empty;
    public string PushStatus { get; set; } = string.Empty;
    public string ReceiveFile { get; set; } = string.Empty;
}

public class StatusTranslations
{
    public string Success { get; set; } = string.Empty;
    public string Error { get; set; } = string.Empty;
    public string NotFound { get; set; } = string.Empty;
    public string InvalidParams { get; set; } = string.Empty;
}

public class MenuTranslations
{
    public string Home { get; set; } = string.Empty;
    public string Storage { get; set; } = string.Empty;
    public string Users { get; set; } = string.Empty;
    public string Smb { get; set; } = string.Empty;
    public string Push { get; set; } = string.Empty;
    public string Settings { get; set; } = string.Empty;
}