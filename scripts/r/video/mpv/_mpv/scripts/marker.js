function set_clipboard(text) {
  mp.utils.subprocess_detached({
    args: ["powershell", "set-clipboard", '"' + text.replace("\n", "`n") + '"'],
  });
}

function add_marker() {
  var time_pos = mp.get_property_number("time-pos");
  var mouse_pos = mp.get_mouse_pos();
  var s = "{{ hl(pos=(" + mouse_pos.x + ", " + mouse_pos.y + "), t='as') }}";

  mp.osd_message(s, 1);
  set_clipboard(s);
}

mp.add_forced_key_binding("m", "add_marker", add_marker);
