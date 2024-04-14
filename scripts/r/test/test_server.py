from _scriptserver import ScriptServer
from utils.logger import setup_logger

if __name__ == "__main__":
    setup_logger()
    script_server = ScriptServer(port=8888)
    script_server.start_server()
    script_server.join_server_thread()
