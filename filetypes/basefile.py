class BaseFile:
    def stop_undo_record(self):
        """ NOT IMPLEMENTED """
    def start_undo_record(self):
        """ NOT IMPLEMENTED """
    def set_undo_point(self):
        """ NOT IMPLEMENTED """
    def save_as(self):
        """ NOT IMPLEMENTED """
    def save(self):
        """ NOT IMPLEMENTED """
    @property
    def unsaved(self):
        return False
    
    @property
    def string(self):
        return self._string
