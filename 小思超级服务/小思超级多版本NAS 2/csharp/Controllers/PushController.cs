using Microsoft.AspNetCore.Mvc;
using NasServer.Models;
using NasServer.Services;

namespace NasServer.Controllers;

[ApiController]
[Route("api/push")]
public class PushController : ControllerBase
{
    private readonly PushService _pushService;
    private readonly ConfigService _configService;

    public PushController(PushService pushService, ConfigService configService)
    {
        _pushService = pushService;
        _configService = configService;
    }

    [HttpGet("targets")]
    public IActionResult GetTargets()
    {
        var targets = _pushService.GetTargets();
        return Ok(new ApiResponse<List<PushTarget>>
        {
            Success = true,
            Message = "success",
            Data = targets,
            Language = _configService.GetConfig().Server.Language
        });
    }

    [HttpPost("targets")]
    public IActionResult AddTarget([FromBody] AddPushTargetRequest request)
    {
        if (string.IsNullOrEmpty(request.Name) || string.IsNullOrEmpty(request.Address))
        {
            return BadRequest(new ApiResponse<PushTarget>
            {
                Success = false,
                Message = "invalid_params",
                Language = _configService.GetConfig().Server.Language
            });
        }

        var target = _pushService.AddTarget(request.Name, request.Address, request.Port);

        if (target == null)
        {
            return BadRequest(new ApiResponse<PushTarget>
            {
                Success = false,
                Message = "Target already exists",
                Language = _configService.GetConfig().Server.Language
            });
        }

        return Ok(new ApiResponse<PushTarget>
        {
            Success = true,
            Message = "success",
            Data = target,
            Language = _configService.GetConfig().Server.Language
        });
    }

    [HttpPost("folder")]
    public async Task<IActionResult> PushFolder([FromBody] PushFolderRequest request)
    {
        if (string.IsNullOrEmpty(request.Folder) || string.IsNullOrEmpty(request.Target))
        {
            return BadRequest(new ApiResponse<object>
            {
                Success = false,
                Message = "invalid_params",
                Language = _configService.GetConfig().Server.Language
            });
        }

        var result = await _pushService.PushFolderAsync(request.Folder, request.Target);

        if (!result)
        {
            return BadRequest(new ApiResponse<object>
            {
                Success = false,
                Message = "Push failed",
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

    [HttpGet("status")]
    public IActionResult GetStatus()
    {
        var records = _pushService.GetRecords();
        return Ok(new ApiResponse<List<PushRecord>>
        {
            Success = true,
            Message = "success",
            Data = records,
            Language = _configService.GetConfig().Server.Language
        });
    }

    [HttpPost("receive")]
    public async Task<IActionResult> ReceiveFile()
    {
        if (!Request.HasFormContentType)
        {
            return BadRequest(new ApiResponse<object>
            {
                Success = false,
                Message = "invalid_params",
                Language = _configService.GetConfig().Server.Language
            });
        }

        var form = await Request.ReadFormAsync();
        var folder = form["folder"].FirstOrDefault() ?? "unknown";
        var filepath = form["filepath"].FirstOrDefault() ?? "";
        var file = form.Files.FirstOrDefault();

        if (file == null)
        {
            return BadRequest(new ApiResponse<object>
            {
                Success = false,
                Message = "No file provided",
                Language = _configService.GetConfig().Server.Language
            });
        }

        var receiveDir = _configService.GetConfig().ReceiveDir;
        var fullDir = Path.Combine(receiveDir, folder);
        Directory.CreateDirectory(fullDir);

        var filePath = Path.Combine(fullDir, filepath);
        Directory.CreateDirectory(Path.GetDirectoryName(filePath)!);

        using (var stream = file.OpenReadStream())
        {
            using var fileStream = File.Create(filePath);
            await stream.CopyToAsync(fileStream);
        }

        return Ok(new ApiResponse<object>
        {
            Success = true,
            Message = "success",
            Language = _configService.GetConfig().Server.Language
        });
    }
}