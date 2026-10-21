using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;

namespace NasServer.Services;

public class IpService
{
    public List<string> GetLocalIpAddresses()
    {
        var ips = new List<string>();

        foreach (var networkInterface in NetworkInterface.GetAllNetworkInterfaces())
        {
            if (networkInterface.OperationalStatus != OperationalStatus.Up)
                continue;

            var ipProps = networkInterface.GetIPProperties();
            foreach (var ipAddr in ipProps.UnicastAddresses)
            {
                if (ipAddr.Address.AddressFamily == AddressFamily.InterNetwork)
                {
                    ips.Add(ipAddr.Address.ToString());
                }
            }
        }

        return ips;
    }

    public async Task<List<string>> ScanLanDevices(int port)
    {
        var devices = new List<string>();
        var localIps = GetLocalIpAddresses();

        foreach (var localIp in localIps)
        {
            var parts = localIp.Split('.');
            if (parts.Length != 4) continue;

            var subnet = $"{parts[0]}.{parts[1]}.{parts[2]}";

            for (int i = 1; i < 255; i++)
            {
                var targetIp = $"{subnet}.{i}";
                if (targetIp == localIp) continue;

                try
                {
                    using var client = new TcpClient();
                    var connectTask = client.ConnectAsync(targetIp, port);
                    await Task.WhenAny(connectTask, Task.Delay(100));

                    if (client.Connected)
                    {
                        devices.Add($"{targetIp}:{port}");
                    }
                }
                catch
                {
                    // Ignore connection failures
                }
            }
        }

        return devices;
    }
}