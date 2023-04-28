def vy(*args, **kwargs):
    from vy.editor import _Editor
    try:    
        return _Editor()(*args, **kwargs) 
    except SystemExit:
        pass

