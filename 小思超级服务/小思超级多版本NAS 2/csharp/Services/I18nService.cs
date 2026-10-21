using System.Text.Json;
using NasServer.Models;

namespace NasServer.Services;

public class I18nService
{
    private readonly string _i18nPath = "../config/i18n";
    private readonly JsonSerializerOptions _jsonOptions = new() { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower };

    public I18nData? GetTranslation(string lang)
    {
        var filePath = Path.Combine(_i18nPath, $"{lang}.json");

        if (!File.Exists(filePath))
            return null;

        var json = File.ReadAllText(filePath);
        return JsonSerializer.Deserialize<I18nData>(json, _jsonOptions);
    }
}