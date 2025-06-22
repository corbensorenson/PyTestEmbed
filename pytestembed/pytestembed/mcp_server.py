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
    
    def __init__(self, workspace_path: str = ".", live_test_port: int = 8765, dependency_service_port: int = 8769):
        self.workspace_path = Path(workspace_path).resolve()
        self.live_test_port = live_test_port
        self.dependency_service_port = dependency_service_port
        self.live_test_client = None
        self.parser = PyTestEmbedParser()
        self.config_manager = ConfigManager()
        self.smart_generator = SmartCodeGenerator()

        # Service processes (for auto-starting dependencies)
        self.live_test_process = None
        self.dependency_service_process = None
        
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
            "convert_to_pytestembed": self._convert_to_pytestembed,
            # Dependency graph tools
            "get_dependencies": self._get_dependencies,
            "get_dependents": self._get_dependents,
            "get_element_info": self._get_element_info,
            "find_dead_code": self._find_dead_code,
            "get_dependency_graph": self._get_dependency_graph,
            "analyze_impact": self._analyze_impact,
            "find_related_code": self._find_related_code,
            "get_navigation_suggestions": self._get_navigation_suggestions
        }
        
        self.resources = {
            "workspace": self._get_workspace_info,
            "config": self._get_config,
            "test_status": self._get_test_status,
            "dependency_graph": self._get_dependency_graph_resource,
            "failing_tests": self._get_failing_tests,
            "dead_code": self._get_dead_code_resource
        }
    
    async def start(self, port: int = 3001):
        """Start the MCP server."""
        print(f"🚀 Starting PyTestEmbed MCP Server on port {port}")

        # Ensure all required services are running
        print("🔧 Ensuring all PyTestEmbed services are running...")

        # Start dependency service first (live test depends on it)
        if not await self.ensure_dependency_service_running():
            print("❌ Failed to start dependency service")
            return

        # Start live test service (depends on dependency service)
        if not await self.ensure_live_test_service_running():
            print("❌ Failed to start live test service")
            return

        print("✅ All PyTestEmbed services are running")

        # Connect to live test server
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

    async def ensure_dependency_service_running(self):
        """Ensure dependency service is running, start it if needed."""
        try:
            # Try to connect to existing dependency service
            test_ws = await websockets.connect(f"ws://localhost:{self.dependency_service_port}")
            await test_ws.close()
            print(f"✅ Dependency service already running on port {self.dependency_service_port}")
            return True
        except Exception:
            print(f"🔗 Starting dependency service on port {self.dependency_service_port}")

            try:
                import subprocess
                self.dependency_service_process = subprocess.Popen([
                    'python', '-m', 'pytestembed.dependency_service',
                    str(self.workspace_path), str(self.dependency_service_port)
                ], cwd=str(self.workspace_path))

                # Wait for it to start
                await asyncio.sleep(3)

                # Verify it started
                try:
                    test_ws = await websockets.connect(f"ws://localhost:{self.dependency_service_port}")
                    await test_ws.close()
                    print(f"✅ Dependency service started successfully")
                    return True
                except Exception as e:
                    print(f"❌ Failed to verify dependency service startup: {e}")
                    return False

            except Exception as e:
                print(f"❌ Failed to start dependency service: {e}")
                return False

    async def ensure_live_test_service_running(self):
        """Ensure live test service is running, start it if needed."""
        try:
            # Try to connect to existing live test service
            test_ws = await websockets.connect(f"ws://localhost:{self.live_test_port}")
            await test_ws.close()
            print(f"✅ Live test service already running on port {self.live_test_port}")
            return True
        except Exception:
            print(f"🔗 Starting live test service on port {self.live_test_port}")

            try:
                import subprocess
                self.live_test_process = subprocess.Popen([
                    'python', '-m', 'pytestembed.live_runner',
                    str(self.workspace_path), str(self.live_test_port)
                ], cwd=str(self.workspace_path))

                # Wait for it to start
                await asyncio.sleep(5)

                # Verify it started
                try:
                    test_ws = await websockets.connect(f"ws://localhost:{self.live_test_port}")
                    await test_ws.close()
                    print(f"✅ Live test service started successfully")
                    return True
                except Exception as e:
                    print(f"❌ Failed to verify live test service startup: {e}")
                    return False

            except Exception as e:
                print(f"❌ Failed to start live test service: {e}")
                return False

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
            },
            {
                "name": "get_dependencies",
                "description": "Get what a code element depends on",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to Python file"},
                        "element_name": {"type": "string", "description": "Name of function/class/method"},
                        "line_number": {"type": "integer", "description": "Line number (optional)"}
                    },
                    "required": ["file_path", "element_name"]
                }
            },
            {
                "name": "get_dependents",
                "description": "Get what depends on a code element (who uses it)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to Python file"},
                        "element_name": {"type": "string", "description": "Name of function/class/method"},
                        "line_number": {"type": "integer", "description": "Line number (optional)"}
                    },
                    "required": ["file_path", "element_name"]
                }
            },
            {
                "name": "get_element_info",
                "description": "Get detailed information about a code element",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to Python file"},
                        "element_name": {"type": "string", "description": "Name of function/class/method"},
                        "line_number": {"type": "integer", "description": "Line number (optional)"}
                    },
                    "required": ["file_path", "element_name"]
                }
            },
            {
                "name": "find_dead_code",
                "description": "Find potentially unused code in the project",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to specific file (optional)"}
                    }
                }
            },
            {
                "name": "analyze_impact",
                "description": "Analyze the impact of changing a code element",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to Python file"},
                        "element_name": {"type": "string", "description": "Name of function/class/method"},
                        "change_type": {"type": "string", "description": "Type of change: modify, delete, rename", "default": "modify"}
                    },
                    "required": ["file_path", "element_name"]
                }
            },
            {
                "name": "find_related_code",
                "description": "Find code related to a specific element (dependencies + dependents)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to Python file"},
                        "element_name": {"type": "string", "description": "Name of function/class/method"},
                        "depth": {"type": "integer", "description": "How many levels deep to search", "default": 2}
                    },
                    "required": ["file_path", "element_name"]
                }
            },
            {
                "name": "get_navigation_suggestions",
                "description": "Get suggestions for where to navigate after making changes",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "changed_files": {"type": "array", "items": {"type": "string"}, "description": "List of files that were changed"},
                        "changed_elements": {"type": "array", "items": {"type": "string"}, "description": "List of elements that were changed"}
                    },
                    "required": ["changed_files"]
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
            },
            {
                "uri": "pytestembed://dependency_graph",
                "name": "Dependency Graph",
                "description": "Complete project dependency graph"
            },
            {
                "uri": "pytestembed://failing_tests",
                "name": "Failing Tests",
                "description": "List of currently failing tests"
            },
            {
                "uri": "pytestembed://dead_code",
                "name": "Dead Code",
                "description": "Potentially unused code in the project"
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

    # Dependency graph tool implementations
    async def _get_dependencies(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get what a code element depends on."""
        file_path = args["file_path"]
        element_name = args["element_name"]
        line_number = args.get("line_number")

        if not self.live_test_client:
            return {"error": "Live test server not available"}

        try:
            # Send request to live test server
            await self.live_test_client.get_dependencies(file_path, element_name, line_number)

            # Note: In a real implementation, we'd need to wait for the response
            # For now, return a success message indicating the request was sent
            return {
                "status": "request_sent",
                "file_path": file_path,
                "element_name": element_name,
                "line_number": line_number,
                "message": "Dependency request sent to live test server. Check live server for results."
            }
        except Exception as e:
            return {"error": f"Failed to get dependencies: {str(e)}"}

    async def _get_dependents(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get what depends on a code element."""
        file_path = args["file_path"]
        element_name = args["element_name"]
        line_number = args.get("line_number")

        if not self.live_test_client:
            return {"error": "Live test server not available"}

        try:
            # Send request to live test server
            await self.live_test_client.get_dependents(file_path, element_name, line_number)

            return {
                "status": "request_sent",
                "file_path": file_path,
                "element_name": element_name,
                "line_number": line_number,
                "message": "Dependents request sent to live test server. Check live server for results."
            }
        except Exception as e:
            return {"error": f"Failed to get dependents: {str(e)}"}

    async def _get_element_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about a code element."""
        file_path = args["file_path"]
        element_name = args["element_name"]
        line_number = args.get("line_number")

        if not self.live_test_client:
            return {"error": "Live test server not available"}

        try:
            # Send both dependency and dependent requests
            await self.live_test_client.get_dependencies(file_path, element_name, line_number)
            await self.live_test_client.get_dependents(file_path, element_name, line_number)

            return {
                "status": "request_sent",
                "file_path": file_path,
                "element_name": element_name,
                "line_number": line_number,
                "message": "Element info requests sent to live test server. Check live server for results."
            }
        except Exception as e:
            return {"error": f"Failed to get element info: {str(e)}"}

    async def _find_dead_code(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Find potentially unused code."""
        file_path = args.get("file_path")

        if not self.live_test_client:
            return {"error": "Live test server not available"}

        try:
            # Send request to live test server
            await self.live_test_client.find_dead_code(file_path)

            return {
                "status": "request_sent",
                "file_path": file_path,
                "message": "Dead code detection request sent to live test server. Check live server for results."
            }
        except Exception as e:
            return {"error": f"Failed to find dead code: {str(e)}"}

    async def _get_dependency_graph(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get the complete dependency graph."""
        if not self.live_test_client:
            return {"error": "Live test server not available"}

        try:
            # Send request to live test server
            await self.live_test_client.get_dependency_graph()

            return {
                "status": "request_sent",
                "message": "Dependency graph request sent to live test server. Check live server for results."
            }
        except Exception as e:
            return {"error": f"Failed to get dependency graph: {str(e)}"}

    async def _analyze_impact(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the impact of changing a code element."""
        file_path = args["file_path"]
        element_name = args["element_name"]
        change_type = args.get("change_type", "modify")

        if not self.live_test_client:
            return {"error": "Live test server not available"}

        try:
            # Send request to live test server
            await self.live_test_client.analyze_impact(file_path, element_name, change_type)

            return {
                "status": "request_sent",
                "file_path": file_path,
                "element_name": element_name,
                "change_type": change_type,
                "message": "Impact analysis request sent to live test server. Check live server for results."
            }
        except Exception as e:
            return {"error": f"Failed to analyze impact: {str(e)}"}

    async def _find_related_code(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Find code related to a specific element."""
        file_path = args["file_path"]
        element_name = args["element_name"]
        depth = args.get("depth", 2)

        if not self.live_test_client:
            return {"error": "Live test server not available"}

        try:
            # Send both dependency and dependent requests to get related code
            await self.live_test_client.get_dependencies(file_path, element_name)
            await self.live_test_client.get_dependents(file_path, element_name)

            return {
                "status": "request_sent",
                "file_path": file_path,
                "element_name": element_name,
                "depth": depth,
                "message": "Related code requests sent to live test server. Check live server for results."
            }
        except Exception as e:
            return {"error": f"Failed to find related code: {str(e)}"}

    async def _get_navigation_suggestions(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get navigation suggestions after making changes."""
        changed_files = args["changed_files"]
        changed_elements = args.get("changed_elements", [])

        if not self.live_test_client:
            return {"error": "Live test server not available"}

        try:
            # For each changed file, get impact analysis
            for file_path in changed_files:
                await self.live_test_client.find_dead_code(file_path)

            # Get failing tests to suggest what to check
            await self.live_test_client.get_failing_tests()

            return {
                "status": "request_sent",
                "changed_files": changed_files,
                "changed_elements": changed_elements,
                "message": "Navigation analysis requests sent to live test server. Check live server for results."
            }
        except Exception as e:
            return {"error": f"Failed to get navigation suggestions: {str(e)}"}

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

    async def _get_dependency_graph_resource(self) -> Dict[str, Any]:
        """Get dependency graph as a resource."""
        if not self.live_test_client:
            return {
                "error": "Live test server not available",
                "elements": {},
                "dependencies": {},
                "message": "Start live test server to access dependency graph"
            }

        return {
            "status": "available",
            "description": "Complete project dependency graph showing code relationships",
            "capabilities": [
                "Find what code depends on what",
                "Identify dead/unused code",
                "Analyze impact of changes",
                "Navigate code relationships",
                "Smart test selection based on dependencies"
            ],
            "available_tools": [
                "get_dependencies - Find what an element depends on",
                "get_dependents - Find what depends on an element",
                "find_dead_code - Identify unused code",
                "analyze_impact - Assess change impact",
                "get_dependency_graph - Get complete graph",
                "find_related_code - Find related elements",
                "get_navigation_suggestions - Get navigation help"
            ],
            "message": "Use dependency graph tools to explore code relationships and get intelligent insights"
        }

    async def _get_failing_tests(self) -> Dict[str, Any]:
        """Get currently failing tests as a resource."""
        if not self.live_test_client:
            return {
                "error": "Live test server not available",
                "failing_tests": [],
                "message": "Start live test server to access test results"
            }

        return {
            "status": "available",
            "description": "Currently failing tests in the project",
            "capabilities": [
                "List all failing tests",
                "Show test failure details",
                "Track test history",
                "Identify flaky tests"
            ],
            "available_tools": [
                "get_failing_tests - Get list of failing tests",
                "run_tests - Run tests for a file",
                "run_test_at_line - Run specific test"
            ],
            "message": "Use get_failing_tests tool to retrieve current test failures"
        }

    async def _get_dead_code_resource(self) -> Dict[str, Any]:
        """Get dead code information as a resource."""
        if not self.live_test_client:
            return {
                "error": "Live test server not available",
                "dead_code": [],
                "message": "Start live test server to access dead code detection"
            }

        return {
            "status": "available",
            "description": "Potentially unused code in the project",
            "capabilities": [
                "Identify unused functions and methods",
                "Find unreferenced classes",
                "Detect orphaned code",
                "Suggest cleanup opportunities"
            ],
            "available_tools": [
                "find_dead_code - Detect unused code",
                "get_dependents - Check if code is used",
                "analyze_impact - Assess removal impact"
            ],
            "message": "Use find_dead_code tool to identify potentially unused code"
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
