using System.Text.Json;
using NasServer.Models;

namespace NasServer.Services;

public class SmbService
{
    private readonly string _sharesPath = "../nas_data/smb_shares.json";
    private List<SmbShare>? _shares;
    private readonly JsonSerializerOptions _jsonOptions = new() { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower };

    public List<SmbShare> GetShares()
    {
        if (_shares != null) return _shares;

        if (File.Exists(_sharesPath))
        {
            var json = File.ReadAllText(_sharesPath);
            _shares = JsonSerializer.Deserialize<List<SmbShare>>(json, _jsonOptions) ?? new List<SmbShare>();
        }
        else
        {
            _shares = new List<SmbShare>();
            SaveShares();
        }

        return _shares;
    }

    private void SaveShares()
    {
        Directory.CreateDirectory(Path.GetDirectoryName(_sharesPath)!);
        var json = JsonSerializer.Serialize(_shares, _jsonOptions);
        File.WriteAllText(_sharesPath, json);
    }

    public SmbShare? CreateShare(string name, string path, string permissions)
    {
        var shares = GetShares();

        if (shares.Any(s => s.Name == name))
            return null;

        var share = new SmbShare
        {
            Name = name,
            Path = path,
            Permissions = permissions,
            CreatedAt = DateTime.Now
        };

        shares.Add(share);
        SaveShares();

        Directory.CreateDirectory(path);

        return share;
    }

    public bool DeleteShare(string name)
    {
        var shares = GetShares();
        var share = shares.FirstOrDefault(s => s.Name == name);

        if (share == null) return false;

        shares.Remove(share);
        SaveShares();

        return true;
    }
}