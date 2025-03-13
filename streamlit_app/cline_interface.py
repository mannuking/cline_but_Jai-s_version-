import streamlit as st
import os
import json
import time
import anthropic
import sys
import re
from pathlib import Path

class ClineInterface:
    def __init__(self):
        if 'client' not in st.session_state:
            st.session_state.client = None
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []
    
    def set_api_key(self, api_key):
        """Set up the client with the provided API key."""
        if api_key:
            try:
                st.session_state.client = anthropic.Anthropic(api_key=api_key)
                return True
            except Exception as e:
                st.error(f"Error initializing client: {str(e)}")
                return False
        return False
    
    def generate_system_prompt(self, project_path):
        """Generate system prompt with project context."""
        system_prompt = """You are Cline, an AI programming assistant.
You help users build software projects by understanding their requirements and providing practical code solutions.
You can assist with code writing, debugging, and explaining concepts.

For file operations, tell the user to use the File Explorer panel.
For running commands, tell the user to use the Terminal panel.

Follow these guidelines:
1. Keep your answers focused on the user's programming needs
2. Provide complete, working code solutions
3. Explain your reasoning clearly
4. When suggesting file changes, specify the exact file path and code to be modified
5. Help the user understand errors and debugging strategies

The user is working in a web-based IDE with:
- A file explorer panel for browsing and editing files
- A code editor with syntax highlighting
- A terminal for running commands
- This chat interface to communicate with you

The user can download their complete project when finished.
"""
        
        # Add project files information
        files_info = "\n\nCurrent Project Structure:\n"
        for root, dirs, files in os.walk(project_path):
            if "__pycache__" in root or ".git" in root:
                continue
                
            rel_path = os.path.relpath(root, project_path)
            level = len(Path(rel_path).parts)
            indent = "  " * level
            
            if rel_path != ".":
                files_info += f"{indent}📁 {os.path.basename(root)}/\n"
            
            for file in sorted(files):
                if file.startswith(".") or file.endswith(".pyc"):
                    continue
                files_info += f"{indent}  📄 {file}\n"
        
        system_prompt += files_info
        return system_prompt
    
    def handle_tool_calls(self, tool_calls, file_explorer, terminal, project_path, open_files):
        """Handle tool calls from the AI."""
        results = []
        for tool_call in tool_calls:
            function = tool_call.function
            
            if function.name == "read_file":
                try:
                    args = json.loads(function.arguments)
                    file_path = os.path.join(project_path, args.get("path", ""))
                    
                    if os.path.exists(file_path):
                        with open(file_path, 'r') as f:
                            content = f.read()
                        results.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function.name,
                            "content": f"Content of {args.get('path')}:\n\n```\n{content}\n```"
                        })
                    else:
                        results.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function.name,
                            "content": f"Error: File '{args.get('path')}' not found."
                        })
                except Exception as e:
                    results.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function.name,
                        "content": f"Error reading file: {str(e)}"
                    })
                    
            elif function.name == "write_file":
                try:
                    args = json.loads(function.arguments)
                    file_path = os.path.join(project_path, args.get("path", ""))
                    content = args.get("content", "")
                    
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    with open(file_path, 'w') as f:
                        f.write(content)
                    
                    # Update open file if it's currently open
                    if file_path in open_files:
                        open_files[file_path] = content
                    
                    results.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function.name,
                        "content": f"File '{args.get('path')}' has been created/updated successfully."
                    })
                except Exception as e:
                    results.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function.name,
                        "content": f"Error writing file: {str(e)}"
                    })
                    
            elif function.name == "execute_command":
                try:
                    args = json.loads(function.arguments)
                    command = args.get("command", "")
                    
                    stdout, stderr, returncode = terminal.execute_command(command)
                    
                    result = f"Command: {command}\n"
                    if stdout:
                        result += f"\nStandard Output:\n{stdout}"
                    if stderr:
                        result += f"\nStandard Error:\n{stderr}"
                    result += f"\nReturn Code: {returncode}"
                    
                    results.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function.name,
                        "content": result
                    })
                except Exception as e:
                    results.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function.name,
                        "content": f"Error executing command: {str(e)}"
                    })
                    
            elif function.name == "list_directory":
                try:
                    args = json.loads(function.arguments)
                    dir_path = args.get("path", ".")
                    full_path = os.path.join(project_path, dir_path)
                    
                    if os.path.exists(full_path) and os.path.isdir(full_path):
                        files = os.listdir(full_path)
                        file_info = []
                        
                        for file in sorted(files):
                            file_path = os.path.join(full_path, file)
                            is_dir = os.path.isdir(file_path)
                            file_type = "directory" if is_dir else "file"
                            
                            file_info.append({
                                "name": file,
                                "type": file_type,
                                "size": os.path.getsize(file_path) if not is_dir else None
                            })
                        
                        results.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function.name,
                            "content": json.dumps(file_info, indent=2)
                        })
                    else:
                        results.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function.name,
                            "content": f"Error: Directory '{dir_path}' not found."
                        })
                except Exception as e:
                    results.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function.name,
                        "content": f"Error listing directory: {str(e)}"
                    })
                    
        return results
    
    def render(self, file_explorer, terminal, open_files, project_path):
        """Render the Cline Assistant interface."""
        # Check if API key is set
        if not st.session_state.client:
            st.warning("Please enter your API key in the sidebar to use the Cline Assistant.")
            return
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.markdown(f"**You**: {message['content']}")
                elif message["role"] == "assistant":
                    st.markdown(f"**Cline**: {message['content']}")
                elif message["role"] == "tool_result":
                    with st.expander(f"Tool Result: {message['name']}"):
                        st.code(message['content'], language="plaintext")
        
        # User input
        with st.form("chat_input_form", clear_on_submit=True):
            user_input = st.text_area("Message Cline", height=100)
            submitted = st.form_submit_button("Send")
            
        if submitted and user_input:
            # Add user message to chat history
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Add user message to conversation history
            st.session_state.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Generate system prompt with project context
            system_prompt = self.generate_system_prompt(project_path)
            
            # Define tools
            tools = [
                {
                    "name": "read_file",
                    "description": "Read the content of a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "The path to the file to read"
                            }
                        },
                        "required": ["path"]
                    }
                },
                {
                    "name": "write_file",
                    "description": "Write content to a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "The path to the file to write"
                            },
                            "content": {
                                "type": "string",
                                "description": "The content to write to the file"
                            }
                        },
                        "required": ["path", "content"]
                    }
                },
                {
                    "name": "execute_command",
                    "description": "Execute a command in the terminal",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The command to execute"
                            }
                        },
                        "required": ["command"]
                    }
                },
                {
                    "name": "list_directory",
                    "description": "List files and folders in a directory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "The path to the directory to list"
                            }
                        },
                        "required": ["path"]
                    }
                }
            ]
            
            try:
                with st.spinner("Cline is thinking..."):
                    # Make API call
                    response = st.session_state.client.messages.create(
                        model="claude-3-sonnet-20240229",
                        max_tokens=4000,
                        system=system_prompt,
                        messages=st.session_state.conversation_history,
                        tools=tools,
                    )
                    
                    # Process the response
                    if response.content:
                        assistant_message_content = ""
                        for content_block in response.content:
                            if content_block.type == "text":
                                assistant_message_content += content_block.text
                        
                        # Add assistant message to chat history
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": assistant_message_content
                        })
                        
                        # Add assistant message to conversation history
                        st.session_state.conversation_history.append({
                            "role": "assistant",
                            "content": assistant_message_content
                        })
                    
                    # Handle tool calls if any
                    if response.tool_calls:
                        tool_results = self.handle_tool_calls(
                            response.tool_calls,
                            file_explorer,
                            terminal,
                            project_path,
                            open_files
                        )
                        
                        for tool_result in tool_results:
                            # Add tool result to chat history
                            st.session_state.chat_history.append({
                                "role": "tool_result",
                                "name": tool_result["name"],
                                "content": tool_result["content"]
                            })
                            
                            # Add tool result to conversation history
                            st.session_state.conversation_history.append(tool_result)
                        
                        # Make a follow-up API call with the tool results
                        with st.spinner("Processing tool results..."):
                            follow_up_response = st.session_state.client.messages.create(
                                model="claude-3-sonnet-20240229",
                                max_tokens=4000,
                                system=system_prompt,
                                messages=st.session_state.conversation_history
                            )
                            
                            if follow_up_response.content:
                                follow_up_content = ""
                                for content_block in follow_up_response.content:
                                    if content_block.type == "text":
                                        follow_up_content += content_block.text
                                
                                # Add follow-up message to chat history
                                st.session_state.chat_history.append({
                                    "role": "assistant",
                                    "content": follow_up_content
                                })
                                
                                # Add follow-up message to conversation history
                                st.session_state.conversation_history.append({
                                    "role": "assistant",
                                    "content": follow_up_content
                                })
                
            except Exception as e:
                st.error(f"Error communicating with Cline: {str(e)}")
            
            # Force a rerun to update the chat container
            st.experimental_rerun()

# Add additional utility functions
def extract_code_blocks(text):
    """Extract code blocks from markdown text."""
    pattern = r"```(?:\w+)?\s*([\s\S]*?)```"
    return re.findall(pattern, text)

