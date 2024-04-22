using UnityEngine;
using System;
using System.Runtime.InteropServices;
using UnityEngine.EventSystems;
using System.Collections.Generic;
//using Python.Runtime;
//using UnityEditor.Scripting.Python;

public class InitAPP : MonoBehaviour
{
    public TextMesh text;
    private void Start()
    {
        //PythonRunner.EnsureInitialized();
        //using (Py.GIL())
        //{
        //    try
        //    {
        //        dynamic sys = Py.Import("sys");
        //        UnityEngine.Debug.Log($"python version: {sys.version}");
        //    }
        //    catch (PythonException e)
        //    {
        //        UnityEngine.Debug.LogException(e);
        //    }
        //}
    }
}


//using System;
//using Python.Runtime;

//internal sealed class Program
//{
//    private static void Main(string[] args)
//    {
//        // NOTE: set this based on your python install. this will resolve from
//        // your PATH environment variable as well.
//        Runtime.PythonDLL = "python310.dll";

//        PythonEngine.Initialize();
//        using (Py.GIL())
//        {
//            // NOTE: this doesn't validate input
//            Console.WriteLine("Enter first integer:");
//            var firstInt = int.Parse(Console.ReadLine());

//            Console.WriteLine("Enter second integer:");
//            var secondInt = int.Parse(Console.ReadLine());

//            using dynamic scope = Py.CreateScope();
//            scope.Exec("def add(a, b): return a + b");
//            var sum = scope.add(firstInt, secondInt);
//            Console.WriteLine($"Sum: {sum}");
//        }
//    }
//}