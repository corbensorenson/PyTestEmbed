#!/usr/bin/env python3
"""
PyTestEmbed MCP Server

Provides Model Context Protocol (MCP) integration for PyTestEmbed,
allowing agentic coders like Augment and Cline to interact with
PyTestEmbed's testing and documentation capabilities.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import websockets
from dataclasses import asdict

from .live_runner import LiveTestClient
from .smart_generator import SmartCodeGenerator, GenerationRequest, CodeContext
from .parser import PyTestEmbedParser
from .config_manager import ConfigManager


class PyTestEmbedMCPServer:
    """MCP Server for PyTestEmbed integration with agentic coding tools."""
    
    def __init__(self, workspace_path: str = ".", live_test_port: int = 8765):
        self.workspace_path = Path(workspace_path).resolve()
        self.live_test_port = live_test_port
        self.live_test_client = None
        self.parser = PyTestEmbedParser()
        self.config_manager = ConfigManager()
        self.smart_generator = SmartCodeGenerator()
        
        # MCP protocol handlers
        self.tools = {
            "run_tests": self._run_tests,
            "run_test_at_line": self._run_test_at_line,
            "generate_test_block": self._generate_test_block,
            "generate_doc_block": self._generate_doc_block,
            "generate_both_blocks": self._generate_both_blocks,
            "parse_file": self._parse_file,
            "get_test_results": self._get_test_results,
            "get_coverage": self._get_coverage,
            "validate_syntax": self._validate_syntax,
            "convert_to_pytestembed": self._convert_to_pytestembed
        }
        
        self.resources = {
            "workspace": self._get_workspace_info,
            "config": self._get_config,
            "test_status": self._get_test_status
        }
    
    async def start(self, port: int = 3001):
        """Start the MCP server."""
        print(f"🚀 Starting PyTestEmbed MCP Server on port {port}")
        
        # Try to connect to live test server
        await self._connect_to_live_test_server()
        
        # Start MCP server
        async def handle_client(websocket, path):
            print(f"📱 MCP Client connected: {websocket.remote_address}")
            try:
                async for message in websocket:
                    response = await self._handle_mcp_message(message)
                    if response:
                        await websocket.send(json.dumps(response))
            except websockets.exceptions.ConnectionClosed:
                print(f"📱 MCP Client disconnected: {websocket.remote_address}")
            except Exception as e:
                print(f"❌ Error handling MCP client: {e}")
        
        server = await websockets.serve(handle_client, "localhost", port)
        print(f"✅ PyTestEmbed MCP Server running at ws://localhost:{port}")
        
        try:
            await server.wait_closed()
        except KeyboardInterrupt:
            print("\n🛑 Stopping MCP server...")
        finally:
            if self.live_test_client:
                await self.live_test_client.disconnect()
    
    async def _connect_to_live_test_server(self):
        """Connect to the live test server."""
        try:
            self.live_test_client = LiveTestClient(self.live_test_port)
            connected = await self.live_test_client.connect()
            if connected:
                print(f"📡 Connected to live test server on port {self.live_test_port}")
            else:
                print(f"⚠️ Could not connect to live test server on port {self.live_test_port}")
                print("   Live testing features will be unavailable")
        except Exception as e:
            print(f"❌ Failed to connect to live test server: {e}")
    
    async def _handle_mcp_message(self, message: str) -> Optional[Dict[str, Any]]:
        """Handle incoming MCP protocol messages."""
        try:
            data = json.loads(message)
            method = data.get("method")
            params = data.get("params", {})
            request_id = data.get("id")
            
            if method == "tools/list":
                return self._list_tools(request_id)
            elif method == "tools/call":
                return await self._call_tool(params, request_id)
            elif method == "resources/list":
                return self._list_resources(request_id)
            elif method == "resources/read":
                return await self._read_resource(params, request_id)
            elif method == "initialize":
                return self._initialize(params, request_id)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    def _initialize(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Handle MCP initialization."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {}
                },
                "serverInfo": {
                    "name": "pytestembed",
                    "version": "1.0.0"
                }
            }
        }
    
    def _list_tools(self, request_id: Any) -> Dict[str, Any]:
        """List available MCP tools."""
        tools_list = [
            {
                "name": "run_tests",
                "description": "Run all tests in a Python file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to Python file"}
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "run_test_at_line",
                "description": "Run a specific test at a given line number",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to Python file"},
                        "line_number": {"type": "integer", "description": "Line number of test"}
                    },
                    "required": ["file_path", "line_number"]
                }
            },
            {
                "name": "generate_test_block",
                "description": "Generate PyTestEmbed test block for a function",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to Python file"},
                        "line_number": {"type": "integer", "description": "Line number of function"},
                        "ai_provider": {"type": "string", "description": "AI provider (ollama/lmstudio)", "default": "lmstudio"}
                    },
                    "required": ["file_path", "line_number"]
                }
            },
            {
                "name": "generate_doc_block",
                "description": "Generate PyTestEmbed documentation block for a function",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to Python file"},
                        "line_number": {"type": "integer", "description": "Line number of function"},
                        "ai_provider": {"type": "string", "description": "AI provider (ollama/lmstudio)", "default": "lmstudio"}
                    },
                    "required": ["file_path", "line_number"]
                }
            },
            {
                "name": "generate_both_blocks",
                "description": "Generate both test and doc blocks for a function",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to Python file"},
                        "line_number": {"type": "integer", "description": "Line number of function"},
                        "ai_provider": {"type": "string", "description": "AI provider (ollama/lmstudio)", "default": "lmstudio"}
                    },
                    "required": ["file_path", "line_number"]
                }
            },
            {
                "name": "parse_file",
                "description": "Parse a Python file and extract PyTestEmbed blocks",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to Python file"}
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "validate_syntax",
                "description": "Validate PyTestEmbed syntax in a file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to Python file"}
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "convert_to_pytestembed",
                "description": "Convert standard Python file to PyTestEmbed format",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to Python file"},
                        "ai_provider": {"type": "string", "description": "AI provider (ollama/lmstudio)", "default": "lmstudio"}
                    },
                    "required": ["file_path"]
                }
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": tools_list
            }
        }

    def _list_resources(self, request_id: Any) -> Dict[str, Any]:
        """List available MCP resources."""
        resources_list = [
            {
                "uri": "pytestembed://workspace",
                "name": "Workspace Info",
                "description": "Information about the current workspace"
            },
            {
                "uri": "pytestembed://config",
                "name": "Configuration",
                "description": "PyTestEmbed configuration settings"
            },
            {
                "uri": "pytestembed://test_status",
                "name": "Test Status",
                "description": "Current test execution status"
            }
        ]

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "resources": resources_list
            }
        }

    async def _call_tool(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Call a specific tool."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in self.tools:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": f"Unknown tool: {tool_name}"
                }
            }

        try:
            result = await self.tools[tool_name](arguments)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Tool execution failed: {str(e)}"
                }
            }

    async def _read_resource(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Read a specific resource."""
        uri = params.get("uri", "")

        if not uri.startswith("pytestembed://"):
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": f"Invalid resource URI: {uri}"
                }
            }

        resource_name = uri.replace("pytestembed://", "")

        if resource_name not in self.resources:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": f"Unknown resource: {resource_name}"
                }
            }

        try:
            result = await self.resources[resource_name]()
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Resource read failed: {str(e)}"
                }
            }

    # Tool implementations
    async def _run_tests(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Run all tests in a file."""
        file_path = args["file_path"]

        if not self.live_test_client:
            return {"error": "Live test server not available"}

        try:
            await self.live_test_client.run_tests(file_path)
            return {
                "status": "success",
                "message": f"Tests started for {file_path}",
                "file_path": file_path
            }
        except Exception as e:
            return {"error": f"Failed to run tests: {str(e)}"}

    async def _run_test_at_line(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Run a specific test at a line."""
        file_path = args["file_path"]
        line_number = args["line_number"]

        if not self.live_test_client:
            return {"error": "Live test server not available"}

        try:
            await self.live_test_client.run_test_at_line(file_path, line_number)
            return {
                "status": "success",
                "message": f"Test started at line {line_number} in {file_path}",
                "file_path": file_path,
                "line_number": line_number
            }
        except Exception as e:
            return {"error": f"Failed to run test: {str(e)}"}

    async def _generate_test_block(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a test block for a function."""
        file_path = args["file_path"]
        line_number = args["line_number"]
        ai_provider = args.get("ai_provider", "lmstudio")

        try:
            # Read the file
            full_path = self.workspace_path / file_path
            with open(full_path, 'r') as f:
                content = f.read()

            # Generate test block
            result = self.smart_generator.generate_for_function(
                source_code=content,
                line_number=line_number,
                file_path=str(full_path),
                generation_type="test"
            )

            return {
                "status": "success",
                "generated_blocks": result,
                "file_path": file_path,
                "line_number": line_number
            }
        except Exception as e:
            return {"error": f"Failed to generate test block: {str(e)}"}

    async def _generate_doc_block(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a documentation block for a function."""
        file_path = args["file_path"]
        line_number = args["line_number"]
        ai_provider = args.get("ai_provider", "lmstudio")

        try:
            # Read the file
            full_path = self.workspace_path / file_path
            with open(full_path, 'r') as f:
                content = f.read()

            # Generate doc block
            result = self.smart_generator.generate_for_function(
                source_code=content,
                line_number=line_number,
                file_path=str(full_path),
                generation_type="doc"
            )

            return {
                "status": "success",
                "generated_blocks": result,
                "file_path": file_path,
                "line_number": line_number
            }
        except Exception as e:
            return {"error": f"Failed to generate doc block: {str(e)}"}

    async def _generate_both_blocks(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate both test and doc blocks for a function."""
        file_path = args["file_path"]
        line_number = args["line_number"]
        ai_provider = args.get("ai_provider", "lmstudio")

        try:
            # Read the file
            full_path = self.workspace_path / file_path
            with open(full_path, 'r') as f:
                content = f.read()

            # Generate both blocks
            result = self.smart_generator.generate_for_function(
                source_code=content,
                line_number=line_number,
                file_path=str(full_path),
                generation_type="both"
            )

            return {
                "status": "success",
                "generated_blocks": result,
                "file_path": file_path,
                "line_number": line_number
            }
        except Exception as e:
            return {"error": f"Failed to generate blocks: {str(e)}"}

    async def _parse_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a Python file and extract PyTestEmbed blocks."""
        file_path = args["file_path"]

        try:
            # Read the file
            full_path = self.workspace_path / file_path
            with open(full_path, 'r') as f:
                content = f.read()

            # Parse the file
            parsed = self.parser.parse_file(content)

            return {
                "status": "success",
                "parsed_data": asdict(parsed),
                "file_path": file_path
            }
        except Exception as e:
            return {"error": f"Failed to parse file: {str(e)}"}

    async def _get_test_results(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get current test results."""
        if not self.live_test_client:
            return {"error": "Live test server not available"}

        return {
            "status": "success",
            "message": "Test results would be retrieved from live test server",
            "note": "This requires implementing result caching in live test client"
        }

    async def _get_coverage(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get coverage information."""
        file_path = args.get("file_path")

        if not self.live_test_client:
            return {"error": "Live test server not available"}

        try:
            if file_path:
                await self.live_test_client.get_coverage(file_path)

            return {
                "status": "success",
                "message": f"Coverage requested for {file_path if file_path else 'all files'}",
                "file_path": file_path
            }
        except Exception as e:
            return {"error": f"Failed to get coverage: {str(e)}"}

    async def _validate_syntax(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Validate PyTestEmbed syntax in a file."""
        file_path = args["file_path"]

        try:
            # Read the file
            full_path = self.workspace_path / file_path
            with open(full_path, 'r') as f:
                content = f.read()

            # Try to parse the file
            try:
                parsed = self.parser.parse_file(content)
                return {
                    "status": "success",
                    "valid": True,
                    "message": "PyTestEmbed syntax is valid",
                    "file_path": file_path,
                    "functions_count": len(parsed.functions),
                    "classes_count": len(parsed.classes)
                }
            except Exception as parse_error:
                return {
                    "status": "success",
                    "valid": False,
                    "message": f"PyTestEmbed syntax error: {str(parse_error)}",
                    "file_path": file_path
                }
        except Exception as e:
            return {"error": f"Failed to validate syntax: {str(e)}"}

    async def _convert_to_pytestembed(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a standard Python file to PyTestEmbed format."""
        file_path = args["file_path"]
        ai_provider = args.get("ai_provider", "lmstudio")

        try:
            # Read the file
            full_path = self.workspace_path / file_path
            with open(full_path, 'r') as f:
                content = f.read()

            # This would use the convert functionality
            # For now, return a placeholder
            return {
                "status": "success",
                "message": f"Conversion to PyTestEmbed format initiated for {file_path}",
                "file_path": file_path,
                "ai_provider": ai_provider,
                "note": "Full conversion implementation would generate test and doc blocks for all functions"
            }
        except Exception as e:
            return {"error": f"Failed to convert file: {str(e)}"}

    # Resource implementations
    async def _get_workspace_info(self) -> Dict[str, Any]:
        """Get workspace information."""
        return {
            "workspace_path": str(self.workspace_path),
            "live_test_port": self.live_test_port,
            "live_test_connected": self.live_test_client is not None,
            "python_files": [str(p.relative_to(self.workspace_path))
                           for p in self.workspace_path.rglob("*.py")]
        }

    async def _get_config(self) -> Dict[str, Any]:
        """Get PyTestEmbed configuration."""
        config = self.config_manager.load_config()
        return asdict(config)

    async def _get_test_status(self) -> Dict[str, Any]:
        """Get current test status."""
        return {
            "live_test_server_connected": self.live_test_client is not None,
            "live_test_port": self.live_test_port,
            "workspace": str(self.workspace_path)
        }


# CLI entry point for MCP server
async def start_mcp_server(workspace: str = ".", mcp_port: int = 3001, live_test_port: int = 8765):
    """Start the PyTestEmbed MCP server."""
    server = PyTestEmbedMCPServer(workspace, live_test_port)
    await server.start(mcp_port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PyTestEmbed MCP Server")
    parser.add_argument("--workspace", default=".", help="Workspace directory")
    parser.add_argument("--mcp-port", type=int, default=3001, help="MCP server port")
    parser.add_argument("--live-test-port", type=int, default=8765, help="Live test server port")

    args = parser.parse_args()

    asyncio.run(start_mcp_server(args.workspace, args.mcp_port, args.live_test_port))
