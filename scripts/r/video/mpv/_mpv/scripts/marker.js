var in_time = 0.0;
var out_time = 0.0;

function set_clipboard(text) {
  mp.utils.subprocess_detached({
    args: ["powershell", "set-clipboard", '"' + text.replace("\n", "`n") + '"'],
  });
}

function add_marker() {
  var time_pos = mp.get_property_number("time-pos");
  var mouse_pos = mp.get_mouse_pos();
  var s = "{{ hl(pos=(" + mouse_pos.x + ", " + mouse_pos.y + "), t='as') }}";

  mp.osd_message(s, 3);
  set_clipboard(s);
}

function set_in_time() {
  in_time = mp.get_property_native("playback-time");
  if (in_time == null || in_time == "none") {
    in_time = 0;
  }

  if (in_time > out_time) {
    out_time = in_time;
  }

  show_cut_info();
}

function set_out_time() {
  out_time = mp.get_property_native("playback-time");
  if (out_time == null || out_time == "none") {
    out_time = 0;
  }

  if (out_time < in_time) {
    in_time = out_time;
  }

  show_cut_info();
}

function show_cut_info() {
  var message = "";
  message += "begin=" + in_time.toFixed(3) + "s\n";
  message += "end=" + out_time.toFixed(3) + "s\n";
  message += "duration=" + (out_time - in_time).toFixed(3) + "s\n";
  mp.osd_message(message, 3);
}

function cut_video() {
  var filePath = mp.get_property_native("path");
  var fileName = mp.get_property_native("filename");
  var fileNameNoExt = mp.get_property_native("filename/no-ext");
  var extLen = fileName.length - fileNameNoExt.length;
  var filePathNoExt = filePath.substring(0, filePath.length - extLen);

  if (in_time == out_time) {
    mp.osd_message("error: in_time == out_time", 3);
    return;
  }

  var p = {};
  p["cancellable"] = false;
  p["args"] = [
    "ffmpeg",
    "-y",
    "-nostdin",
    "-i",
    filePath,
    "-ss",
    in_time.toFixed(3),
    "-strict",
    "-2",
    "-t",
    (out_time - in_time).toFixed(3),
    "-codec:v",
    "libx264",
    "-crf",
    "19",
    "-c:a",
    "aac",
    "-b:a",
    "128k",
    filePathNoExt +
      "-cut-" +
      in_time.toFixed(3) +
      "-" +
      out_time.toFixed(3) +
      ".mp4",
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

mp.add_forced_key_binding("i", "set_in_time", set_in_time);
mp.add_forced_key_binding("o", "set_out_time", set_out_time);
mp.add_forced_key_binding("m", "add_marker", add_marker);
mp.add_forced_key_binding("x", "cut_video", cut_video);
