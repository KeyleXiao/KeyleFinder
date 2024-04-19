using UnityEngine;
using System;
using System.Runtime.InteropServices;
using UnityEngine.EventSystems;
using System.Collections.Generic;
using System.Diagnostics;

public class InitAPP : MonoBehaviour
{
    public Rect screenPosition;
    [DllImport("user32.dll")]
    static extern IntPtr SetWindowLong(IntPtr hwnd, int _nIndex, int dwNewLong);
    [DllImport("user32.dll")]
    static extern bool SetWindowPos(IntPtr hWnd, int hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);

    [DllImport("user32.dll")]
    static extern IntPtr GetForegroundWindow();//获取当前获取了焦点的窗口句柄

    [DllImport("user32.dll")]
    public static extern bool ReleaseCapture();
    [DllImport("user32.dll")]
    public static extern bool SendMessage(IntPtr hwnd, int wMsg, int wParam, int lParam);

    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hwnd, int nCmdShow);

    [DllImport("user32.dll")]
    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

    // GetSystemMetrics实际获取的是系统记录的分辨率，不是物理分辨率，如屏幕2560*1600，显示缩放200%，这里获取到的是1280*800
    [DllImport("user32.dll", SetLastError = true)]



    private static extern int GetSystemMetrics(int nIndex);
    private static int SM_CXSCREEN = 0; //主屏幕分辨率宽度
    private static int SM_CYSCREEN = 1; //主屏幕分辨率高度
    private static int SM_CYCAPTION = 4; //标题栏高度
    private static int SM_CXFULLSCREEN = 16; //最大化窗口宽度（减去任务栏）
    private static int SM_CYFULLSCREEN = 17; //最大化窗口高度（减去任务栏）

    const uint SWP_SHOWWINDOW = 0x0040;
    const int GWL_STYLE = -16;
    const int WS_BORDER = 1;
    const int WS_POPUP = 0x800000;
    const int SW_SHOWMINIMIZED = 2; //{最小化, 激活}
    const int SW_SHOWMAXIMIZED = 3; //{最大化, 激活} 
    const int SW_SHOWRESTORE = 1;//还原

    IntPtr Handle;
    float xx;
    bool bx;

    private const int initWidth = 1920;
    private const int initHeight = 1080;



    int newWidth;
    int newHeight;


    public GameObject maxButton;
    public GameObject midButton;


    private void Start()
    {
        bx = false;
        xx = 0f;

        // 屏幕分辨率
        newWidth = GetSystemMetrics(SM_CXSCREEN);
        newHeight = GetSystemMetrics(SM_CYSCREEN);


        float offsetWidth = (float)newWidth / (float)initWidth;
        float offsetHeight = (float)newHeight / (float)initHeight;


        float offset = (offsetWidth + offsetHeight) * 0.4f;

        newWidth = (int)(initWidth * offset);
        newHeight = (int)(initHeight * offset);

        // 获取当前 Unity 应用程序的进程ID
        int currentProcessId = Process.GetCurrentProcess().Id;
        // 根据进程ID获取进程对象
        Process currentProcess = Process.GetProcessById(currentProcessId);
        // 获取当前进程的主窗口句柄
        Handle = currentProcess.MainWindowHandle;

        Borderless();
    }



    void Update()
    {
#if UNITY_STANDALONE_WIN
        //当点击到名为"Frame"的UI时，方可拖动窗体
        if (IsPointerOverGameObject("Frame"))
        {
            if (Input.GetMouseButtonDown(0))
            {
                xx = 0f;
                bx = true;
            }
            if (bx && xx >= 0)
            { //这样做为了区分界面上面其它需要滑动的操作
                ReleaseCapture();
                SendMessage(Handle, 0xA1, 0x02, 0);
                SendMessage(Handle, 0x0202, 0, 0);
            }
            if (bx)
                xx += Time.deltaTime;
            if (Input.GetMouseButtonUp(0))
            {
                xx = 0f;
                bx = false;
            }
        }

#endif
    }


    /// <summary>
    /// 实现无边框
    /// </summary>
    private void Borderless()
    {
#if UNITY_STANDALONE_WIN && !UNITY_EDITOR
        Resolution[] r = Screen.resolutions;
        screenPosition = new Rect((r[r.Length - 1].width - Screen.width) / 2, (r[r.Length - 1].height - Screen.height) / 2, Screen.width, Screen.height);
        SetWindowLong(Handle, GWL_STYLE, WS_POPUP);//将网上的WS_BORDER替换成WS_POPUP  
        SetWindowPos(Handle, 0, (int)screenPosition.x, (int)screenPosition.y, initWidth, initHeight, SWP_SHOWWINDOW);
#endif
    }


    public bool IsPointerOverGameObject(string name)
    {
        bool hasItemMenu = false;
        //实例化点击事件
        PointerEventData eventDataCurrentPosition = new PointerEventData(UnityEngine.EventSystems.EventSystem.current);
        //将点击位置的屏幕坐标赋值给点击事件
        //eventDataCurrentPosition.position = new Vector2(screenPosition.x, screenPosition.y);
        eventDataCurrentPosition.position = Input.mousePosition;
        List<RaycastResult> results = new List<RaycastResult>();
        //向点击处发射射线
        EventSystem.current.RaycastAll(eventDataCurrentPosition, results);

        for (int i = 0; i < results.Count; i++)
        {
            if (results[i].gameObject.name == name)
            {
                hasItemMenu = true;
            }
        }
        return hasItemMenu;
    }

    /// <summary>
    /// 最小化窗口
    /// </summary>
    public void btn_MinClick()
    {
        ShowWindow(Handle, SW_SHOWMINIMIZED);
    }

    /// <summary>
    /// 最大化窗口
    /// </summary>
    public void btn_MaxClick()
    {
        ShowWindow(Handle, SW_SHOWMAXIMIZED);
    }

    /// <summary>
    /// 还原窗口
    /// </summary>
    public void Btn_InitWindowsClick()
    {
        ShowWindow(Handle, SW_SHOWRESTORE);
    }

}


