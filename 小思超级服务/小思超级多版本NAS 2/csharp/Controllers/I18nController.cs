using Microsoft.AspNetCore.Mvc;
using NasServer.Models;
using NasServer.Services;

namespace NasServer.Controllers;

[ApiController]
[Route("api/i18n")]
public class I18nController : ControllerBase
{
    private readonly I18nService _i18nService;
    private readonly ConfigService _configService;

    public I18nController(I18nService i18nService, ConfigService configService)
    {
        _i18nService = i18nService;
        _configService = configService;
    }

    [HttpGet]
    public IActionResult GetTranslation([FromQuery] string? lang)
    {
        var language = lang ?? _configService.GetConfig().Server.Language;
        var translation = _i18nService.GetTranslation(language);

        if (translation == null)
        {
            return NotFound(new ApiResponse<I18nData>
            {
                Success = false,
                Message = "not_found",
                Language = language
            });
        }

        return Ok(new ApiResponse<I18nData>
        {
            Success = true,
            Message = "success",
            Data = translation,
            Language = language
        });
    }
}