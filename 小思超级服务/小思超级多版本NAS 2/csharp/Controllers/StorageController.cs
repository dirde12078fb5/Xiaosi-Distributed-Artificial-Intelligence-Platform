using Microsoft.AspNetCore.Mvc;
using NasServer.Models;
using NasServer.Services;

namespace NasServer.Controllers;

[ApiController]
[Route("api/storage")]
public class StorageController : ControllerBase
{
    private readonly StorageService _storageService;
    private readonly ConfigService _configService;

    public StorageController(StorageService storageService, ConfigService configService)
    {
        _storageService = storageService;
        _configService = configService;
    }

    [HttpGet("volumes")]
    public IActionResult GetVolumes()
    {
        var volumes = _storageService.GetVolumes();
        return Ok(new ApiResponse<List<Volume>>
        {
            Success = true,
            Message = "success",
            Data = volumes,
            Language = _configService.GetConfig().Server.Language
        });
    }

    [HttpPost("volumes")]
    public IActionResult CreateVolume([FromBody] CreateVolumeRequest request)
    {
        if (string.IsNullOrEmpty(request.Name) || string.IsNullOrEmpty(request.Path))
        {
            return BadRequest(new ApiResponse<Volume>
            {
                Success = false,
                Message = "invalid_params",
                Language = _configService.GetConfig().Server.Language
            });
        }

        var volume = _storageService.CreateVolume(request.Name, request.Path, request.QuotaGb);

        if (volume == null)
        {
            return BadRequest(new ApiResponse<Volume>
            {
                Success = false,
                Message = "Volume already exists",
                Language = _configService.GetConfig().Server.Language
            });
        }

        return Ok(new ApiResponse<Volume>
        {
            Success = true,
            Message = "success",
            Data = volume,
            Language = _configService.GetConfig().Server.Language
        });
    }

    [HttpPost("volumes/delete")]
    public IActionResult DeleteVolume([FromBody] DeleteVolumeRequest request)
    {
        if (string.IsNullOrEmpty(request.Name))
        {
            return BadRequest(new ApiResponse<object>
            {
                Success = false,
                Message = "invalid_params",
                Language = _configService.GetConfig().Server.Language
            });
        }

        var result = _storageService.DeleteVolume(request.Name);

        if (!result)
        {
            return NotFound(new ApiResponse<object>
            {
                Success = false,
                Message = "not_found",
                Language = _configService.GetConfig().Server.Language
            });
        }

        return Ok(new ApiResponse<object>
        {
            Success = true,
            Message = "success",
            Language = _configService.GetConfig().Server.Language
        });
    }
}