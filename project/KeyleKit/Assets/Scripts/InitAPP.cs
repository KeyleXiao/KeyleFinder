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
    static extern IntPtr GetForegroundWindow();//��ȡ��ǰ��ȡ�˽���Ĵ��ھ��

    [DllImport("user32.dll")]
    public static extern bool ReleaseCapture();
    [DllImport("user32.dll")]
    public static extern bool SendMessage(IntPtr hwnd, int wMsg, int wParam, int lParam);

    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hwnd, int nCmdShow);

    [DllImport("user32.dll")]
    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

    // GetSystemMetricsʵ�ʻ�ȡ����ϵͳ��¼�ķֱ��ʣ���������ֱ��ʣ�����Ļ2560*1600����ʾ����200%�������ȡ������1280*800
    [DllImport("user32.dll", SetLastError = true)]



    private static extern int GetSystemMetrics(int nIndex);
    private static int SM_CXSCREEN = 0; //����Ļ�ֱ��ʿ��
    private static int SM_CYSCREEN = 1; //����Ļ�ֱ��ʸ߶�
    private static int SM_CYCAPTION = 4; //�������߶�
    private static int SM_CXFULLSCREEN = 16; //��󻯴��ڿ�ȣ���ȥ��������
    private static int SM_CYFULLSCREEN = 17; //��󻯴��ڸ߶ȣ���ȥ��������

    const uint SWP_SHOWWINDOW = 0x0040;
    const int GWL_STYLE = -16;
    const int WS_BORDER = 1;
    const int WS_POPUP = 0x800000;
    const int SW_SHOWMINIMIZED = 2; //{��С��, ����}
    const int SW_SHOWMAXIMIZED = 3; //{���, ����} 
    const int SW_SHOWRESTORE = 1;//��ԭ

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

        // ��Ļ�ֱ���
        newWidth = GetSystemMetrics(SM_CXSCREEN);
        newHeight = GetSystemMetrics(SM_CYSCREEN);


        float offsetWidth = (float)newWidth / (float)initWidth;
        float offsetHeight = (float)newHeight / (float)initHeight;


        float offset = (offsetWidth + offsetHeight) * 0.4f;

        newWidth = (int)(initWidth * offset);
        newHeight = (int)(initHeight * offset);

        // ��ȡ��ǰ Unity Ӧ�ó���Ľ���ID
        int currentProcessId = Process.GetCurrentProcess().Id;
        // ���ݽ���ID��ȡ���̶���
        Process currentProcess = Process.GetProcessById(currentProcessId);
        // ��ȡ��ǰ���̵������ھ��
        Handle = currentProcess.MainWindowHandle;

        Borderless();
    }



    void Update()
    {
#if UNITY_STANDALONE_WIN
        //���������Ϊ"Frame"��UIʱ�������϶�����
        if (IsPointerOverGameObject("Frame"))
        {
            if (Input.GetMouseButtonDown(0))
            {
                xx = 0f;
                bx = true;
            }
            if (bx && xx >= 0)
            { //������Ϊ�����ֽ�������������Ҫ�����Ĳ���
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
    /// ʵ���ޱ߿�
    /// </summary>
    private void Borderless()
    {
#if UNITY_STANDALONE_WIN && !UNITY_EDITOR
        Resolution[] r = Screen.resolutions;
        screenPosition = new Rect((r[r.Length - 1].width - Screen.width) / 2, (r[r.Length - 1].height - Screen.height) / 2, Screen.width, Screen.height);
        SetWindowLong(Handle, GWL_STYLE, WS_POPUP);//�����ϵ�WS_BORDER�滻��WS_POPUP  
        SetWindowPos(Handle, 0, (int)screenPosition.x, (int)screenPosition.y, initWidth, initHeight, SWP_SHOWWINDOW);
#endif
    }


    public bool IsPointerOverGameObject(string name)
    {
        bool hasItemMenu = false;
        //ʵ��������¼�
        PointerEventData eventDataCurrentPosition = new PointerEventData(UnityEngine.EventSystems.EventSystem.current);
        //�����λ�õ���Ļ���긳ֵ������¼�
        //eventDataCurrentPosition.position = new Vector2(screenPosition.x, screenPosition.y);
        eventDataCurrentPosition.position = Input.mousePosition;
        List<RaycastResult> results = new List<RaycastResult>();
        //��������������
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
    /// ��С������
    /// </summary>
    public void btn_MinClick()
    {
        ShowWindow(Handle, SW_SHOWMINIMIZED);
    }

    /// <summary>
    /// ��󻯴���
    /// </summary>
    public void btn_MaxClick()
    {
        ShowWindow(Handle, SW_SHOWMAXIMIZED);
    }

    /// <summary>
    /// ��ԭ����
    /// </summary>
    public void Btn_InitWindowsClick()
    {
        ShowWindow(Handle, SW_SHOWRESTORE);
    }

}


