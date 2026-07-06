using Microsoft.AspNetCore.Mvc;
using NasServer.Models;
using NasServer.Services;

namespace NasServer.Controllers;

[ApiController]
[Route("api/smb")]
public class SmbController : ControllerBase
{
    private readonly SmbService _smbService;
    private readonly ConfigService _configService;

    public SmbController(SmbService smbService, ConfigService configService)
    {
        _smbService = smbService;
        _configService = configService;
    }

    [HttpGet("shares")]
    public IActionResult GetShares()
    {
        var shares = _smbService.GetShares();
        return Ok(new ApiResponse<List<SmbShare>>
        {
            Success = true,
            Message = "success",
            Data = shares,
            Language = _configService.GetConfig().Server.Language
        });
    }

    [HttpPost("shares")]
    public IActionResult CreateShare([FromBody] CreateShareRequest request)
    {
        if (string.IsNullOrEmpty(request.Name) || string.IsNullOrEmpty(request.Path))
        {
            return BadRequest(new ApiResponse<SmbShare>
            {
                Success = false,
                Message = "invalid_params",
                Language = _configService.GetConfig().Server.Language
            });
        }

        var share = _smbService.CreateShare(request.Name, request.Path, request.Permissions);

        if (share == null)
        {
            return BadRequest(new ApiResponse<SmbShare>
            {
                Success = false,
                Message = "Share already exists",
                Language = _configService.GetConfig().Server.Language
            });
        }

        return Ok(new ApiResponse<SmbShare>
        {
            Success = true,
            Message = "success",
            Data = share,
            Language = _configService.GetConfig().Server.Language
        });
    }

    [HttpPost("shares/delete")]
    public IActionResult DeleteShare([FromBody] DeleteShareRequest request)
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

        var result = _smbService.DeleteShare(request.Name);

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