from _scriptserver import start_server
from _shutil import setup_logger

if __name__ == "__main__":
    setup_logger()
    start_server(port=8888)
