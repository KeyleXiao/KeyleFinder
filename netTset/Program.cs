// See https://aka.ms/new-console-template for more information
using System;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using Newtonsoft;


var netHelper = new NetHelper();

Console.WriteLine("输入端口(先启动KeyleKitService.py脚本)：");
var port = Console.ReadLine();

await netHelper.ConnectAsync("127.0.0.1", int.Parse(port));

CancellationTokenSource cts = new CancellationTokenSource();
var ta = Task.Run(netHelper.ReceiveMessageAsync, cts.Token);

while (true)
{
    Console.WriteLine("输入任意消息回车发送，输入exit退出：");
    var content = Console.ReadLine();

    // 发送消息给服务器
    await netHelper.SendMessageAsync(content);

    if (content == "exit")
    {
        cts.Cancel();
        break;
    }

    if (content == "test")
    {
        List<string> imgs = new List<string>();

        imgs.Add("/Users/keyle/Documents/KeyleFinder.git/demo/layer.png");
        imgs.Add("/Users/keyle/Documents/KeyleFinder.git/demo/middle.png");
        var imgData = JsonSerializer.Serialize(imgs);

        await netHelper.SendMessageAsync(imgData);
    }
}
// 关闭连接
netHelper.Close();
Console.ReadLine(); // 等待用户按下回车键退出


public class NetHelper
{
    private TcpClient client;
    private NetworkStream stream;

    public NetHelper()
    {
        client = new TcpClient();
    }

    public async Task ConnectAsync(string ipAddress, int port)
    {
        try
        {
            await client.ConnectAsync(ipAddress, port);
            stream = client.GetStream();
            Console.WriteLine("连接到服务器成功");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"无法连接到服务器: {ex.Message}");
        }
    }

    public async Task SendMessageAsync(string message)
    {
        try
        {
            byte[] data = Encoding.UTF8.GetBytes(message);
            await stream.WriteAsync(data, 0, data.Length);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"发送消息失败: {ex.Message}");
        }
    }

    public async Task SendMessageAsync(byte[] data)
    {
        try
        {
            await stream.WriteAsync(data, 0, data.Length);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"发送消息失败: {ex.Message}");
        }
    }

    public async Task<string> ReceiveMessageAsync()
    {
        try
        {
            byte[] data = new byte[1024 * 1024];
            int bytes = await stream.ReadAsync(data, 0, data.Length);
            string receivedMessage = Encoding.UTF8.GetString(data, 0, bytes);
            Console.WriteLine("服务器回复：" + receivedMessage);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"接收消息失败: {ex.Message}");
            return null;
        }

        return await ReceiveMessageAsync();
    }

    public void Close()
    {
        stream.Close();
        client.Close();
        Console.WriteLine("连接已关闭");
    }
}
