using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ConnectTool
{
    static ConnectTool instance;

    private ConnectTool() { Task task = StartAsync(); }

    public static ConnectTool ins 
    {
        get 
        {
            if (instance == null)
            {
                instance = new ConnectTool(); 
            }
            return instance;
        }
    }
    private const int Port = 12580; // 服务器监听的端口号
    private const string ServerIp = "127.0.0.1"; // 服务器的IP地址


}

