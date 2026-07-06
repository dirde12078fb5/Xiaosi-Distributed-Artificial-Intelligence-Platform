using System.Text.Json;
using NasServer.Models;

namespace NasServer.Services;

public class ConfigService
{
    private readonly string _configPath = "../config/config.json";
    private NasConfig? _config;
    private readonly JsonSerializerOptions _jsonOptions = new() { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower };

    public NasConfig GetConfig()
    {
        if (_config != null) return _config;

        if (File.Exists(_configPath))
        {
            var json = File.ReadAllText(_configPath);
            _config = JsonSerializer.Deserialize<NasConfig>(json, _jsonOptions);
        }
        else
        {
            _config = new NasConfig();
            SaveConfig(_config);
        }

        return _config!;
    }

    public void SaveConfig(NasConfig config)
    {
        _config = config;
        var json = JsonSerializer.Serialize(config, _jsonOptions);
        Directory.CreateDirectory(Path.GetDirectoryName(_configPath)!);
        File.WriteAllText(_configPath, json);
    }

    public void UpdateConfig(Action<NasConfig> updateAction)
    {
        var config = GetConfig();
        updateAction(config);
        SaveConfig(config);
    }
}