import threading
from api.api import api_run
from parser.parser import run


if __name__ == "__main__":
    thread = threading.Thread(target=run)
    thread.start()
    api_run()