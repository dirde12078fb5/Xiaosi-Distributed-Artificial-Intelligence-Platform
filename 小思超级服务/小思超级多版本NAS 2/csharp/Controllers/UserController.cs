using Microsoft.AspNetCore.Mvc;
using NasServer.Models;
using NasServer.Services;

namespace NasServer.Controllers;

[ApiController]
[Route("api/users")]
public class UserController : ControllerBase
{
    private readonly UserService _userService;
    private readonly ConfigService _configService;

    public UserController(UserService userService, ConfigService configService)
    {
        _userService = userService;
        _configService = configService;
    }

    [HttpGet]
    public IActionResult GetUsers()
    {
        var users = _userService.GetUsers();
        return Ok(new ApiResponse<List<User>>
        {
            Success = true,
            Message = "success",
            Data = users,
            Language = _configService.GetConfig().Server.Language
        });
    }

    [HttpPost]
    public IActionResult CreateUser([FromBody] CreateUserRequest request)
    {
        if (string.IsNullOrEmpty(request.Username) || string.IsNullOrEmpty(request.Password))
        {
            return BadRequest(new ApiResponse<User>
            {
                Success = false,
                Message = "invalid_params",
                Language = _configService.GetConfig().Server.Language
            });
        }

        var user = _userService.CreateUser(request.Username, request.Password);

        if (user == null)
        {
            return BadRequest(new ApiResponse<User>
            {
                Success = false,
                Message = "User already exists",
                Language = _configService.GetConfig().Server.Language
            });
        }

        return Ok(new ApiResponse<User>
        {
            Success = true,
            Message = "success",
            Data = user,
            Language = _configService.GetConfig().Server.Language
        });
    }

    [HttpPost("delete")]
    public IActionResult DeleteUser([FromBody] DeleteUserRequest request)
    {
        if (string.IsNullOrEmpty(request.Username))
        {
            return BadRequest(new ApiResponse<object>
            {
                Success = false,
                Message = "invalid_params",
                Language = _configService.GetConfig().Server.Language
            });
        }

        var result = _userService.DeleteUser(request.Username);

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