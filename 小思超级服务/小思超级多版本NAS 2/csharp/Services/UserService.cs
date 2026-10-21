using System.Text.Json;
using NasServer.Models;

namespace NasServer.Services;

public class UserService
{
    private readonly string _usersPath = "../nas_data/users.json";
    private List<User>? _users;
    private readonly JsonSerializerOptions _jsonOptions = new() { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower };

    public List<User> GetUsers()
    {
        if (_users != null) return _users;

        if (File.Exists(_usersPath))
        {
            var json = File.ReadAllText(_usersPath);
            _users = JsonSerializer.Deserialize<List<User>>(json, _jsonOptions) ?? new List<User>();
        }
        else
        {
            _users = new List<User>();
            SaveUsers();
        }

        return _users;
    }

    private void SaveUsers()
    {
        Directory.CreateDirectory(Path.GetDirectoryName(_usersPath)!);
        var json = JsonSerializer.Serialize(_users, _jsonOptions);
        File.WriteAllText(_usersPath, json);
    }

    public User? CreateUser(string username, string password)
    {
        var users = GetUsers();

        if (users.Any(u => u.Username == username))
            return null;

        var user = new User
        {
            Username = username,
            Password = HashPassword(password),
            CreatedAt = DateTime.Now
        };

        users.Add(user);
        SaveUsers();

        return user;
    }

    public bool DeleteUser(string username)
    {
        var users = GetUsers();
        var user = users.FirstOrDefault(u => u.Username == username);

        if (user == null) return false;

        users.Remove(user);
        SaveUsers();

        return true;
    }

    private static string HashPassword(string password)
    {
        using var sha256 = System.Security.Cryptography.SHA256.Create();
        var bytes = System.Security.Cryptography.SHA256.HashData(System.Text.Encoding.UTF8.GetBytes(password));
        return Convert.ToHexString(bytes).ToLower();
    }
}