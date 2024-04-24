using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;

public class KeyleKit : MonoBehaviour
{
    public Texture2D LayerImg;
    
}

[CustomEditor(typeof(KeyleKit))]
public class KeyleKitEditor : Editor
{
    KeyleKit tar = null;

    protected void OnEnable()
    {
        tar = (KeyleKit)target;
    }

    //public override bool RequiresConstantRepaint()
    //{
    //    return true;
    //}

    public override void OnInspectorGUI()
    {
        if (tar == null)
            tar = (KeyleKit)target;
        else
            return;

        
    }
}