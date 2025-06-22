"""
AI Service for PyTestEmbed

This module provides a centralized AI service that handles all LLM interactions
for test and documentation generation. It's completely IDE-agnostic and can be
used by any editor or IDE through simple API calls.
"""

import asyncio
import json
import time
import websockets
import websockets.server
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .ai_integration import AIManager
from .ai_test_generator import AITestGenerator
from .ai_doc_enhancer import AIDocumentationEnhancer
from .smart_generator import SmartGenerator
from .parser import PyTestEmbedParser


@dataclass
class AIGenerationRequest:
    """Request for AI-powered generation."""
    file_path: str
    line_number: int
    generation_type: str  # 'test', 'doc', 'both'
    ai_provider: Optional[str] = None
    context: Optional[Dict] = None


@dataclass
class AIGenerationResponse:
    """Response from AI generation."""
    success: bool
    content: str
    generation_type: str
    error: Optional[str] = None
    provider_used: Optional[str] = None
    fallback_used: bool = False


class AIService:
    """Centralized AI service for PyTestEmbed."""
    
    def __init__(self, workspace_path: str, port: int = 8771):
        self.workspace_path = Path(workspace_path)
        self.port = port
        self.server = None
        self.clients = set()
        
        # Initialize AI components
        self.ai_manager = AIManager()
        self.parser = PyTestEmbedParser()
        self.test_generator = AITestGenerator(ai_provider="lmstudio")
        self.doc_enhancer = AIDocumentationEnhancer(ai_provider="lmstudio")
        self.smart_generator = SmartGenerator(str(workspace_path))
        
        # Default AI provider preference
        self.default_provider = "lmstudio"  # User prefers LMStudio over Ollama
        
        print(f"🤖 AI Service initialized for workspace: {workspace_path}")
    
    async def start_server(self):
        """Start the AI service WebSocket server."""
        async def handle_client(websocket, path):
            self.clients.add(websocket)
            print(f"🤖 AI Service client connected: {websocket.remote_address}")
            
            try:
                async for message in websocket:
                    await self.handle_message(websocket, message)
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                self.clients.discard(websocket)
                print(f"🤖 AI Service client disconnected")
        
        self.server = await websockets.serve(handle_client, "localhost", self.port)
        print(f"🤖 AI Service running at ws://localhost:{self.port}")
    
    async def handle_message(self, websocket, message: str):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)
            command = data.get('command')
            
            if command == 'generate_test_block':
                await self.handle_generate_test_block(websocket, data)
            elif command == 'generate_doc_block':
                await self.handle_generate_doc_block(websocket, data)
            elif command == 'generate_both_blocks':
                await self.handle_generate_both_blocks(websocket, data)
            elif command == 'convert_file_to_pytestembed':
                await self.handle_convert_file(websocket, data)
            elif command == 'get_ai_providers':
                await self.handle_get_ai_providers(websocket)
            elif command == 'set_ai_provider':
                await self.handle_set_ai_provider(websocket, data)
            elif command == 'get_ai_status':
                await self.handle_get_ai_status(websocket)
            else:
                await self.send_error(websocket, f"Unknown command: {command}")
                
        except Exception as e:
            await self.send_error(websocket, f"Error processing message: {str(e)}")
    
    async def handle_generate_test_block(self, websocket, data: Dict):
        """Generate test block for a function/method."""
        try:
            request = AIGenerationRequest(
                file_path=data['file_path'],
                line_number=data['line_number'],
                generation_type='test',
                ai_provider=data.get('ai_provider', self.default_provider),
                context=data.get('context')
            )
            
            response = await self.generate_content(request)
            
            await websocket.send(json.dumps({
                'type': 'test_block_generated',
                'success': response.success,
                'content': response.content,
                'file_path': request.file_path,
                'line_number': request.line_number,
                'provider_used': response.provider_used,
                'fallback_used': response.fallback_used,
                'error': response.error,
                'timestamp': time.time()
            }))
            
        except Exception as e:
            await self.send_error(websocket, f"Error generating test block: {str(e)}")
    
    async def handle_generate_doc_block(self, websocket, data: Dict):
        """Generate documentation block for a function/method."""
        try:
            request = AIGenerationRequest(
                file_path=data['file_path'],
                line_number=data['line_number'],
                generation_type='doc',
                ai_provider=data.get('ai_provider', self.default_provider),
                context=data.get('context')
            )
            
            response = await self.generate_content(request)
            
            await websocket.send(json.dumps({
                'type': 'doc_block_generated',
                'success': response.success,
                'content': response.content,
                'file_path': request.file_path,
                'line_number': request.line_number,
                'provider_used': response.provider_used,
                'fallback_used': response.fallback_used,
                'error': response.error,
                'timestamp': time.time()
            }))
            
        except Exception as e:
            await self.send_error(websocket, f"Error generating doc block: {str(e)}")
    
    async def handle_generate_both_blocks(self, websocket, data: Dict):
        """Generate both test and doc blocks for a function/method."""
        try:
            request = AIGenerationRequest(
                file_path=data['file_path'],
                line_number=data['line_number'],
                generation_type='both',
                ai_provider=data.get('ai_provider', self.default_provider),
                context=data.get('context')
            )
            
            response = await self.generate_content(request)
            
            await websocket.send(json.dumps({
                'type': 'both_blocks_generated',
                'success': response.success,
                'content': response.content,
                'file_path': request.file_path,
                'line_number': request.line_number,
                'provider_used': response.provider_used,
                'fallback_used': response.fallback_used,
                'error': response.error,
                'timestamp': time.time()
            }))
            
        except Exception as e:
            await self.send_error(websocket, f"Error generating both blocks: {str(e)}")
    
    async def handle_convert_file(self, websocket, data: Dict):
        """Convert a standard Python file to PyTestEmbed format."""
        try:
            file_path = data['file_path']
            full_path = self.workspace_path / file_path
            
            # Use smart generator for file conversion
            converted_content = self.smart_generator.convert_file_to_pytestembed(str(full_path))
            
            await websocket.send(json.dumps({
                'type': 'file_converted',
                'success': True,
                'content': converted_content,
                'file_path': file_path,
                'timestamp': time.time()
            }))
            
        except Exception as e:
            await self.send_error(websocket, f"Error converting file: {str(e)}")
    
    async def handle_get_ai_providers(self, websocket):
        """Get list of available AI providers."""
        try:
            providers = {
                'lmstudio': {
                    'name': 'LMStudio',
                    'available': self.ai_manager.providers.get('lmstudio', {}).get('available', False),
                    'preferred': True,  # User preference
                    'models': ['Qwen 14B', 'CodeLlama', 'Custom']
                },
                'ollama': {
                    'name': 'Ollama',
                    'available': self.ai_manager.providers.get('ollama', {}).get('available', False),
                    'preferred': False,
                    'models': ['codellama', 'llama2', 'mistral']
                }
            }
            
            await websocket.send(json.dumps({
                'type': 'ai_providers',
                'providers': providers,
                'current_provider': self.default_provider,
                'timestamp': time.time()
            }))
            
        except Exception as e:
            await self.send_error(websocket, f"Error getting AI providers: {str(e)}")
    
    async def handle_set_ai_provider(self, websocket, data: Dict):
        """Set the default AI provider."""
        try:
            provider = data['provider']
            if provider in ['lmstudio', 'ollama']:
                self.default_provider = provider
                
                # Update all AI components
                self.test_generator.ai_provider = provider
                self.doc_enhancer.ai_provider = provider
                
                await websocket.send(json.dumps({
                    'type': 'ai_provider_set',
                    'success': True,
                    'provider': provider,
                    'timestamp': time.time()
                }))
            else:
                await self.send_error(websocket, f"Unknown AI provider: {provider}")
                
        except Exception as e:
            await self.send_error(websocket, f"Error setting AI provider: {str(e)}")
    
    async def handle_get_ai_status(self, websocket):
        """Get AI service status and availability."""
        try:
            status = {
                'ai_available': self.ai_manager.is_ai_available(),
                'current_provider': self.default_provider,
                'lmstudio_available': self.ai_manager.providers.get('lmstudio', {}).get('available', False),
                'ollama_available': self.ai_manager.providers.get('ollama', {}).get('available', False),
                'workspace_path': str(self.workspace_path),
                'connected_clients': len(self.clients)
            }
            
            await websocket.send(json.dumps({
                'type': 'ai_status',
                'status': status,
                'timestamp': time.time()
            }))
            
        except Exception as e:
            await self.send_error(websocket, f"Error getting AI status: {str(e)}")
    
    async def generate_content(self, request: AIGenerationRequest) -> AIGenerationResponse:
        """Generate content using AI based on the request."""
        try:
            # Parse the file to get context
            full_path = self.workspace_path / request.file_path
            parsed = self.parser.parse_file(str(full_path))
            
            # Find the function/method at the specified line
            target_function = None
            for func in parsed.functions:
                if func.line_number == request.line_number:
                    target_function = func
                    break
            
            if not target_function:
                # Check classes and methods
                for cls in parsed.classes:
                    if cls.line_number == request.line_number:
                        target_function = cls
                        break
                    for method in cls.methods:
                        if method.line_number == request.line_number:
                            target_function = method
                            break
            
            if not target_function:
                return AIGenerationResponse(
                    success=False,
                    content="",
                    generation_type=request.generation_type,
                    error="No function or method found at specified line"
                )
            
            # Generate content based on type
            if request.generation_type == 'test':
                content = await self._generate_test_content(target_function, request.ai_provider)
            elif request.generation_type == 'doc':
                content = await self._generate_doc_content(target_function, request.ai_provider)
            elif request.generation_type == 'both':
                test_content = await self._generate_test_content(target_function, request.ai_provider)
                doc_content = await self._generate_doc_content(target_function, request.ai_provider)
                content = f"{test_content}\n{doc_content}"
            else:
                return AIGenerationResponse(
                    success=False,
                    content="",
                    generation_type=request.generation_type,
                    error=f"Unknown generation type: {request.generation_type}"
                )
            
            return AIGenerationResponse(
                success=True,
                content=content,
                generation_type=request.generation_type,
                provider_used=request.ai_provider or self.default_provider,
                fallback_used=not self.ai_manager.is_ai_available()
            )
            
        except Exception as e:
            return AIGenerationResponse(
                success=False,
                content="",
                generation_type=request.generation_type,
                error=str(e)
            )
    
    async def _generate_test_content(self, function_info, ai_provider: Optional[str]) -> str:
        """Generate test content for a function."""
        # Convert function info to dict format expected by test generator
        func_dict = {
            'name': function_info.name,
            'line_number': function_info.line_number,
            'parameters': getattr(function_info, 'parameters', []),
            'docstring': getattr(function_info, 'docstring', ''),
            'body': getattr(function_info, 'body', '')
        }
        
        test_lines = self.test_generator.generate_tests(func_dict, 'function')
        return '\n'.join(test_lines)
    
    async def _generate_doc_content(self, function_info, ai_provider: Optional[str]) -> str:
        """Generate documentation content for a function."""
        # Convert function info to dict format expected by doc enhancer
        func_dict = {
            'name': function_info.name,
            'line_number': function_info.line_number,
            'parameters': getattr(function_info, 'parameters', []),
            'docstring': getattr(function_info, 'docstring', ''),
            'body': getattr(function_info, 'body', '')
        }
        
        doc_lines = self.doc_enhancer.generate_documentation(func_dict, 'function')
        return '\n'.join(doc_lines)
    
    async def send_error(self, websocket, message: str):
        """Send error message to client."""
        await websocket.send(json.dumps({
            'type': 'error',
            'message': message,
            'timestamp': time.time()
        }))
    
    async def stop_server(self):
        """Stop the AI service server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            print("🤖 AI Service stopped")


async def main():
    """Run the AI service."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m pytestembed.ai_service <workspace_path>")
        sys.exit(1)
    
    workspace_path = sys.argv[1]
    service = AIService(workspace_path)
    
    try:
        await service.start_server()
        print("🤖 AI Service is running. Press Ctrl+C to stop.")
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        print("\n🤖 Shutting down AI Service...")
        await service.stop_server()


if __name__ == "__main__":
    asyncio.run(main())
