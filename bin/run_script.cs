using System;
using System.Collections.Generic;
using System.Diagnostics;

class Program {

    static void Main (string[] args) {
        List<string> arguments = new List<string> ();

        string pythonFile = System.IO.Path.Combine (AppDomain.CurrentDomain.BaseDirectory, "run_script.py");
        arguments.Add (pythonFile);

        for (int i = 0; i < args.Length; i++) {
            arguments.Add (args[i]);
        }

        var info = new ProcessStartInfo ("python", string.Join (" ", arguments));
        info.UseShellExecute = false;
        var proc = Process.Start (info);
        proc.WaitForExit ();
    }
}