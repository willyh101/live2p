from termcolor import cprint
import threading

lock = threading.Lock()

class Alert:
    alerts = {
        'none': '*',
        'info': '[INFO]',
        'warn': '[WARNING]',
        'error': '[ERROR]',
        'success': '[INFO]'
    }
    
    colors = {
        'none': 'white',
        'info': 'yellow',
        'warn': 'yellow',
        'error': 'red',
        'success': 'green'
    }
    
    def __init__(self, message, level='none'):
        """
        Prints out colored alert messages.
        
        Level       Header       Color
        =====       ======       =====
        'none'      *            white
        'info'      [INFO]       yellow
        'warn'      [WARN]       yellow
        'error'     [ERROR]      red
        'success'   [INFO]       green

        Args:
            message (str): Message to print.
            level (str, optional): Specified alert level. Defaults to 'none'.
        """
        self.message = message
        self.level = level
        self.color = self.colors[self.level]
        
        out = self.format()
        self.show(out)
    
    def format(self):
        return f'{self.alerts[self.level]} {self.message}'
    
    def show(self, output):
        with lock:
            cprint(output, self.color)