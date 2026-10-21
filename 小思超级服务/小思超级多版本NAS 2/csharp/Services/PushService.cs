using System.Text.Json;
using NasServer.Models;

namespace NasServer.Services;

public class PushService
{
    private readonly ConfigService _configService;
    private readonly string _recordsPath = "../nas_data/push_records.json";
    private List<PushRecord>? _records;
    private readonly JsonSerializerOptions _jsonOptions = new() { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower };

    public PushService(ConfigService configService)
    {
        _configService = configService;
    }

    public List<PushTarget> GetTargets()
    {
        return _configService.GetConfig().Push.Targets;
    }

    public PushTarget? AddTarget(string name, string address, int port)
    {
        var config = _configService.GetConfig();

        if (config.Push.Targets.Any(t => t.Name == name))
            return null;

        var target = new PushTarget
        {
            Name = name,
            Address = address,
            Port = port
        };

        config.Push.Targets.Add(target);
        _configService.SaveConfig(config);

        return target;
    }

    public List<PushRecord> GetRecords()
    {
        if (_records != null) return _records;

        if (File.Exists(_recordsPath))
        {
            var json = File.ReadAllText(_recordsPath);
            _records = JsonSerializer.Deserialize<List<PushRecord>>(json, _jsonOptions) ?? new List<PushRecord>();
        }
        else
        {
            _records = new List<PushRecord>();
            SaveRecords();
        }

        return _records;
    }

    private void SaveRecords()
    {
        Directory.CreateDirectory(Path.GetDirectoryName(_recordsPath)!);
        var json = JsonSerializer.Serialize(_records, _jsonOptions);
        File.WriteAllText(_recordsPath, json);
    }

    public PushRecord CreateRecord(string folder, string target)
    {
        var records = GetRecords();

        var record = new PushRecord
        {
            Folder = folder,
            Target = target,
            Status = "pending",
            StartTime = DateTime.Now
        };

        records.Add(record);
        SaveRecords();

        return record;
    }

    public void UpdateRecord(string id, string status, int filesCount)
    {
        var records = GetRecords();
        var record = records.FirstOrDefault(r => r.Id == id);

        if (record != null)
        {
            record.Status = status;
            record.FilesCount = filesCount;
            record.EndTime = DateTime.Now;
            SaveRecords();
        }
    }

    public async Task<bool> PushFolderAsync(string folderPath, string targetName)
    {
        var config = _configService.GetConfig();
        var target = config.Push.Targets.FirstOrDefault(t => t.Name == targetName);

        if (target == null) return false;

        if (!Directory.Exists(folderPath)) return false;

        var record = CreateRecord(folderPath, targetName);
        var filesCount = 0;

        try
        {
            using var client = new HttpClient();
            var files = Directory.GetFiles(folderPath, "*", SearchOption.AllDirectories);

            foreach (var file in files)
            {
                var relativePath = file.Substring(folderPath.Length).TrimStart('\\', '/');

                using var formData = new MultipartFormDataContent();
                formData.Add(new StringContent(Path.GetFileName(folderPath)), "folder");
                formData.Add(new StringContent(relativePath), "filepath");

                var fileBytes = await File.ReadAllBytesAsync(file);
                formData.Add(new ByteArrayContent(fileBytes), "file", Path.GetFileName(file));

                var url = $"http://{target.Address}:{target.Port}/api/push/receive";
                await client.PostAsync(url, formData);

                filesCount++;
            }

            UpdateRecord(record.Id, "completed", filesCount);
            return true;
        }
        catch
        {
            UpdateRecord(record.Id, "failed", filesCount);
            return false;
        }
    }
}