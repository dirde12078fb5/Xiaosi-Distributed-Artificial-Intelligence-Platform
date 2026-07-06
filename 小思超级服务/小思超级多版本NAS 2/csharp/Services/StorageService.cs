using NasServer.Models;

namespace NasServer.Services;

public class StorageService
{
    private readonly ConfigService _configService;

    public StorageService(ConfigService configService)
    {
        _configService = configService;
    }

    public List<Volume> GetVolumes()
    {
        return _configService.GetConfig().Storage.Volumes;
    }

    public Volume? CreateVolume(string name, string path, long quotaGb)
    {
        var config = _configService.GetConfig();

        if (config.Storage.Volumes.Any(v => v.Name == name))
            return null;

        var volume = new Volume
        {
            Name = name,
            Path = path,
            QuotaGb = quotaGb,
            CreatedAt = DateTime.Now
        };

        config.Storage.Volumes.Add(volume);
        _configService.SaveConfig(config);

        Directory.CreateDirectory(path);

        return volume;
    }

    public bool DeleteVolume(string name)
    {
        var config = _configService.GetConfig();
        var volume = config.Storage.Volumes.FirstOrDefault(v => v.Name == name);

        if (volume == null) return false;

        config.Storage.Volumes.Remove(volume);
        _configService.SaveConfig(config);

        return true;
    }
}