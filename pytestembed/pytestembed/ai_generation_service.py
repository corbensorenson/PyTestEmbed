#!/usr/bin/env python3
"""
PyTestEmbed AI Generation Service

Dedicated service for AI-powered code generation, enhancement, and refactoring.
Handles lightbulb quick fixes from IDEs and provides structured AI responses.
"""

import asyncio
import json
import sys
import time
import websockets
from pathlib import Path
from typing import Dict, Any, Optional

from .ai_service import AIService, AIGenerationRequest
from .smart_generator import SmartCodeGenerator, GenerationRequest, CodeContext
from .parser import PyTestEmbedParser
from .config_manager import ConfigManager


class AIGenerationService:
    """Dedicated AI generation service for PyTestEmbed."""

    def __init__(self, workspace: str = ".", port: int = 8771, dependency_service_port: int = 8769):
        self.workspace_path = Path(workspace).resolve()
        self.port = port
        self.dependency_service_port = dependency_service_port
        self.clients = set()

        # Initialize AI components
        self.config_manager = ConfigManager()
        self.ai_service = AIService(str(self.workspace_path))
        self.smart_generator = SmartCodeGenerator()
        self.parser = PyTestEmbedParser()

        # Dependency service process (will be started if needed)
        self.dependency_service_process = None
        
        print(f"🤖 AI Generation Service initialized")
        print(f"📁 Workspace: {self.workspace_path}")
        print(f"🔌 Port: {self.port}")

    async def ensure_dependency_service_running(self):
        """Ensure dependency service is running for context gathering."""
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

    async def handle_client(self, websocket, path):
        """Handle client connections."""
        self.clients.add(websocket)
        client_addr = websocket.remote_address
        print(f"🔗 AI Generation client connected: {client_addr}")
        
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            print(f"🔌 AI Generation client disconnected: {client_addr}")
        except Exception as e:
            print(f"⚠️ Error handling AI Generation client {client_addr}: {e}")
        finally:
            self.clients.discard(websocket)

    async def handle_message(self, websocket, message):
        """Handle incoming messages from clients."""
        try:
            data = json.loads(message)
            command = data.get('command')
            
            if command == 'health_check':
                await self.handle_health_check(websocket)
            elif command == 'ai_generation':
                await self.handle_ai_generation(websocket, data)
            else:
                await self.send_error(websocket, f"Unknown command: {command}")
                
        except json.JSONDecodeError:
            await self.send_error(websocket, "Invalid JSON message")
        except Exception as e:
            await self.send_error(websocket, f"Error processing message: {e}")

    async def handle_health_check(self, websocket):
        """Handle health check request."""
        try:
            await websocket.send(json.dumps({
                'type': 'health_check',
                'status': 'healthy',
                'service': 'ai_generation_service',
                'connected_clients': len(self.clients),
                'ai_available': self.ai_service.ai_manager.is_ai_available(),
                'timestamp': time.time()
            }))
        except Exception as e:
            print(f"⚠️ Error in health check: {e}")

    async def handle_ai_generation(self, websocket, data):
        """Handle AI generation requests from IDEs."""
        try:
            action = data.get('action')
            block_type = data.get('block_type')
            file_path = data.get('file_path')
            line_number = data.get('line_number')
            
            if not all([action, block_type, file_path, line_number]):
                await self.send_error(websocket, "Missing required parameters")
                return
            
            print(f"🤖 Processing {action} for {block_type} block at {file_path}:{line_number}")
            
            # Send progress update
            await websocket.send(json.dumps({
                'type': 'ai_generation_progress',
                'message': f"Starting {action}..."
            }))
            
            # Process the request based on action type
            result = await self.process_ai_action(action, block_type, file_path, line_number)
            
            if result['success']:
                await websocket.send(json.dumps({
                    'type': 'ai_generation_result',
                    'success': True,
                    'action': action,
                    'block_type': block_type,
                    'content': result['content'],
                    'provider_used': result.get('provider_used'),
                    'fallback_used': result.get('fallback_used', False)
                }))
            else:
                await websocket.send(json.dumps({
                    'type': 'ai_generation_result',
                    'success': False,
                    'action': action,
                    'block_type': block_type,
                    'error': result['error']
                }))
                
        except Exception as e:
            print(f"⚠️ Error in AI generation: {e}")
            await self.send_error(websocket, f"AI generation failed: {e}")

    async def process_ai_action(self, action: str, block_type: str, file_path: str, line_number: int) -> Dict[str, Any]:
        """Process different AI generation actions."""
        try:
            # Map actions to generation types
            action_mapping = {
                # Test block actions
                'rewrite_test_block': 'test',
                'add_another_test': 'test',
                'generate_edge_case_tests': 'test',
                'improve_test_coverage': 'test',
                
                # Doc block actions
                'rewrite_doc_block': 'doc',
                'add_more_detail': 'doc',
                'add_examples': 'doc',
                'improve_clarity': 'doc'
            }
            
            generation_type = action_mapping.get(action)
            if not generation_type:
                return {'success': False, 'error': f"Unknown action: {action}"}
            
            # Create AI generation request
            ai_request = AIGenerationRequest(
                file_path=file_path,
                line_number=line_number,
                generation_type=generation_type,
                context={'action': action, 'block_type': block_type}
            )
            
            # Generate content using AI service
            response = await self.ai_service.generate_content(ai_request)
            
            if response.success:
                # Apply the generated content to the file
                await self.apply_generated_content(
                    file_path, line_number, response.content, action, block_type
                )
                
                return {
                    'success': True,
                    'content': response.content,
                    'provider_used': response.provider_used,
                    'fallback_used': response.fallback_used
                }
            else:
                return {'success': False, 'error': response.error}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def apply_generated_content(self, file_path: str, line_number: int, content: str, action: str, block_type: str):
        """Apply generated content to the file."""
        try:
            # Read the current file
            full_path = self.workspace_path / file_path
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find the block to modify
            block_start, block_end = self.find_block_boundaries(lines, line_number, block_type)
            
            if action.startswith('rewrite_'):
                # Replace the entire block
                new_lines = lines[:block_start] + [content + '\n'] + lines[block_end + 1:]
            elif action.startswith('add_'):
                # Add content to the existing block
                existing_content = ''.join(lines[block_start:block_end + 1]).strip()
                combined_content = f"{existing_content}\n{content}"
                new_lines = lines[:block_start] + [combined_content + '\n'] + lines[block_end + 1:]
            else:
                # Default: replace the block
                new_lines = lines[:block_start] + [content + '\n'] + lines[block_end + 1:]
            
            # Write the modified file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
                
            print(f"✅ Applied {action} to {file_path}:{line_number}")
            
        except Exception as e:
            print(f"⚠️ Error applying generated content: {e}")
            raise

    def find_block_boundaries(self, lines: list, line_number: int, block_type: str) -> tuple:
        """Find the start and end lines of a test: or doc: block."""
        # Convert to 0-based indexing
        start_line = line_number - 1
        
        # Find the actual block start (should be the test: or doc: line)
        block_start = start_line
        for i in range(start_line, max(0, start_line - 10), -1):
            line_text = lines[i].strip()
            if line_text.startswith(f'{block_type}:'):
                block_start = i
                break
        
        # Find block end (next line with same or less indentation)
        base_indent = len(lines[block_start]) - len(lines[block_start].lstrip())
        block_end = block_start
        
        for i in range(block_start + 1, len(lines)):
            line = lines[i]
            line_text = line.strip()
            
            # Skip empty lines
            if not line_text:
                continue
                
            # If we hit a line with same or less indentation, we've found the end
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= base_indent:
                break
                
            block_end = i
        
        return block_start, block_end

    async def send_error(self, websocket, error_message: str):
        """Send error message to client."""
        try:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': error_message
            }))
        except Exception as e:
            print(f"⚠️ Error sending error message: {e}")

    async def run(self):
        """Run the AI generation service."""
        print(f"🚀 Starting AI Generation Service on port {self.port}")

        # Ensure dependency service is running (AI generation depends on it for context)
        if not await self.ensure_dependency_service_running():
            print("❌ Failed to start dependency service, AI generation may have limited context")

        try:
            async with websockets.serve(self.handle_client, "localhost", self.port):
                print(f"🎯 AI Generation Service ready on ws://localhost:{self.port}")
                print("🤖 AI-powered code generation available")
                await asyncio.Future()  # Run forever

        except Exception as e:
            print(f"❌ Failed to start AI Generation Service: {e}")


async def main():
    """Main entry point for AI generation service."""
    if len(sys.argv) < 2:
        print("Usage: python -m pytestembed.ai_generation_service <workspace_path> [port]")
        sys.exit(1)
    
    workspace = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8771
    
    service = AIGenerationService(workspace, port)
    await service.run()


if __name__ == "__main__":
    asyncio.run(main())
