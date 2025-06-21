import sys
from utils.window import activate_window_by_name

success = activate_window_by_name(sys.argv[1])
sys.exit(0 if success else 1)
