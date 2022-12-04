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

function deleteFile(file) {
  mp.command_native({
    name: "subprocess",
    args: [
      "cmd",
      "/c",
      "del",
      '"' + file + '"', // double quote
    ],
  });
}

function createDirectory(dir) {
  mp.command_native({
    name: "subprocess",
    args: [
      "powershell",
      "New-Item",
      "-ItemType",
      "Directory",
      "-Force",
      "-Path",
      '"' + dir + '"', // double quote
      "|",
      "Out-Null",
    ],
  });
}

var tempDir = undefined;
function getTempDir() {
  if (tempDir === undefined) {
    tempDir = mp.get_property_native("path").replace(/[^\\/]+$/, "") + "tmp";
    createDirectory(tempDir);
  }
  return tempDir;
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

function getTimestamp() {
  return Math.round(+new Date() / 1000);
}

function getNewAvailableFile(file) {
  var PAD_SIZE = 1;
  var START_INDEX = 1;

  function pad(num) {
    var s = num + "";
    while (s.length < PAD_SIZE) s = "0" + s;
    return s;
  }

  var patt = /(.*?)(?:-(\d{1,2}))?\.(\w+)/g;
  var match = patt.exec(file);

  var prefix = match[1];
  // var ext = match[3];
  var ix = match[2] ? parseInt(match[2]) + 1 : START_INDEX;

  // Find new unused file name.
  var newFile;
  while (true) {
    newFile = prefix + "-" + pad(ix.toString()) + ".mp4";
    if (mp.utils.file_info(newFile)) {
      ix++;
    } else {
      break;
    }
  }

  return newFile;
}

function exportVideo(params) {
  if (currentFile == null) {
    currentFile = mp.get_property_native("path");
  }

  var args = ["ffmpeg", "-hide_banner", "-loglevel", "panic"];

  if (params.start != null) {
    if (params.noEncode) {
      args = args.concat(["-ss", params.start.toString()]);
    } else {
      var fastSeekPos = Math.max(0, params.start - 10);
      if (fastSeekPos > 0) {
        params.start = params.start - fastSeekPos;
        args = args.concat(["-ss", fastSeekPos.toString()]);
      }
    }
  }

  // Input file
  args = args.concat(["-i", currentFile]);

  if (params.start != null && !params.noEncode) {
    args = args.concat(["-ss", params.start.toString(), "-strict", "-2"]);
  }

  if (params.duration != null) {
    args = args.concat(["-t", params.duration.toString()]);
  }

  // Filters
  if (params.vf) {
    args = args.concat(["-filter:v", params.vf]);
  }

  if (params.removeAudio) {
    args = args.concat(["-c:v", "copy", "-an"]);
  } else {
    // Pixel format
    args = args.concat(["-pix_fmt", "yuv420p"]);

    if (params.noEncode) {
      // Copy instead of re-encoding
      args = args.concat(["-vcodec", "copy", "-acodec", "copy"]);
    } else {
      // Video encoding
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
    }

    // Audio encoding
    args = args.concat(["-c:a", "aac", "-b:a", "128k"]);
  }

  if (params.temp) {
    var outFile = getNewAvailableFile(currentFile);
    args.push(outFile);
    mp.msg.warning(args.toString());
    mp.command_native({ name: "subprocess", args: args });
  } else {
    mp.set_property_native("pause", true);

    var outFile = getTempDir() + "/" + getTimestamp() + ".mp4";
    args.push(outFile);

    mp.command_native({ name: "subprocess", args: args });
    historyFiles.push(currentFile);
    currentFile = outFile;

    // Avoid ffmpeg error caused by loading the file at the same time.
    setTimeout(function () {
      mp.commandv("loadfile", outFile);
      mp.set_property_native("pause", false);
    });
  }
}

var rect = [];

mp.add_forced_key_binding("m", "copy_mouse_to_clipboard", function () {
  var mousePos = mp.get_mouse_pos();
  var osdSize = mp.get_osd_size();
  var normalizedMouseX = mousePos.x / osdSize.width;
  var normalizedMouseY = mousePos.y / osdSize.height;
  var outX = normalizedMouseX * 1920;
  var outY = normalizedMouseY * 1080;

  if (rect.length == 0) {
    var s =
      "{{ hl(pos=(" +
      Math.round(outX) +
      ", " +
      Math.round(outY) +
      "), t='as') }}";
    mp.osd_message(s);
    setClip(s);
    rect.push(outX, outY);
  } else {
    var s =
      "{{ hl(rect=(" +
      Math.round(rect[0]) +
      ", " +
      Math.round(rect[1]) +
      ", " +
      Math.round(outX - rect[0]) +
      ", " +
      Math.round(outY - rect[1]) +
      "), t='as') }}";
    mp.osd_message(s);
    setClip(s);
    rect.length = 0;
  }
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

mp.add_forced_key_binding("5", "speed_up_1.5x", function () {
  mp.osd_message("speed up 1.5x...");
  exportVideo({ vf: "setpts=PTS/1.5" });
});

mp.add_forced_key_binding("h", "speed_up_0.5x", function () {
  mp.osd_message("set speed to 0.5x...");
  exportVideo({ vf: "setpts=PTS/0.5" });
});

mp.add_forced_key_binding("a", "to_anamorphic", function () {
  mp.osd_message("to anamorphic...");
  exportVideo({
    vf: "scale=1920:-2,crop=1920:816:0:132,pad=1920:1080:0:132",
  });
});

mp.add_forced_key_binding("8", "crop_1920_1080", function () {
  mp.osd_message("crop 1920x1080...");
  exportVideo({
    vf: "crop=1920:1080:0:0",
  });
});

mp.add_forced_key_binding("4", "crop_1440_810", function () {
  mp.osd_message("crop 1440x810...");
  exportVideo({
    vf: "crop=1440:810:0:0",
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

mp.add_forced_key_binding("R", "reverse", function () {
  mp.osd_message("reverse...");
  exportVideo({
    vf: "reverse",
  });
});

mp.add_forced_key_binding("T", "simulate_typing", function () {
  mp.osd_message("simulate typing...");
  exportVideo({
    vf:
      "mpdecimate" +
      ",tpad=stop_mode=clone:stop_duration=0.1" +
      ",setpts=N/FRAME_RATE/TB,setpts=2.0*PTS*(1+random(0)*0.1)",
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

mp.add_forced_key_binding("<", "crop_bottom", function () {
  mp.osd_message("crop bottom...");
  exportVideo({
    vf: "crop=0.75*iw:0.75*ih:0.125*iw:0.25*ih",
  });
});

mp.add_forced_key_binding("M", "crop_bottom_left", function () {
  mp.osd_message("crop bottom left...");
  exportVideo({
    vf: "crop=0.75*iw:0.75*ih:0:0.25*ih",
  });
});
mp.add_forced_key_binding(">", "crop_bottom_right", function () {
  mp.osd_message("crop bottom right...");
  exportVideo({
    vf: "crop=0.75*iw:0.75*ih:0.25*iw:0.25*ih",
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
  mp.osd_message("done.");
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
  mp.osd_message("done.");
  inTime = 0;
  outTime = 0;
});

mp.add_forced_key_binding("ctrl+x", "cut_video_no_encode", function () {
  mp.osd_message("cut video (no encode)...");
  exportVideo({
    start: inTime,
    duration: outTime - inTime,
    temp: true,
    noEncode: true,
  });
  inTime = 0;
  outTime = 0;
});

mp.add_forced_key_binding("s", "save_file", function () {
  var outFile = getNewAvailableFile(historyFiles[0]);
  mp.osd_message("saved as " + outFile);
  copyFile(currentFile, outFile);
});

mp.add_forced_key_binding("ctrl+s", "overwrite_file", function () {
  copyFile(currentFile, historyFiles[0]);
  mp.commandv("quit");
});

mp.add_forced_key_binding("S", "screenshot", function () {
  var outFile =
    getBaseName(mp.get_property_native("path")) + "-" + getTimestamp() + ".png";
  mp.commandv("screenshot-to-file", outFile);
  mp.osd_message("Screenshot saved.");
});

// ---

var cutPoints = [];

mp.add_forced_key_binding("t", "add_cut_point", function () {
  var t = mp.get_property_native("playback-time");
  cutPoints.push(t);

  mp.osd_message("CutPoint: " + t.toFixed(3));
});

mp.add_forced_key_binding("alt+c", "export", function () {
  var prev = 0;
  for (var i = 0; i < cutPoints.length; i++) {
    cur = cutPoints[i];
    exportVideo({ start: prev, duration: cur - prev, temp: true });
    prev = cur;
  }
  exportVideo({ start: prev, temp: true });
});
