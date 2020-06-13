var out = "";

function set_clipboard(text) {
  mp.utils.subprocess_detached({
    args: ["powershell", "set-clipboard", '"' + text.replace("\n", "`n") + '"'],
  });
}

function add_marker() {
  var time_pos = mp.get_property_number("time-pos");
  var mouse_pos = mp.get_mouse_pos();
  var s =
    "{{ hl(pos=(" +
    mouse_pos.x +
    ", " +
    mouse_pos.y +
    "), t='as+" +
    time_pos.toFixed(3) +
    "') }}";

  out += s + "\n";

  mp.osd_message(out, 1);
  set_clipboard(out);
}

mp.add_forced_key_binding("m", "add_marker", add_marker);
