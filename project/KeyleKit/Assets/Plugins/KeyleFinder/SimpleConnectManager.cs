using System;
using System.Buffers;
using System.Net;
using System.Net.Sockets;
using System.Net.Sockets.Kcp;
using System.Threading.Tasks;
using UnityEngine;

public class SimpleConnectManager
{
    Connection connection;
    static SimpleConnectManager instance;

    private SimpleConnectManager() 
    {
        Start();
    }

    public static SimpleConnectManager ins 
    {
        get 
        {
            if (instance == null)
            {
                instance = new SimpleConnectManager(); 
            }
            return instance;
        }
    }


    void Start() 
    {
        IPEndPoint end = new System.Net.IPEndPoint(System.Net.IPAddress.Loopback, 50001);
        connection = new Connection(50002, end);

        Task.Run(async () =>
        {
            while (true)
            {
                connection.kcp.Update(DateTimeOffset.UtcNow);
                await Task.Delay(10);
            }
        });

        StartRecv(connection);
    }

    async void StartRecv(Connection client)
    {
        while (true)
        {
            var res = await client.ReceiveAsync();
            var str = System.Text.Encoding.UTF8.GetString(res);

            //if ("发送一条消息" == str)
            //{
            //    Console.WriteLine(str);

            //    var buffer = System.Text.Encoding.UTF8.GetBytes("回复一条消息");
            //    client.SendAsync(buffer, buffer.Length);
            //}
        }
    }


}


public class Connection : IKcpCallback
{
    UdpClient client;
    public Connection(int port)
        : this(port, null)
    {
    }

    public Connection(int port, System.Net.IPEndPoint endPoint)
    {
        client = new UdpClient(port);
        kcp = new SimpleSegManager.Kcp(2001, this);
        this.EndPoint = endPoint;
        BeginRecv();
    }

    public SimpleSegManager.Kcp kcp { get; }
    public IPEndPoint EndPoint { get; set; }

    public void Output(IMemoryOwner<byte> buffer, int avalidLength)
    {
        var s = buffer.Memory.Span.Slice(0, avalidLength).ToArray();
        client.SendAsync(s, s.Length, EndPoint);
        buffer.Dispose();
    }

    public async void SendAsync(byte[] datagram, int bytes)
    {
        kcp.Send(datagram.AsSpan().Slice(0, bytes));
    }

    public async ValueTask<byte[]> ReceiveAsync()
    {
        var (buffer, avalidLength) = kcp.TryRecv();
        while (buffer == null)
        {
            await Task.Delay(10);
            (buffer, avalidLength) = kcp.TryRecv();
        }

        var s = buffer.Memory.Span.Slice(0, avalidLength).ToArray();
        return s;
    }

    private async void BeginRecv()
    {
        var res = await client.ReceiveAsync();
        EndPoint = res.RemoteEndPoint;
        kcp.Input(res.Buffer);
        BeginRecv();
    }
}