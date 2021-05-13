import pytest
import threading

server_settings = {
    'ip': 'localhost',
    'port': 6000
}

@pytest.fixture
def server():
    pass
    # thread = threading.Thread(target=TestServer(**server_settings))
    # thread.daemon = True
    # thread.start()