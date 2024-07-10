from vy.utils import Cancel
from threading import Thread

class Completer:
    def __init__(self, buffer):
        self.buff = buffer
        self.selected = -1
        self.completion = []
        self.prefix_len = 0
        
        self._async = Cancel()    
        self._last = (0,0)
        self.last_version = None
        
        Thread(target=self.generate, args=(),daemon=True).start()
        
    @property
    def is_active(self):
        return self._async.task_done and self.completion and self.selected != -1
               
    def generate(self):
        while True:     
            self._async.notify_working()
            (lin, col), version = self.buff.cursor_lin_col, self.buff.string
            if self.last_version is not version:
                self.last_version = version
            
            result, prefix = self.buff.auto_complete()
            if result:
                self.completion, self.prefix_len = result, prefix
                self.selected = -1
            
            self._async.notify_task_done()
            self.selected = -1
            self.completion = []
            self.prefix_len = 0
                
    def get_raw_screen(self):
        if self.buff._cursor_lin_col != self._last:
            self._last = self.buff.cursor_lin_col
            self._async.restart_work()
        if self._async.task_done:
            return self.completion, self.selected
        return [], -1
        
    def move_cursor_up(self):
        if self.selected > 0:
            self.selected -= 1
        else:
            self.selected = len(self.completion) - 1

    def move_cursor_down(self):
        if self.selected == len(self.completion) - 1:
            self.selected = 0
        else:
            self.selected += 1

    def select_item(self):
        if self.is_active:
            return self.completion[self.selected], self.prefix_len
        return '', 0

