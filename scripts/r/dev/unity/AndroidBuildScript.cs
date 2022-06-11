using UnityEngine;
using UnityEditor;
using System;

public class BuildScript
{
    public static void BuildAndroid()
    {
        string[] levels = new string[EditorBuildSettings.scenes.Length];

        for (int i = 0; i < EditorBuildSettings.scenes.Length; i++)
        {
            levels[i] = EditorBuildSettings.scenes[i].path;
        }

        string outApk = Environment.GetEnvironmentVariable("UNITY_OUTPUT_APK");
        Debug.Assert(!string.IsNullOrEmpty(outApk));

        BuildPipeline.BuildPlayer(levels, outApk, BuildTarget.Android, BuildOptions.None);
    }
}
