import subprocess
import threading
import itertools
import queue
import json
import os
import time

def open_lsp_channel(server, buffer):
    try:
        return LSPClient(server, buffer)
    except FileNotFoundError:
        return None

class LSPClient:
    """
    LSPClient class for interacting with a Language Server Protocol (LSP) server.

    This class acts as a client for an LSP server, enabling communication for a comprehensive
    set of language-specific tasks as defined in the LSP specifications. It interacts with the
    server using JSON-RPC requests and processes responses accordingly.

    Parameters:
        server_command (list[str]): The command used to start the LSP server (e.g., `['pylsp']`).
        timeout (float, optional): Timeout duration in seconds for each request. Default is 2.0 seconds.
    """

    def __init__(self, server_command, target_buffer, timeout=5.0):
        self._timeout = timeout
        self._proc = subprocess.Popen(
                server_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0
        )
        self._pending_responses = {}
        self._id_gen = itertools.count(1)
        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._stderr_thread = threading.Thread(target=self._stderr_loop, daemon=True)
        self._reader_thread.start()
        self._stderr_thread.start()

        # Minimal realistic client capabilities. These can be extended depending on language server needs.
        # See https://microsoft.github.io/language-server-protocol/specifications/specification-current/#clientCapabilities
        capabilities = {
            "workspace": {
                "workspaceFolders": {"supported": False, "changeNotifications": False}
                
            },
            "textDocument": {
                "synchronization": {"openClose": True, "save": {"includeText": True}, "change": 2},
                "hover": {},
                "definition": {},
                "references": {},
                "rename": {},
                "completion": {},
                "documentSymbol": {},
                "documentHighlight": {},
                "foldingRange": {},
                "documentFormatting": {},
                "documentRangeFormatting": {},
                "codeLens": {},
                "codeAction": {},
                "signatureHelp": {}
            },
            "experimental": {}
        }
        capabilities = {
            "textDocument": {
                "completion": {
                    "completionItem": {
                        "snippetSupport": False
                    },
                    "completionItemKind": {
                        "valueSet": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]
                    },
                    "contextSupport": True
                }
            }
        }
#        capabilities = {}
        # Process ID for the client, required by LSP spec
        process_id = os.getpid()

        # The root URI of the workspace. Set this to the root directory of your project.
        # Use "file:///" if no project directory is available.
        
        root_uri = "file://" + (str(target_buffer.path.parent) if target_buffer.path else '/')
        
        # Initialize and send the 'initialized' notification immediately after
        self.initialize(process_id=process_id, root_uri=root_uri, capabilities=capabilities)
        self.initialized()

    def __bool__(self):
        """
        Determine the boolean value of the LSPClient instance.
        
        Returns:
            bool: Always returns True to indicate an active client.
        """
        return True

    def _stderr_loop(self):
        """
        Internal method for continuously reading stderr from the LSP server process.
        
        This method runs in a separate thread and logs all stderr output to a file.
        """
        while True:
            line = self._proc.stderr.readline().decode("utf-8")
            if line:
                with open('stderr_from_lsp.log', 'a+') as out:
                    out.write("[STDERR] " + line)
                    out.flush()

    def _send_request(self, method, params):
        """
        Internal method to send a JSON-RPC request to the LSP server.

        Parameters:
            method (str): The LSP method to call.
            params (dict or None): Parameters to pass to the method.

        Returns:
            dict: The server's response.

        Raises:
            TimeoutError: If no response is received within the timeout period.
        """
        request_id = str(next(self._id_gen))

        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }

        response_queue = queue.Queue()
        self._pending_responses[request_id] = response_queue

        message = json.dumps(request).encode("utf-8")
        payload = b"Content-Length: %d\r\n\r\n" % len(message) + message
        self._proc.stdin.write(payload)
        self._proc.stdin.flush()

        with open('stdin_from_lsp.log', 'a') as out:
            out.write(f"--> Request: {method}\n")
            out.write(message.decode('utf-8') + "\n")
            out.flush()

        try:
            response = response_queue.get(timeout=self._timeout)
            return response
        except queue.Empty:
            raise TimeoutError(f"No response for request {method} within {self._timeout}s")
        finally:
            del self._pending_responses[request_id]

    def _send_notification(self, method, params):
        """
        Internal method to send a JSON-RPC notification to the LSP server.
        
        Notifications are one-way messages that do not expect a response.

        Parameters:
            method (str): The LSP method to call.
            params (dict): Parameters to pass to the method.
        """
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        message = json.dumps(notification).encode('utf-8')
        payload = (
            b"Content-Length: "
            + str(len(message)).encode('utf-8')
            + b"\r\n\r\n"
            + message
        )

        with open('stdin_from_lsp.log', 'a') as out:
            out.write(f"--> Notification: {method}\n")
            out.write(message.decode('utf-8') + "\n")
            out.flush()

        self._proc.stdin.write(payload)
        self._proc.stdin.flush()

    def _read_loop(self):
        """
        Internal method for continuously reading responses from the LSP server process.
        
        This method runs in a separate thread and processes incoming JSON-RPC messages.
        """
        while True:
            headers = {}
            while True:
                line = self._proc.stdout.readline().decode('utf-8')
                with open('stdout_from_lsp.log', 'a+') as out:
                    out.write("<-- Header: " + line)
                    out.flush()
                if not line.strip():
                    break
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()
    
            content_length = int(headers.get("Content-Length", 0))
            if content_length:
                content = self._proc.stdout.read(content_length).decode("utf-8")
                with open('stdout_from_lsp.log', 'a+') as out:
                    out.write("<-- Content: " + content + "\n")
                    out.flush()
                
                try:
                    response = json.loads(content)
                    
                    # Handle response to a request
                    if "id" in response:
                        response_id = str(response["id"])
                        if response_id in self._pending_responses:
                            self._pending_responses[response_id].put(response)
                        else:
                            with open('read_from_lsp.log', 'a') as out:
                                out.write(f"Received response for unknown id: {response_id}\n")
                                out.flush()
                    # Handle server notifications (no id)
                    elif "method" in response:
                        with open('read_from_lsp.log', 'a') as out:
                            out.write(f"Received notification: {response['method']}\n")
                            out.flush()
                except json.JSONDecodeError as e:
                    with open('read_from_lsp.log', 'a') as out:
                        out.write(f"Error decoding JSON: {e}, content: {repr(content)}\n")
                        out.flush()    

    def _read_exactly(self, stream, n):
        """
        Cross-platform blocking read of exactly `n` bytes, with timeout.
        
        Parameters:
            stream (file-like object): The stream to read from.
            n (int): Number of bytes to read.
            
        Returns:
            str: The decoded content.
            
        Raises:
            TimeoutError: If reading times out.
        """
        deadline = time.monotonic() + self._timeout
        data = b''  # Use bytes instead of str
        while len(data) < n:
            if time.monotonic() > deadline:
                raise TimeoutError(f"Timeout while reading {n} bytes (got {len(data)})")
            chunk = stream.read(n - len(data))
            if not chunk:
                time.sleep(0.01)
                continue
            data += chunk
        return data.decode('utf-8')

    def initialize(self, process_id: int, root_uri: str, capabilities: dict):
        """
        Sends an 'initialize' request to the LSP server.

        Parameters:
            process_id (int): The process ID of the client.
            root_uri (str): Root URI of the workspace.
            capabilities (dict): Client capabilities.
            
        Returns:
            dict: Server response containing server capabilities.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#initialize
        """
        params = {
            "processId": process_id,
            "rootUri": root_uri,
            "rootPath": '/',
            "capabilities": capabilities,
        }
        return self._send_request("initialize", params)

    def initialized(self):
        """
        Sends an 'initialized' notification after initialize completes.
    
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#initialized
        """
        self._send_notification("initialized", {})

    def shutdown(self):
        """
        Sends a 'shutdown' request to the server.
        
        Returns:
            dict: Server response, typically null.

        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#shutdown
        """
        return self._send_request("shutdown", None)

    def exit(self):
        """
        Sends an 'exit' notification to the server.

        This notification asks the server to exit its process.

        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#exit
        """
        notification = {
            "jsonrpc": "2.0",
            "method": "exit",
            "params": {}
        }
        message = json.dumps(notification).encode('utf-8')
        payload = f"Content-Length: {len(message)}\r\n\r\n".encode('utf-8') + message
        self._proc.stdin.write(payload)
        self._proc.stdin.flush()
    
    def text_document_did_open(self, uri: str, language_id: str, version: int, text: str):
        """
        Notifies the server that a text document has been opened.
        
        Parameters:
            uri (str): The document's URI.
            language_id (str): The document's language identifier.
            version (int): The document's version number.
            text (str): The document's full content.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_didOpen
        """
        text_document = {
            "uri": uri,
            "languageId": language_id,
            "version": version,
            "text": text
        }
        self._send_notification("textDocument/didOpen", {
            "textDocument": text_document
        })

    def text_document_did_change(self, uri: str, version: int, content_changes: list):
        """
        Notifies the server that a text document has changed.
        
        Parameters:
            uri (str): The document's URI.
            version (int): The document's version number.
            content_changes (list): List of text document content changes.
                Each change should be a dict with either 'text' (full content) or
                'range', 'rangeLength', and 'text' for incremental updates.
                
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_didChange
        """
        text_document = {
            "uri": uri,
            "version": version
        }
        self._send_notification("textDocument/didChange", {
            "textDocument": text_document,
            "contentChanges": content_changes
        })

    def text_document_did_save(self, uri: str, text: str = None):
        """
        Notifies the server that a text document has been saved.
        
        Parameters:
            uri (str): The document's URI.
            text (str, optional): The document's content that was saved.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_didSave
        """
        text_document = {"uri": uri}
        params = {"textDocument": text_document}
        if text is not None:
            params["text"] = text
        self._send_notification("textDocument/didSave", params)

    def text_document_did_close(self, uri: str):
        """
        Notifies the server that a text document has been closed.
        
        Parameters:
            uri (str): The document's URI.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_didClose
        """
        text_document = {"uri": uri}
        self._send_notification("textDocument/didClose", {
            "textDocument": text_document
        })

    def text_document_hover(self, uri: str, line: int, character: int):
        """
        Requests hover information at a given text document position.
        
        Parameters:
            uri (str): The document's URI.
            line (int): The line position (zero-based).
            character (int): The character position (zero-based).
            
        Returns:
            dict: Hover information or null.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_hover
        """
        text_document = {"uri": uri}
        position = {"line": line, "character": character}
        return self._send_request("textDocument/hover", {
            "textDocument": text_document,
            "position": position
        })

    def text_document_completion(self, 
                                 uri: str,
                                 document_text: str,
                                 line: int, 
                                 character: int, 
                                 trigger_kind: int = None, 
                                 trigger_character: str = None):
        """
        Requests completion items at a given text document position.
        
        Parameters:
            uri (str): The document's URI.
            line (int): The line position (zero-based).
            character (int): The character position (zero-based).
            trigger_kind (int, optional): The completion trigger kind.
                1 = Invoked, 2 = TriggerCharacter, 3 = TriggerForIncompleteCompletions
            trigger_character (str, optional): The trigger character if trigger_kind is 2.
            
        Returns:
            tuple: (prefix_length, [completion_items]) where prefix_length is the number
                   of characters to delete and completion_items is a list of strings.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_completion
        """
        text_document = {"uri": uri}
        position = {"line": line, "character": character}
        context = {}
        if trigger_kind is not None:
            context["triggerKind"] = trigger_kind
        if trigger_character is not None:
            context["triggerCharacter"] = trigger_character
            
        lsp_response = self._send_request("textDocument/completion", {
            "textDocument": text_document,
            "position": position,
            "context": context
        })
        
        # Default to empty results if there's an issue
        if not lsp_response or 'result' not in lsp_response or 'items' not in lsp_response['result']:
            return [], 0
            
        
        completion_items = lsp_response['result']['items']
        if not completion_items:
            return [], 0
        
        # Extract the completion texts
        completions = []
        for item in completion_items:
            # Use insertText if available, otherwise use label
            text = item.get('insertText', item.get('label', ''))
            # If it's a function, keep just the name part
            if '(' in text and ')' in text:
                text = text.split('(', 1)[0]
            completions.append(text)
        
        # Calculate prefix length by analyzing document content

        lines = document_text.split('\n')
        if 0 <= line < len(lines):
            current_line = lines[line]
            prefix = current_line[:character]
            
            # Find the last word boundary 
            for i in range(len(prefix) - 1, -1, -1):
                if not prefix[i].isalnum() and prefix[i] != '_':
                    break
            else:
                i = -1
            
            current_word = prefix[i+1:]
            prefix_length = len(current_word)
            
            # Check if any completion matches the current word
            for completion in completions:
                if completion.lower().startswith(current_word.lower()):
                    return completions, prefix_length
        
        # Fallback to 0 if we couldn't determine it
        return completions, 0

    def text_document_definition(self, uri: str, line: int, character: int):
        """
        Requests the definition location for a symbol at a given text document position.
        
        Parameters:
            uri (str): The document's URI.
            line (int): The line position (zero-based).
            character (int): The character position (zero-based).
            
        Returns:
            dict or list: Location or locations of the definition.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_definition
        """
        text_document = {"uri": uri}
        position = {"line": line, "character": character}
        return self._send_request("textDocument/definition", {
            "textDocument": text_document,
            "position": position
        })

    def text_document_rename(self, uri: str, line: int, character: int, new_name: str):
        """
        Requests to rename a symbol at a given text document position.
        
        Parameters:
            uri (str): The document's URI.
            line (int): The line position (zero-based).
            character (int): The character position (zero-based).
            new_name (str): The new name of the symbol.
            
        Returns:
            dict: WorkspaceEdit defining the changes to make.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_rename
        """
        text_document = {"uri": uri}
        position = {"line": line, "character": character}
        return self._send_request("textDocument/rename", {
            "textDocument": text_document,
            "position": position,
            "newName": new_name
        })

    def text_document_references(self, uri: str, line: int, character: int, include_declaration: bool = True):
        """
        Requests all references to a symbol at a given text document position.
        
        Parameters:
            uri (str): The document's URI.
            line (int): The line position (zero-based).
            character (int): The character position (zero-based).
            include_declaration (bool, optional): Whether to include the declaration. Default is True.
            
        Returns:
            list: A list of locations.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_references
        """
        text_document = {"uri": uri}
        position = {"line": line, "character": character}
        return self._send_request("textDocument/references", {
            "textDocument": text_document,
            "position": position,
            "context": {"includeDeclaration": include_declaration}
        })

    def text_document_document_symbol(self, uri: str):
        """
        Requests all symbols defined in a text document.
        
        Parameters:
            uri (str): The document's URI.
            
        Returns:
            list: A list of document symbols.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_documentSymbol
        """
        text_document = {"uri": uri}
        return self._send_request("textDocument/documentSymbol", {
            "textDocument": text_document
        })

    def text_document_folding_range(self, uri: str):
        """
        Requests folding ranges for a text document.
        
        Parameters:
            uri (str): The document's URI.
            
        Returns:
            list: A list of folding ranges.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_foldingRange
        """
        text_document = {"uri": uri}
        return self._send_request("textDocument/foldingRange", {
            "textDocument": text_document
        })

    def text_document_document_highlight(self, uri: str, line: int, character: int):
        """
        Requests document highlights for a text document position.
        
        Parameters:
            uri (str): The document's URI.
            line (int): The line position (zero-based).
            character (int): The character position (zero-based).
            
        Returns:
            list: A list of document highlights.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_documentHighlight
        """
        text_document = {"uri": uri}
        position = {"line": line, "character": character}
        return self._send_request("textDocument/documentHighlight", {
            "textDocument": text_document,
            "position": position
        })

    def text_document_formatting(self, uri: str, tab_size: int = 4, insert_spaces: bool = True):
        """
        Requests formatting for an entire document.
        
        Parameters:
            uri (str): The document's URI.
            tab_size (int, optional): The tab size. Default is 4.
            insert_spaces (bool, optional): Whether to insert spaces or tabs. Default is True.
            
        Returns:
            list: A list of text edits.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_formatting
        """
        text_document = {"uri": uri}
        options = {
            "tabSize": tab_size,
            "insertSpaces": insert_spaces
        }
        return self._send_request("textDocument/formatting", {
            "textDocument": text_document,
            "options": options
        })

    def text_document_range_formatting(self, uri: str, start_line: int, start_char: int, 
                                       end_line: int, end_char: int, tab_size: int = 4, 
                                       insert_spaces: bool = True):
        """
        Requests formatting for a range in a document.
        
        Parameters:
            uri (str): The document's URI.
            start_line (int): The start line position (zero-based).
            start_char (int): The start character position (zero-based).
            end_line (int): The end line position (zero-based).
            end_char (int): The end character position (zero-based).
            tab_size (int, optional): The tab size. Default is 4.
            insert_spaces (bool, optional): Whether to insert spaces or tabs. Default is True.
            
        Returns:
            list: A list of text edits.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_rangeFormatting
        """
        text_document = {"uri": uri}
        range_obj = {
            "start": {"line": start_line, "character": start_char},
            "end": {"line": end_line, "character": end_char}
        }
        options = {
            "tabSize": tab_size,
            "insertSpaces": insert_spaces
        }
        return self._send_request("textDocument/rangeFormatting", {
            "textDocument": text_document,
            "range": range_obj,
            "options": options
        })

    def text_document_on_type_formatting(self, uri: str, line: int, character: int, ch: str, 
                                        tab_size: int = 4, insert_spaces: bool = True):
        """
        Requests formatting as the user types.
        
        Parameters:
            uri (str): The document's URI.
            line (int): The line position (zero-based).
            character (int): The character position (zero-based).
            ch (str): The character that was typed.
            tab_size (int, optional): The tab size. Default is 4.
            insert_spaces (bool, optional): Whether to insert spaces or tabs. Default is True.
            
        Returns:
            list: A list of text edits.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_onTypeFormatting
        """
        text_document = {"uri": uri}
        position = {"line": line, "character": character}
        options = {
            "tabSize": tab_size,
            "insertSpaces": insert_spaces
        }
        return self._send_request("textDocument/onTypeFormatting", {
            "textDocument": text_document,
            "position": position,
            "ch": ch,
            "options": options
        })

    def text_document_signature_help(self, uri: str, line: int, character: int):
        """
        Requests signature help information at a given text document position.
        
        Parameters:
            uri (str): The document's URI.
            line (int): The line position (zero-based).
            character (int): The character position (zero-based).
            
        Returns:
            dict: Signature help information.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_signatureHelp
        """
        text_document = {"uri": uri}
        position = {"line": line, "character": character}
        return self._send_request("textDocument/signatureHelp", {
            "textDocument": text_document,
            "position": position
        })

    def text_document_type_definition(self, uri: str, line: int, character: int):
        """
        Requests the type definition location for a symbol at a given text document position.
        
        Parameters:
            uri (str): The document's URI.
            line (int): The line position (zero-based).
            character (int): The character position (zero-based).
            
        Returns:
            dict or list: Location or locations of the type definition.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_typeDefinition
        """
        text_document = {"uri": uri}
        position = {"line": line, "character": character}
        return self._send_request("textDocument/typeDefinition", {
            "textDocument": text_document,
            "position": position
        })

    def text_document_implementation(self, uri: str, line: int, character: int):
        """
        Requests the implementation locations for a symbol at a given text document position.
        
        Parameters:
            uri (str): The document's URI.
            line (int): The line position (zero-based).
            character (int): The character position (zero-based).
            
        Returns:
            dict or list: Location or locations of the implementation.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_implementation
        """
        text_document = {"uri": uri}
        position = {"line": line, "character": character}
        return self._send_request("textDocument/implementation", {
            "textDocument": text_document,
            "position": position
        })

    def workspace_symbol(self, query: str):
        """
        Requests workspace symbols matching a query string.
        
        Parameters:
            query (str): The query string to filter symbols by.
            
        Returns:
            list: A list of workspace symbols.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#workspace_symbol
        """
        return self._send_request("workspace/symbol", {
            "query": query
        })

    def workspace_execute_command(self, command: str, arguments: list = None):
        """
        Executes a command on the server.
        
        Parameters:
            command (str): The command identifier.
            arguments (list, optional): The arguments for the command.
            
        Returns:
            dict: The result of the executed command.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#workspace_executeCommand
        """
        return self._send_request("workspace/executeCommand", {
            "command": command,
            "arguments": arguments or []
        })

    def workspace_will_rename_files(self, files: list):
        """
        Sends a request to the server to check if renaming files will affect content.
        
        Parameters:
            files (list): List of file renames. Each item should be a dict with 'oldUri' and 'newUri'.
            
        Returns:
            dict: WorkspaceEdit defining the changes to make to accommodate the rename.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#workspace_willRenameFiles
        """
        return self._send_request("workspace/willRenameFiles", {
            "files": files
        })

    def workspace_did_change_watched_files(self, changes: list):
        """
        Notifies the server that watched files have changed.
        
        Parameters:
            changes (list): List of file changes. Each item should be a dict with 'uri' and 'type'.
                Type values: 1 = Created, 2 = Changed, 3 = Deleted
                
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#workspace_didChangeWatchedFiles
        """
        self._send_notification("workspace/didChangeWatchedFiles", {
            "changes": changes
        })

    def workspace_did_change_configuration(self, settings: dict):
        """
        Notifies the server that configuration settings have changed.
        
        Parameters:
            settings (dict): The new configuration settings.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#workspace_didChangeConfiguration
        """
        self._send_notification("workspace/didChangeConfiguration", {
            "settings": settings
        })

    def text_document_code_action(self, uri: str, start_line: int, start_char: int, 
                                 end_line: int, end_char: int, diagnostics: list = None,
                                 only: list = None):
        """
        Requests code actions for a given text document range and context.
        
        Parameters:
            uri (str): The document's URI.
            start_line (int): The start line position (zero-based).
            start_char (int): The start character position (zero-based).
            end_line (int): The end line position (zero-based).
            end_char (int): The end character position (zero-based).
            diagnostics (list, optional): List of diagnostic information items.
            only (list, optional): List of code action kinds to return.
            
        Returns:
            list: A list of code action items.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_codeAction
        """
        text_document = {"uri": uri}
        range_obj = {
            "start": {"line": start_line, "character": start_char},
            "end": {"line": end_line, "character": end_char}
        }
        context = {"diagnostics": diagnostics or []}
        if only:
            context["only"] = only
            
        return self._send_request("textDocument/codeAction", {
            "textDocument": text_document,
            "range": range_obj,
            "context": context
        })

    def text_document_code_lens(self, uri: str):
        """
        Requests code lens items for a given text document.
        
        Parameters:
            uri (str): The document's URI.
            
        Returns:
            list: A list of code lens items.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_codeLens
        """
        text_document = {"uri": uri}
        return self._send_request("textDocument/codeLens", {
            "textDocument": text_document
        })

    def code_lens_resolve(self, code_lens: dict):
        """
        Resolves additional information for a code lens item.
        
        Parameters:
            code_lens (dict): The code lens to resolve.
            
        Returns:
            dict: The resolved code lens.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#codeLens_resolve
        """
        return self._send_request("codeLens/resolve", code_lens)

    def text_document_semantic_tokens_full(self, uri: str):
        """
        Requests semantic tokens for a text document.
        
        Parameters:
            uri (str): The document's URI.
            
        Returns:
            dict: Semantic tokens information.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_semanticTokens
        """
        text_document = {"uri": uri}
        return self._send_request("textDocument/semanticTokens/full", {
            "textDocument": text_document
        })

    def text_document_semantic_tokens_range(self, uri: str, start_line: int, start_char: int, 
                                           end_line: int, end_char: int):
        """
        Requests semantic tokens for a range in a text document.
        
        Parameters:
            uri (str): The document's URI.
            start_line (int): The start line position (zero-based).
            start_char (int): The start character position (zero-based).
            end_line (int): The end line position (zero-based).
            end_char (int): The end character position (zero-based).
            
        Returns:
            dict: Semantic tokens information for the specified range.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_semanticTokens
        """
        text_document = {"uri": uri}
        range_obj = {
            "start": {"line": start_line, "character": start_char},
            "end": {"line": end_line, "character": end_char}
        }
        return self._send_request("textDocument/semanticTokens/range", {
            "textDocument": text_document,
            "range": range_obj
        })

    def text_document_inlay_hint(self, uri: str, start_line: int, start_char: int,
                                end_line: int, end_char: int):
        """
        Requests inlay hints for a range in a text document.
        
        Parameters:
            uri (str): The document's URI.
            start_line (int): The start line position (zero-based).
            start_char (int): The start character position (zero-based).
            end_line (int): The end line position (zero-based).
            end_char (int): The end character position (zero-based).
            
        Returns:
            list: A list of inlay hints.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#textDocument_inlayHint
        """
        text_document = {"uri": uri}
        range_obj = {
            "start": {"line": start_line, "character": start_char},
            "end": {"line": end_line, "character": end_char}
        }
        return self._send_request("textDocument/inlayHint", {
            "textDocument": text_document,
            "range": range_obj
        })

    def inlay_hint_resolve(self, inlay_hint: dict):
        """
        Resolves additional information for an inlay hint.
        
        Parameters:
            inlay_hint (dict): The inlay hint to resolve.
            
        Returns:
            dict: The resolved inlay hint.
            
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#inlayHint_resolve
        """
        return self._send_request("inlayHint/resolve", inlay_hint)

    def notebook_document_did_open(self, notebook_document_uri: str, notebook_type: str, version: int,
                                  metadata: dict = None, cells: list = None):
        """
        Notifies the server that a notebook document has been opened.
        
        Parameters:
            notebook_document_uri (str): The notebook document's URI.
            notebook_type (str): The notebook's type.
            version (int): The notebook document's version number.
            metadata (dict, optional): The notebook document's metadata.
            cells (list, optional): The notebook's cells. Each cell should contain uri, notebook_document_uri,
                                   language, and other relevant properties.
                                   
        See: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#notebookDocument_didOpen
        """
        notebook_document = {
            "uri": notebook_document_uri,
            "notebookType": notebook_type,
            "version": version
        }
        
        if metadata is not None:
            notebook_document["metadata"] = metadata
            
        if cells is not None:
            notebook_document["cells"] = cells
            
        self._send_notification("notebookDocument/didOpen", {
            "notebookDocument": notebook_document
        })

LSP_Full_capacities = {
  "textDocument": {
    "synchronization": {
      "dynamicRegistration": True,
      "willSave": True,
      "willSaveWaitUntil": True,
      "didSave": True
    },
    "completion": {
      "dynamicRegistration": True,
      "completionItem": {
        "snippetSupport": True,
        "commitCharactersSupport": True,
        "documentationFormat": ["markdown", "plaintext"],
        "deprecatedSupport": True,
        "preselectSupport": True,
        "tagSupport": { "valueSet": [1] },
        "insertReplaceSupport": True,
        "resolveSupport": {
          "properties": ["documentation", "detail", "additionalTextEdits"]
        },
        "insertTextModeSupport": { "valueSet": [1, 2] },
        "labelDetailsSupport": True
      },
      "contextSupport": True
    },
    "hover": {
      "dynamicRegistration": True,
      "contentFormat": ["markdown", "plaintext"]
    },
    "signatureHelp": {
      "dynamicRegistration": True,
      "signatureInformation": {
        "documentationFormat": ["markdown", "plaintext"],
        "parameterInformation": {
          "labelOffsetSupport": True
        },
        "activeParameterSupport": True
      },
      "contextSupport": True
    },
    "declaration": { "dynamicRegistration": True },
    "definition": { "dynamicRegistration": True },
    "typeDefinition": { "dynamicRegistration": True },
    "implementation": { "dynamicRegistration": True },
    "references": { "dynamicRegistration": True },
    "documentHighlight": { "dynamicRegistration": True },
    "documentSymbol": {
      "dynamicRegistration": True,
      "symbolKind": {
        "valueSet": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]
      },
      "hierarchicalDocumentSymbolSupport": True,
      "tagSupport": { "valueSet": [1] }
    },
    "codeAction": {
      "dynamicRegistration": True,
      "isPreferredSupport": True,
      "disabledSupport": True,
      "dataSupport": True,
      "resolveSupport": {
        "properties": ["edit"]
      },
      "codeActionLiteralSupport": {
        "codeActionKind": {
          "valueSet": ["quickfix", "refactor", "refactor.extract", "refactor.inline", "refactor.rewrite", "source", "source.organizeImports"]
        }
      }
    },
    "codeLens": { "dynamicRegistration": True },
    "documentLink": {
      "dynamicRegistration": True,
      "tooltipSupport": True
    },
    "colorProvider": { "dynamicRegistration": True },
    "formatting": { "dynamicRegistration": True },
    "rangeFormatting": { "dynamicRegistration": True },
    "onTypeFormatting": { "dynamicRegistration": True },
    "rename": {
      "dynamicRegistration": True,
      "prepareSupport": True
    },
    "publishDiagnostics": {
      "relatedInformation": True,
      "tagSupport": { "valueSet": [1, 2] },
      "versionSupport": True,
      "codeDescriptionSupport": True,
      "dataSupport": True
    },
    "foldingRange": {
      "dynamicRegistration": True,
      "rangeLimit": 5000,
      "lineFoldingOnly": True
    },
    "semanticTokens": {
      "dynamicRegistration": True,
      "requests": {
        "range": True,
        "full": {
          "delta": True
        }
      },
      "tokenTypes": ["namespace", "type", "class", "enum", "interface", "struct", "typeParameter", "parameter", "variable", "property", "enumMember", "event", "function", "method", "macro", "keyword", "modifier", "comment", "string", "number", "regexp", "operator"],
      "tokenModifiers": ["declaration", "definition", "readonly", "static", "deprecated", "abstract", "async", "modification", "documentation", "defaultLibrary"],
      "formats": ["relative"],
      "overlappingTokenSupport": False,
      "multilineTokenSupport": False
    },
    "inlayHint": {
      "dynamicRegistration": True,
      "resolveSupport": {
        "properties": ["tooltip"]
      }
    },
    "inlineValue": {
      "dynamicRegistration": True
    },
    "notebookDocument": {
      "synchronization": {
        "dynamicRegistration": True
      }
    }
  },
  "workspace": {
    "applyEdit": True,
    "workspaceEdit": {
      "documentChanges": True,
      "resourceOperations": ["create", "rename", "delete"],
      "failureHandling": "textOnlyTransactional",
      "normalizesLineEndings": True,
      "changeAnnotationSupport": {
        "groupsOnLabel": True
      }
    },
    "didChangeConfiguration": {
      "dynamicRegistration": True
    },
    "didChangeWatchedFiles": {
      "dynamicRegistration": True
    },
    "symbol": {
      "dynamicRegistration": True,
      "symbolKind": {
        "valueSet": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]
      },
      "tagSupport": { "valueSet": [1] }
    },
    "executeCommand": {
      "dynamicRegistration": True
    },
    "workspaceFolders": True,
    "configuration": True,
    "semanticTokens": {
      "refreshSupport": True
    },
    "codeLens": {
      "refreshSupport": True
    },
    "inlayHint": {
      "refreshSupport": True
    }
  }
}


language_servers = {
    '.py'        : ('pylsp',                              # https://github.com/python-lsp/python-lsp-server
                    'pyright'),                           # https://github.com/microsoft/pyright
    '.js'        : ('tsserver',                           # https://github.com/Microsoft/TypeScript
                    'javascript-typescript-langserver',   # https://github.com/typescript-language-server/typescript-language-server
                    'eslint'),                            # https://github.com/microsoft/vscode-eslint
    '.ts'        : ('tsserver',                           # https://github.com/Microsoft/TypeScript
                    'typescript-language-server',         # https://github.com/typescript-language-server/typescript-language-server
                    'eslint'),                            # https://github.com/microsoft/vscode-eslint
    '.java'      : ('jdtls',                              # https://github.com/eclipse/eclipse.jdt.ls
                    'eclim'),                             # https://github.com/ervandew/eclim
    '.go'        : ('gopls',                              # https://github.com/golang/tools/tree/master/gopls
                    'go-langserver'),                     # https://github.com/sourcegraph/go-langserver
    '.rb'        : ('solargraph',                         # https://github.com/solargraph/solargraph
                    'ruby-lsp'),                          # https://github.com/Shopify/ruby-lsp
    '.php'       : ('intelephense',                       # https://github.com/bmewburn/vscode-intelephense
                    'phpactor',                           # https://github.com/phpactor/phpactor
                    'php-ls'),                            # https://github.com/arnaud-lb/php-language-server
    '.cpp'       : ('clangd',                             # https://clangd.llvm.org/
                    'ccls',                               # https://github.com/MaskRay/ccls
                    'clang-server'),                      # https://github.com/golang/tools/tree/master/gopls
    '.h'         : ('clangd',                             # https://clangd.llvm.org/
                    'ccls'),                              # https://github.com/MaskRay/ccls
    '.cs'        : ('omnisharp',                          # https://github.com/OmniSharp/omnisharp-roslyn
                    'razor'),                             # https://github.com/dotnet/razor
    '.html'      : ('vscode-html-languageserver',         # https://github.com/vscode-langservers/vscode-html-languageserver
                    'html-languageserver'),               # https://github.com/iamcco/vscode-html-languageserver
    '.css'       : ('vscode-css-languageserver',          # https://github.com/vscode-langservers/vscode-css-languageserver
                    'css-languageserver'),                # https://github.com/iamcco/vscode-css-languageserver
    '.json'      : ('vscode-json-languageserver',         # https://github.com/vscode-langservers/vscode-json-languageserver
                    'json-languageserver'),               # https://github.com/iamcco/vscode-json-languageserver
    '.yaml'      : ('yaml-language-server'),              # https://github.com/redhat-developer/yaml-language-server
    '.yml'       : ('yaml-language-server'),              # https://github.com/redhat-developer/yaml-language-server
    '.xml'       : ('lemminx'),                           # https://github.com/eclipse/lemminx
    '.sh'        : ('bash-language-server'),              # https://github.com/bash-lsp/bash-language-server
    '.swift'     : ('sourcekit-lsp'),                     # https://github.com/apple/sourcekit-lsp
    '.r'         : ('languageserver'),                    # https://github.com/REditorSupport/languageserver
    '.scala'     : ('metals'),                            # https://scalameta.org/metals/
    '.clj'       : ('clojure-lsp'),                       # https://github.com/snoe/clojure-lsp
    '.cljs'      : ('clojure-lsp'),                       # https://github.com/snoe/clojure-lsp
    '.fs'        : ('ionide'),                            # https://github.com/ionide/ionide-vscode-fsharp
    '.fsx'       : ('ionide'),                            # https://github.com/ionide/ionide-vscode-fsharp
    '.ex'        : ('elixir-ls'),                         # https://github.com/elixir-lsp/elixir-ls
    '.exs'       : ('elixir-ls'),                         # https://github.com/elixir-lsp/elixir-ls
    '.kt'        : ('kotlin-language-server'),            # https://github.com/fwcd/KotlinLanguageServer
    '.kts'       : ('kotlin-language-server'),            # https://github.com/fwcd/KotlinLanguageServer
    '.lua'       : ('lua-lsp'),                           # https://github.com/Alloyed/lua-lsp
    '.jl'        : ('julials'),                           # https://github.com/julia-vscode/LanguageServer.jl
    '.dart'      : ('dart_analysis_server'),              # https://github.com/dart-lang/sdk
    '.md'        : ('marksman'),                          # https://github.com/artempyanykh/marksman
    '.vue'       : ('vls'),                               # https://github.com/vuejs/language-tools
    '.svelte'    : ('svelteserver'),                      # https://github.com/sveltejs/language-tools
    '.tex'       : ('texlab'),                            # https://github.com/latex-lsp/texlab
    '.bib'       : ('texlab'),                            # https://github.com/latex-lsp/texlab
    '.xaml'      : ('omnisharp'),                         # https://github.com/OmniSharp/omnisharp-roslyn
    '.erl'       : ('erlang_ls'),                         # https://github.com/erlang-ls/erlang_ls
    '.coffee'    : ('coffeels'),                          # https://github.com/graphcool/coco-language-server (example fork)
    '.cfg'       : ('efm-langserver'),                    # https://github.com/mattn/efm-langserver
    '.toml'      : ('taplo'),                             # https://github.com/tamasfe/taplo
    '.ini'       : ('efm-langserver'),                    # https://github.com/mattn/efm-langserver
    '.sql'       : ('sqls'),                              # https://github.com/lighttiger2505/sqls
    '.dockerfile': ('dockerfile-language-server'),        # https://github.com/rcjsuen/dockerfile-language-server-nodejs
    '.make'      : ('efm-langserver'),                    # https://github.com/mattn/efm-langserver
    '.cmake'     : ('cmake-language-server'),             # https://github.com/regen100/cmake-language-server
    '.ps1'       : ('powershell-es'),                     # https://github.com/PowerShell/PowerShellEditorServices
    '.asm'       : ('nasm-lsp'),                          # https://github.com/viperproject/prusti-dev
}

