import pytest
from live2p.alerts import Alert

@pytest.fixture
def msg():
    return 'test_message'

@pytest.fixture
def level():
    return 'info'

@pytest.fixture
def alert(msg, level):
    return Alert(msg, level)

def test_msg(alert, msg):
    assert alert.message == msg
    
def test_level(alert, level):
    assert alert.level == level
    
def test_color(alert):
    assert alert.color == 'yellow'
    
def test_default():
    a = Alert('test message')
    assert a.color == 'white' and a.level == 'none'