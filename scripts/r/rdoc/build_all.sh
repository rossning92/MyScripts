set -e
run_script r/rdoc/clone_renderdoc.sh
run_script r/rdoc/build_renderdoc_win.cmd
run_script r/rdoc/build_renderdoc_android.sh