using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using NasServer.Services;

var builder = WebApplication.CreateBuilder(new WebApplicationOptions
{
    Args = args,
    ContentRootPath = AppDomain.CurrentDomain.BaseDirectory
});

builder.Services.AddSingleton<ConfigService>();
builder.Services.AddSingleton<StorageService>();
builder.Services.AddSingleton<UserService>();
builder.Services.AddSingleton<SmbService>();
builder.Services.AddSingleton<IpService>();
builder.Services.AddSingleton<PushService>();
builder.Services.AddSingleton<I18nService>();

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

builder.WebHost.ConfigureKestrel(options =>
{
    var configService = new ConfigService();
    var config = configService.GetConfig();
    options.ListenAnyIP(config.Server.Port);
});

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseRouting();
app.MapControllers();

app.MapGet("/", () => "小思超级NAS服务 - C#版本 (端口: 8085)");

var configService = app.Services.GetRequiredService<ConfigService>();
var config = configService.GetConfig();

Console.WriteLine($"小思超级NAS服务已启动");
Console.WriteLine($"服务地址: http://{config.Server.Host}:{config.Server.Port}");
Console.WriteLine($"语言: {config.Server.Language}");
Console.WriteLine($"数据目录: {config.DataDir}");

app.Run();