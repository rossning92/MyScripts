var nvenc = true;

var historyFiles = [];
var baseName = null;
var currentFile = null;

var inTime = 0;
var outTime = 0;

function setClip(text) {
  mp.utils.subprocess_detached({
    args: ["powershell", "set-clipboard", '"' + text.replace("\n", "`n") + '"'],
  });
}

function copyFile(src, dst) {
  mp.command_native({
    name: "subprocess",
    args: [
      "powershell",
      "Copy-Item",
      '"' + src + '"', // double quote
      "-Destination",
      '"' + dst + '"', // double quote
    ],
  });
}

function getBaseName(file) {
  return file.replace(/\.[^/.]+$/, "");
}

function setCutPoint(isInTime) {
  cur = mp.get_property_native("playback-time");
  if (!outTime) {
    outTime = mp.get_property_native("duration");
  }

  if (isInTime) {
    inTime = cur;
  } else {
    outTime = cur;
  }

  if (inTime > outTime) {
    outTime = inTime;
  }

  mp.osd_message("[" + inTime.toFixed(3) + ", " + outTime.toFixed(3) + "]");
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
  if (currentFile == null) {
    currentFile = mp.get_property_native("path");
  }

  var args = ["ffmpeg", "-hide_banner", "-loglevel", "panic"];

  if (params.start != null && params.fastSeek) {
    args = args.concat(["-ss", params.start.toString()]);
  }

  // Input file
  args = args.concat(["-i", currentFile]);

  if (params.start != null && !params.fastSeek) {
    args = args.concat(["-ss", params.start.toString(), "-strict", "-2"]);
  }

  if (params.start != null) {
    args = args.concat(["-t", params.duration.toString()]);
  }

  // Filters
  if (params.vf) {
    args = args.concat(["-filter:v", params.vf]);
  }

  if (params.removeAudio) {
    args = args.concat(["-c:v", "copy", "-an"]);
  } else {
    // Video encoding

    // Pixel format
    args = args.concat(["-pix_fmt", "yuv420p"]);

    if (nvenc) {
      args = args.concat([
        "-c:v",
        "h264_nvenc",
        "-preset",
        "hq",
        "-rc:v",
        "vbr_hq",
        "-qmin",
        "17",
        "-qmax",
        "21",
      ]);
    } else {
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
    }

    // Audio encoding
    args = args.concat(["-c:a", "aac", "-b:a", "128k"]);
  }

  // Output file
  if (baseName == null) baseName = getBaseName(currentFile);

  if (params.temp) {
    var outFile = getBaseName(currentFile) + "-" + getTimestamp() + ".mp4";
    args.push(outFile);
    mp.utils.subprocess_detached({
      args: args,
    });
  } else {
    mp.set_property_native("pause", true);

    var outFile = "/tmp/" + getTimestamp() + ".mp4";
    args.push(outFile);

    mp.command_native({ name: "subprocess", args: args });
    historyFiles.push(currentFile);
    currentFile = outFile;

    // Avoid ffmpeg error caused by loading the file at the same time..
    setTimeout(function () {
      mp.commandv("loadfile", outFile);
      mp.set_property_native("pause", false);
    });
  }
}

mp.add_forced_key_binding("m", "copy_mouse_to_clipboard", function () {
  var mousePos = mp.get_mouse_pos();
  var osdSize = mp.get_osd_size();
  var normalizedMouseX = mousePos.x / osdSize.width;
  var normalizedMouseY = mousePos.y / osdSize.height;

  var w = mp.get_property_number("width");
  var h = mp.get_property_number("height");
  var outX = Math.floor(normalizedMouseX * 1920);
  var outY = Math.floor(normalizedMouseY * 1080);

  var s = "{{ hl(pos=(" + outX + ", " + outY + "), t='as') }}";

  mp.osd_message(s);
  setClip(s);
});

mp.add_forced_key_binding("1", "resize_1080p", function () {
  mp.osd_message("resize to 1080p...");
  // exportVideo({ vf: "scale=-2:1080" });
  exportVideo({ vf: "scale=1920:-2" });
});

mp.add_forced_key_binding("7", "resize_720p", function () {
  mp.osd_message("resize to 720p...");
  exportVideo({ vf: "scale=-2:720" });
});

mp.add_forced_key_binding("2", "speed_up_2x", function () {
  mp.osd_message("speed up 2x...");
  exportVideo({ vf: "setpts=PTS/2" });
});

mp.add_forced_key_binding("a", "to_anamorphic", function () {
  mp.osd_message("to anamorphic...");
  exportVideo({
    vf: "scale=1920:-2,crop=1920:816:0:132,pad=1920:1080:0:132",
  });
});

mp.add_forced_key_binding("8", "crop_top_left_1080p", function () {
  mp.osd_message("crop top left 1080p...");
  exportVideo({
    vf: "crop=1920:1080:0:0",
  });
});

mp.add_forced_key_binding("5", "crop_out_taskbar", function () {
  mp.osd_message("Crop out taskbar...");
  exportVideo({
    vf: "crop=2560:1378:0:0,scale=1920:-2",
  });
});

mp.add_forced_key_binding("K", "crop_center", function () {
  mp.osd_message("crop center...");
  exportVideo({
    vf: "crop=0.75*iw:0.75*ih:0.125*iw:0.125*ih",
  });
});

mp.add_forced_key_binding("U", "crop_top_left", function () {
  mp.osd_message("crop top left...");
  exportVideo({
    vf: "crop=0.75*iw:0.75*ih:0:0",
  });
});

mp.add_forced_key_binding("J", "crop_left", function () {
  exportVideo({
    vf: "crop=0.75*iw:0.75*ih:0:0.125*ih",
  });
});

mp.add_forced_key_binding("L", "crop_right", function () {
  exportVideo({
    vf: "crop=0.75*iw:0.75*ih:0.25*iw:0.125*ih",
  });
});

mp.add_forced_key_binding("O", "crop_top_right", function () {
  mp.osd_message("crop top right...");
  exportVideo({
    vf: "crop=0.75*iw:0.75*ih:0.25*iw:0",
  });
});

mp.add_forced_key_binding(">", "crop_bottom_right", function () {
  mp.osd_message("crop bottom right...");
  exportVideo({
    vf: "crop=0.75*iw:0.75*ih:0.25*iw:0.21*ih",
  });
});

mp.add_forced_key_binding("I", "crop_top", function () {
  mp.osd_message("crop top...");
  exportVideo({
    vf: "crop=0.75*iw:0.75*ih:0.125*iw:0",
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

    currentFile = historyFiles.pop();
    mp.commandv("loadfile", currentFile);
  }
});

mp.add_forced_key_binding("[", "set_in_time", function () {
  setCutPoint(true);
});

mp.add_forced_key_binding("]", "set_out_time", function () {
  setCutPoint(false);
});

mp.add_forced_key_binding("x", "cut_video", function () {
  mp.osd_message("cut video...");
  exportVideo({ start: inTime, duration: outTime - inTime });
  inTime = 0;
  outTime = 0;
});

mp.add_forced_key_binding("A", "remove_audio", function () {
  mp.osd_message("remove audio...");
  exportVideo({ removeAudio: true });
});

mp.add_forced_key_binding("X", "cut_video_background", function () {
  mp.osd_message("cut video (temp)...");
  exportVideo({ start: inTime, duration: outTime - inTime, temp: true });
  inTime = 0;
  outTime = 0;
});

mp.add_forced_key_binding("Z", "cut_video_fastseek", function () {
  mp.osd_message("cut video (fast seek)...");
  exportVideo({
    start: inTime,
    duration: outTime - inTime,
    temp: true,
    fastSeek: true,
  });
  inTime = 0;
  outTime = 0;
});

mp.add_forced_key_binding("s", "save_file", function () {
  var outFile = getBaseName(historyFiles[0]) + "-" + getTimestamp() + ".mp4";
  mp.osd_message("saved as " + outFile);
  copyFile(currentFile, outFile);
});

mp.add_forced_key_binding("ctrl+s", "overwrite_file", function () {
  copyFile(currentFile, historyFiles[0]);
  mp.commandv("quit");
});

mp.add_forced_key_binding("S", "screenshot", function () {
  mp.osd_message("save screenshot...");
  var currentFile = mp.get_property_native("path");
  var outFile = getBaseName(currentFile) + "-" + getTimestamp() + ".png";
  mp.commandv("screenshot-to-file", outFile);
});
