using System;
using System.Collections.Generic;
using System.Diagnostics;

class Program {

    static string WrapArgument (string arg) {
        if (arg.Contains (" ")) {
            return "\"" + arg + "\"";
        } else {
            return arg;
        }
    }

    static int Main (string[] args) {
        List<string> arguments = new List<string> ();

        string pythonFile = System.IO.Path.Combine (AppDomain.CurrentDomain.BaseDirectory, "start_script.py");
        arguments.Add (WrapArgument (pythonFile));

        for (int i = 0; i < args.Length; i++) {
            arguments.Add (WrapArgument (args[i]));
        }

        var info = new ProcessStartInfo ("python", string.Join (" ", arguments));
        info.UseShellExecute = false;
        var proc = Process.Start (info);
        proc.WaitForExit ();
        return proc.ExitCode;
    }
}