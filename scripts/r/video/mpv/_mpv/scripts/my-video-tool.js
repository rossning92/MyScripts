var inTime = 0.0;
var outTime = 0.0;
var historyFiles = [];
var baseName = null;
var currentFile = null;

function setClip(text) {
  mp.utils.subprocess_detached({
    args: ["powershell", "set-clipboard", '"' + text.replace("\n", "`n") + '"'],
  });
}

function getBaseName(file) {
  return file.replace(/\.[^/.]+$/, "");
}

function set_in_time() {
  inTime = mp.get_property_native("playback-time");
  if (inTime == null || inTime == "none") {
    inTime = 0;
  }

  if (inTime > outTime) {
    outTime = inTime;
  }

  showCutInfo();
}

function set_out_time() {
  outTime = mp.get_property_native("playback-time");
  if (outTime == null || outTime == "none") {
    outTime = 0;
  }

  if (outTime < inTime) {
    inTime = outTime;
  }

  showCutInfo();
}

function showCutInfo() {
  var message = "";
  message += "begin=" + inTime.toFixed(3) + "s\n";
  message += "end=" + outTime.toFixed(3) + "s\n";
  message += "duration=" + (outTime - inTime).toFixed(3) + "s\n";
  mp.osd_message(message, 3);
}

function getTimeStr() {
  function pad2(n) {
    return n < 10 ? "0" + n : n;
  }

  var date = new Date();
  timeStr =
    date.getFullYear().toString() +
    pad2(date.getMonth() + 1) +
    pad2(date.getDate()) +
    "_" +
    pad2(date.getHours()) +
    pad2(date.getMinutes()) +
    pad2(date.getSeconds());
  return timeStr;
}

function getTempFile() {
  return getTimeStr() + ".mp4";
}

function getTimestamp() {
  return Math.round(+new Date() / 1000);
}

function exportVideo(params) {
  if (isExporting) {
    mp.osd_message("<is exporting>");
    return;
  }

  if (currentFile == null) {
    currentFile = mp.get_property_native("path");
  }

  var args = ["ffmpeg"];

  // Input file
  args = args.concat(["-i", currentFile]);

  // Filters
  if (params.vf) {
    args = args.concat(["-filter:v", params.vf]);
  }

  // Pixel format
  args = args.concat(["-pix_fmt", "yuv420p"]);

  // video encoder
  if (false) {
    args = args.concat([
      "-c:v",
      "libx264",
      "-crf",
      "19",
      "-preset",
      "slow",
      "-pix_fmt",
      "yuv420p",
      "-an",
    ]);
  } else {
    args = args.concat([
      "-c:v",
      "h264_nvenc",
      "-rc:v",
      "vbr_hq",
      "-cq:v",
      "23",
      "-preset",
      "slow",
    ]);
  }

  // Audio encoder
  args = args.concat(["-c:a", "aac", "-b:a", "128k"]);

  // Output file
  if (baseName == null) baseName = getBaseName(currentFile);
  var outFile = baseName + "-" + getTimestamp() + ".mp4";
  args.push(outFile);

  mp.command_native({ name: "subprocess", args: args });
  historyFiles.push(currentFile);
  currentFile = outFile;

  // HACK: delay play exported file
  setTimeout(function () {
    mp.commandv("loadfile", outFile);
  }, 1);
}

function cut_video() {
  var filePath = mp.get_property_native("path");
  var fileName = mp.get_property_native("filename");
  var fileNameNoExt = mp.get_property_native("filename/no-ext");
  var extLen = fileName.length - fileNameNoExt.length;
  var filePathNoExt = filePath.substring(0, filePath.length - extLen);

  if (inTime == outTime) {
    mp.osd_message("error: inTime == outTime", 3);
    return;
  }

  var outFile =
    filePathNoExt +
    "-cut-" +
    inTime.toFixed(0) +
    "-" +
    outTime.toFixed(0) +
    ".mp4";

  var p = {};
  p["cancellable"] = false;
  p["args"] = [
    "ffmpeg",
    "-y",
    "-nostdin",
    "-i",
    filePath,
    "-ss",
    inTime.toFixed(3),
    "-strict",
    "-2",
    "-t",
    (outTime - inTime).toFixed(3),
    "-codec:v",
    "libx264",
    "-crf",
    "19",
    "-c:a",
    "aac",
    "-b:a",
    "128k",
    outFile,
  ];

  p["args"] = [
    "ffmpeg",
    "-ss",
    inTime.toFixed(3),
    "-i",
    filePath,
    "-t",
    (outTime - inTime).toFixed(3),
    "-c",
    "copy",
    outFile,
  ];

  var res = mp.utils.subprocess(p);
  if (res["status"] != 0) {
    var message = "Failed: status: " + res["status"];
    if (res["error"] != null) {
      message = message + ", error message: " + res["error"];
    }
    message = message + "\nstdout = " + res["stdout"];
    mp.osd_message(message, 3);
  } else {
    mp.osd_message("Done.", 3);
  }
}

mp.add_forced_key_binding("m", "copy_mouse_to_clipboard", function () {
  var mousePos = mp.get_mouse_pos();
  var osdSize = mp.get_osd_size();
  var normalizedMouseX = mousePos.x / osdSize.width;
  var normalizedMouseY = mousePos.y / osdSize.height;

  var w = mp.get_property_number("width");
  var h = mp.get_property_number("height");
  var outX = Math.floor(normalizedMouseX * w);
  var outY = Math.floor(normalizedMouseY * h);

  var s = "{{ hl(pos=(" + outX + ", " + outY + "), t='as') }}";

  mp.osd_message(s, 3);
  setClip(s);
});

mp.add_forced_key_binding("1", "resize_1080p", function () {
  mp.osd_message("resize to 1080p...");
  exportVideo({ vf: "scale=-2:1080" });
});

mp.add_forced_key_binding("7", "resize_720p", function () {
  mp.osd_message("resize to 720p...");
  exportVideo({ vf: "scale=-2:720" });
});

mp.add_forced_key_binding("2", "speed_up_2x", function () {
  exportVideo({ vf: "setpts=PTS/2" });
});

mp.add_forced_key_binding("a", "to_anamorphic", function () {
  mp.osd_message("to anamorphic...");
  exportVideo({
    vf: "scale=1920:-2,crop=1920:816:0:132,pad=1920:1080:0:132",
  });
});

mp.add_forced_key_binding("C", "crop_video", function () {
  mp.osd_message("crop video...");
  var vf = mp.get_property_native("vf");
  if (vf) {
    for (var i = 0, len = vf.length; i < len; ++i) {
      if (vf[i].name == "crop") {
        var p = vf[i].params;
        exportVideo({
          vf: "crop=" + p.w + ":" + p.h + ":" + p.x + ":" + p.y,
        });
      }
    }
  }
});

mp.add_forced_key_binding("ctrl+z", "undo", function () {
  if (historyFiles.length > 0) {
    mp.osd_message("undo");

    var lastFile = historyFiles.pop();
    mp.commandv("loadfile", lastFile);
  }
});

// mp.add_forced_key_binding("i", "set_in_time", set_in_time);
// mp.add_forced_key_binding("o", "set_out_time", set_out_time);
// mp.add_forced_key_binding("x", "cut_video", cut_video);
