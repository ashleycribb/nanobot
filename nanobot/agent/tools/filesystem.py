"""File system tools: read, write, edit."""

import asyncio
from pathlib import Path
from typing import Any

from nanobot.agent.tools.base import Tool


def _resolve_path(path: str, allowed_dir: Path | None = None) -> Path:
    """Resolve path and optionally enforce directory restriction."""
    resolved = Path(path).expanduser().resolve()
    if allowed_dir and not str(resolved).startswith(str(allowed_dir.resolve())):
        raise PermissionError(f"Path {path} is outside allowed directory {allowed_dir}")
    return resolved


class ReadFileTool(Tool):
    """Tool to read file contents."""
    
    def __init__(self, allowed_dir: Path | None = None):
        self._allowed_dir = allowed_dir

    @property
    def name(self) -> str:
        return "read_file"
    
    @property
    def description(self) -> str:
        return "Read the contents of a file at the given path."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The file path to read"
                }
            },
            "required": ["path"]
        }
    
    async def execute(self, path: str, **kwargs: Any) -> str:
        try:
            file_path = _resolve_path(path, self._allowed_dir)
            if not file_path.exists():
                return f"Error: File not found: {path}"
            if not file_path.is_file():
                return f"Error: Not a file: {path}"
            
            content = await asyncio.to_thread(file_path.read_text, encoding="utf-8")
            return content
        except PermissionError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error reading file: {str(e)}"


class WriteFileTool(Tool):
    """Tool to write content to a file."""
    
    def __init__(self, allowed_dir: Path | None = None):
        self._allowed_dir = allowed_dir

    @property
    def name(self) -> str:
        return "write_file"
    
    @property
    def description(self) -> str:
        return "Write content to a file at the given path. Creates parent directories if needed."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The file path to write to"
                },
                "content": {
                    "type": "string",
                    "description": "The content to write"
                }
            },
            "required": ["path", "content"]
        }
    
    def _write_sync(self, file_path: Path, content: str, path_str: str) -> str:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content)} bytes to {path_str}"

    async def execute(self, path: str, content: str, **kwargs: Any) -> str:
        try:
            file_path = _resolve_path(path, self._allowed_dir)
            return await asyncio.to_thread(self._write_sync, file_path, content, path)
        except PermissionError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error writing file: {str(e)}"


class EditFileTool(Tool):
    """Tool to edit a file by replacing text."""
    
    def __init__(self, allowed_dir: Path | None = None):
        self._allowed_dir = allowed_dir

    @property
    def name(self) -> str:
        return "edit_file"
    
    @property
    def description(self) -> str:
        return "Edit a file by replacing old_text with new_text. The old_text must exist exactly in the file."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The file path to edit"
                },
                "old_text": {
                    "type": "string",
                    "description": "The exact text to find and replace"
                },
                "new_text": {
                    "type": "string",
                    "description": "The text to replace with"
                }
            },
            "required": ["path", "old_text", "new_text"]
        }
    
    def _edit_sync(self, file_path: Path, old_text: str, new_text: str, path_str: str) -> str:
        if not file_path.exists():
            return f"Error: File not found: {path_str}"

        content = file_path.read_text(encoding="utf-8")

        if old_text not in content:
            return f"Error: old_text not found in file. Make sure it matches exactly."

        # Count occurrences
        count = content.count(old_text)
        if count > 1:
            return f"Warning: old_text appears {count} times. Please provide more context to make it unique."

        new_content = content.replace(old_text, new_text, 1)
        file_path.write_text(new_content, encoding="utf-8")

        return f"Successfully edited {path_str}"

    async def execute(self, path: str, old_text: str, new_text: str, **kwargs: Any) -> str:
        try:
            file_path = _resolve_path(path, self._allowed_dir)
            return await asyncio.to_thread(self._edit_sync, file_path, old_text, new_text, path)
        except PermissionError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error editing file: {str(e)}"


class ListDirTool(Tool):
    """Tool to list directory contents."""
    
    def __init__(self, allowed_dir: Path | None = None):
        self._allowed_dir = allowed_dir

    @property
    def name(self) -> str:
        return "list_dir"
    
    @property
    def description(self) -> str:
        return "List the contents of a directory."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The directory path to list"
                }
            },
            "required": ["path"]
        }
    
    def _list_sync(self, dir_path: Path, path_str: str) -> str:
        if not dir_path.exists():
            return f"Error: Directory not found: {path_str}"
        if not dir_path.is_dir():
            return f"Error: Not a directory: {path_str}"

        items = []
        for item in sorted(dir_path.iterdir()):
            prefix = "📁 " if item.is_dir() else "📄 "
            items.append(f"{prefix}{item.name}")

        if not items:
            return f"Directory {path_str} is empty"

        return "\n".join(items)

    async def execute(self, path: str, **kwargs: Any) -> str:
        try:
            dir_path = _resolve_path(path, self._allowed_dir)
            return await asyncio.to_thread(self._list_sync, dir_path, path)
        except PermissionError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error listing directory: {str(e)}"
