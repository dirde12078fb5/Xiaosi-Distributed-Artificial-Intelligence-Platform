using Microsoft.AspNetCore.Mvc;
using NasServer.Models;
using NasServer.Services;

namespace NasServer.Controllers;

[ApiController]
[Route("api/ip")]
public class IpController : ControllerBase
{
    private readonly IpService _ipService;
    private readonly ConfigService _configService;

    public IpController(IpService ipService, ConfigService configService)
    {
        _ipService = ipService;
        _configService = configService;
    }

    [HttpGet("local")]
    public IActionResult GetLocalIp()
    {
        var ips = _ipService.GetLocalIpAddresses();
        return Ok(new ApiResponse<List<string>>
        {
            Success = true,
            Message = "success",
            Data = ips,
            Language = _configService.GetConfig().Server.Language
        });
    }

    [HttpGet("scan")]
    public async Task<IActionResult> ScanDevices([FromQuery] int port = 8080)
    {
        var devices = await _ipService.ScanLanDevices(port);
        return Ok(new ApiResponse<List<string>>
        {
            Success = true,
            Message = "success",
            Data = devices,
            Language = _configService.GetConfig().Server.Language
        });
    }
}