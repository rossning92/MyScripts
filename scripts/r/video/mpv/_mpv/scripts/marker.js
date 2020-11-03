var inTime = 0.0;
var outTime = 0.0;
var history_files = [];

function set_clipboard(text) {
  mp.utils.subprocess_detached({
    args: ["powershell", "set-clipboard", '"' + text.replace("\n", "`n") + '"'],
  });
}

function add_marker() {
  var timePos = mp.get_property_number("time-pos");

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
  set_clipboard(s);
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

function get_temp_file() {
  function pad2(n) {
    return n < 10 ? "0" + n : n;
  }

  var date = new Date();
  var time_str =
    date.getFullYear().toString() +
    pad2(date.getMonth() + 1) +
    pad2(date.getDate()) +
    "_" +
    pad2(date.getHours()) +
    pad2(date.getMinutes()) +
    pad2(date.getSeconds());

  return time_str + ".mp4";
}

function create_filtered_video(videoFilter) {
  var outFile = get_temp_file();
  var currentFile = mp.get_property_native("filename");

  var common_args = [
    "-pix_fmt",
    "yuv420p",
    "-c:v",
    "libx264",
    "-crf",
    "19",
    "-preset",
    "slow",
    "-pix_fmt",
    "yuv420p",
    "-an",
    "-y",
  ];

  common_args = [
    "-pix_fmt",
    "yuv420p",
    "-c:v",
    "h264_nvenc",
    "-rc:v",
    "vbr_hq",
    "-cq:v",
    "23",
    "-preset",
    "slow",
  ];

  var args = [].concat(
    ["ffmpeg", "-i", currentFile, "-filter:v", videoFilter],
    common_args,
    [outFile]
  );
  mp.command_native_async({ name: "subprocess", args: args }, function (
    success,
    result,
    error
  ) {
    history_files.push(currentFile);
    mp.commandv("loadfile", outFile);
  });
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

// mp.add_forced_key_binding("i", "set_in_time", set_in_time);
// mp.add_forced_key_binding("o", "set_out_time", set_out_time);
mp.add_forced_key_binding("m", "add_marker", add_marker);
// mp.add_forced_key_binding("x", "cut_video", cut_video);

// history_files.push(mp.get_property_native("filename"));

mp.add_forced_key_binding("1", "yoyo", function () {
  create_filtered_video("scale=-2:1080");
});
