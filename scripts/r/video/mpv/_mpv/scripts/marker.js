var inTime = 0.0;
var outTime = 0.0;

function set_clipboard(text) {
  mp.utils.subprocess_detached({
    args: ["powershell", "set-clipboard", '"' + text.replace("\n", "`n") + '"'],
  });
}

function add_marker() {
  var timePos = mp.get_property_number("time-pos");
  var mousePos = mp.get_mouse_pos();
  var s = "{{ hl(pos=(" + mousePos.x + ", " + mousePos.y + "), t='as') }}";

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
