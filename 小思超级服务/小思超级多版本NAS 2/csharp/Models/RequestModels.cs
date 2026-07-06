namespace NasServer.Models;

public class CreateVolumeRequest
{
    public string Name { get; set; } = string.Empty;
    public string Path { get; set; } = string.Empty;
    public long QuotaGb { get; set; } = 1000;
}

public class DeleteVolumeRequest
{
    public string Name { get; set; } = string.Empty;
}

public class CreateUserRequest
{
    public string Username { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
}

public class DeleteUserRequest
{
    public string Username { get; set; } = string.Empty;
}

public class CreateShareRequest
{
    public string Name { get; set; } = string.Empty;
    public string Path { get; set; } = string.Empty;
    public string Permissions { get; set; } = "rw";
}

public class DeleteShareRequest
{
    public string Name { get; set; } = string.Empty;
}

public class AddPushTargetRequest
{
    public string Name { get; set; } = string.Empty;
    public string Address { get; set; } = string.Empty;
    public int Port { get; set; } = 8080;
}

public class PushFolderRequest
{
    public string Folder { get; set; } = string.Empty;
    public string Target { get; set; } = string.Empty;
}