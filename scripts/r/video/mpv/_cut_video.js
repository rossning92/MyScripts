var in_time = 0.0;
var out_time = 0.0;

function set_in_time() {
  in_time = mp.get_property_native("playback-time");
  print_time_info();
}

function set_out_time() {
  out_time = mp.get_property_native("playback-time");
  print_time_info();
}

function print_time_info() {
  s =
    "range: " +
    in_time.toFixed(3) +
    "s - " +
    out_time.toFixed(3) +
    "s\n" +
    ("duration: " + (out_time - in_time).toFixed(3) + "s");
  mp.osd_message(s);
}

mp.add_forced_key_binding("i", "set_in_time", set_in_time);
mp.add_forced_key_binding("o", "set_out_time", set_out_time);
