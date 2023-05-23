"""
    *********************************
    ****    Line-Wise Edition    ****
    *********************************

Linewise actions are actions that require a positive non-zero {count} of lines
to operate on (defaulting to 1).  Even if it is never an error to give them a
{register} argument, most of them will just ignore it.

"""
from vy.actions.helpers import sa_commands as _sa_commands
from vy import keys as k

@_sa_commands('# v_# :comment')
def comment_current_line(editor, reg=None, part=None, arg=None, count=1):
    """
    Comment the current line.  If the current buffer has no
    .set_comment_string attribute set, this does nothing.
    """
    if any((token := editor.current_buffer.set_comment_string)):
        with editor.current_buffer as curbuf:
            before, after = token
            for index in range(count):
                curlin = curbuf.current_line
                if not curlin.lstrip().startswith(before):
                    curbuf.current_line = before + curlin[:-1] + after + '\n'
#                if index != count - 1:
#                    curbuf.move_cursor('j')

@_sa_commands(f'>> v_> :indent i_{k.C_T}')
def indent_current_line(editor, reg=None, part=None, arg=None, count=1):
    """
    Indent the current line.
    """
    with editor.current_buffer as curbuf:
        last_line = curbuf.number_of_lin
        last_target = curbuf.current_line_idx + count
        max_line = min(last_line, last_target)
        indent = curbuf.set_tabsize * ' '
        curbuf.move_cursor('_')
        for idx in range(curbuf.current_line_idx, max_line):
            cur_lin = curbuf.current_line
            curbuf.current_line = indent + cur_lin
            if idx != max_line - 1:
                curbuf.move_cursor('j')

@_sa_commands(f'<< v_< :dedent i_{k.C_D}')
def dedent_current_line(editor, reg=None, part=None, arg=None, count=1):
    """
    Dedent the current line.
    """
    
    with editor.current_buffer as cur_buf:
        last_line = cur_buf.number_of_lin
        last_target = cur_buf.current_line_idx + count
        max_line = min(last_line, last_target)
        indent = cur_buf.set_tabsize * ' '
        for idx in range(cur_buf.current_line_idx, max_line):
            cur_lin = cur_buf.current_line
            
            if cur_lin.startswith(indent):
               new_line = cur_lin.removeprefix(indent)
            elif cur_lin.startswith('\t'):
                new_line = cur_lin.removeprefix('\t')
            elif cur_lin.startswith(' '):
                new_line = cur_lin.lstrip()
                
            delta = len(cur_lin) - len(new_line)    
            curbuf.current_line = new_line
            curbuf.cursor -= delta
            
            if idx != max_line - 1:
                cur_buf.move_cursor('j')
        
        
@_sa_commands('gq v_gq')
def format_line(editor, reg=None, count=1, **kwargs):
    """
    Format line.
    """
    from textwrap import TextWrapper
    cur_buf = editor.current_buffer
    cur_lin = cur_buf.current_line
    stripped_line = cur_lin.lstrip()
#    if any(curbuf.set_comment_string) \
#       and stripped_line.startswith(curbuf.set_comment_string[0]):
#       pass
    to_strip_len = len(cur_lin) - len(stripped_line)
    initial_indent = cur_lin[:to_strip_len]
    wrapper = TextWrapper(width=72,
                            initial_indent='',
                            subsequent_indent=initial_indent,
                            expand_tabs=cur_buf.set_expandtabs,
                            fix_sentence_endings=True,
                            tabsize=cur_buf.set_tabsize,
                            drop_whitespace=True,
                            replace_whitespace=True,
                            ).wrap
    
    from_lin = cur_buf.lines_offsets[cur_buf.current_line_idx]
    try:
        to_lin = cur_buf.lines_offsets[cur_buf.current_line_idx+count] - 1
    except IndexError:
        to_lin = len(cur_buf)
        
    target = slice(from_lin, to_lin)
    cur_buf[target] = '\n'.join(wrapper(cur_buf.string[target]))
    
@_sa_commands('# v_# :comment')
def comment_current_line(editor, reg=None, part=None, arg=None, count=1):
    """
    Comment the current line.  If the current buffer has no .set_comment_string
    attribute set, does nothing.
    """
    if any((token := editor.current_buffer.set_comment_string)):
        with editor.current_buffer as curbuf:
            before, after = token
            for index in range(count):
                curlin = curbuf.current_line
                if not curlin.lstrip().startswith(before):
                    curbuf.current_line = before + curlin[:-1] + after + '\n'
                if index != count - 1:
                    curbuf.move_cursor('j')

@_sa_commands(f'>> v_> :indent i_{k.C_T}')
def indent_current_line(editor, reg=None, part=None, arg=None, count=1):
    """
    Indent the current line.
    """
    with editor.current_buffer as curbuf:
        last_line = curbuf.number_of_lin
        last_target = curbuf.current_line_idx + count
        max_line = min(last_line, last_target)
        indent = curbuf.set_tabsize * ' '
        curbuf.move_cursor('_')
        for idx in range(curbuf.current_line_idx, max_line):
            cur_lin = curbuf.current_line
            curbuf.current_line = indent + cur_lin
            if idx != max_line - 1:
                curbuf.move_cursor('j')

@_sa_commands(f'<< v_< :dedent i_{k.C_D}')
def dedent_current_line(editor, reg=None, part=None, arg=None, count=1):
    """
    Dedent the current line.
    """
    with editor.current_buffer as cur_buf:
        indent = cur_buf.set_tabsize * ' '
        last_line = cur_buf.number_of_lin
        last_target = cur_buf.current_line_idx + count
        max_line = min(last_line, last_target)
        indent = cur_buf.set_tabsize * ' '
        cur_buf.move_cursor('_')
        for idx in range(cur_buf.current_line_idx, max_line):
            cur_lin = cur_buf.current_line
            if cur_lin.startswith(indent):
                cur_buf.current_line = cur_lin.removeprefix(indent)
            elif cur_lin.startswith('\t'):
                cur_buf.current_line = cur_lin.removeprefix('\t')
            elif cur_lin.startswith(' '):
                cur_buf.current_line = cur_lin.lstrip() or '\n'
            if idx != max_line - 1:
                cur_buf.move_cursor('j')
        cur_buf.move_cursor('_')
        
@_sa_commands('J v_J')
def join_lines(editor, reg=None, part=None, arg=None, count=1):
    """
    Joins the {count} next lines together.
    """
    with editor.current_buffer as curbuf:
        for _ in range(count):
            lin, col = curbuf.cursor_lin_col
            if lin + 1 == curbuf.number_of_lin:
                return
            curbuf.current_line = curbuf.current_line.rstrip() + ' \n'
            curbuf.cursor_lin_col = lin+1, 0
            curbuf.current_line = curbuf.current_line.lstrip(' ')
            curbuf.cursor_lin_col = lin, col
            curbuf.join_line_with_next()

