from vy.editor import _Editor
_Editor = _Editor()

def vy(*args, **kwargs):
    global _Editor
    try:    
        return _Editor(*args, **kwargs) 
    except SystemExit:
        pass

