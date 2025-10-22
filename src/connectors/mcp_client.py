"""
MCP (Model Context Protocol) Client for Composio Integration

This module provides an MCP client to communicate with Composio's MCP server,
replacing the direct SDK integration with a standardized protocol approach.
"""

import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class MCPTool:
    """Represents an MCP tool definition"""
    name: str
    description: str
    input_schema: Dict[str, Any]

@dataclass
class MCPResource:
    """Represents an MCP resource definition"""
    uri: str
    name: str
    description: str
    mime_type: str

class ComposioMCPClient:
    """
    MCP Client for Composio server integration
    
    Handles communication with Composio's MCP server using the standardized
    Model Context Protocol over HTTP with Server-Sent Events (SSE).
    """
    
    def __init__(self, server_url: str):
        """
        Initialize the MCP client
        
        Args:
            server_url: The Composio MCP server URL
        """
        self.server_url = server_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.connected = False
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
        
    async def connect(self):
        """Establish connection to the MCP server"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
            
        try:
            # Initialize MCP session
            await self._initialize_session()
            # Discover available tools and resources
            await self._discover_capabilities()
            self.connected = True
            logger.info(f"Successfully connected to MCP server: {self.server_url}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            await self.disconnect()
            raise
            
    async def disconnect(self):
        """Close connection to the MCP server"""
        if self.session:
            await self.session.close()
            self.session = None
        self.connected = False
        logger.info("Disconnected from MCP server")
        
    async def _initialize_session(self):
        """Initialize MCP session with handshake"""
        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {}
                },
                "clientInfo": {
                    "name": "composio-notion-connector",
                    "version": "1.0.0"
                }
            }
        }
        
        # Use the server URL directly since it already includes the MCP path
        async with self.session.post(
            self.server_url,
            json=init_payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
        ) as response:
            if response.status != 200:
                raise Exception(f"MCP initialization failed: {response.status}")
                
            # Check if response is Server-Sent Events (SSE)
            content_type = response.headers.get('Content-Type', '')
            if 'text/event-stream' in content_type:
                # Parse SSE response
                text = await response.text()
                # Extract JSON from SSE format (event: message\ndata: {...})
                lines = text.strip().split('\n')
                for line in lines:
                    if line.startswith('data: '):
                        json_data = line[6:]  # Remove 'data: ' prefix
                        result = json.loads(json_data)
                        if "error" in result:
                            raise Exception(f"MCP initialization error: {result['error']}")
                        break
            else:
                result = await response.json()
                if "error" in result:
                    raise Exception(f"MCP initialization error: {result['error']}")
                
            logger.info("MCP session initialized successfully")
            
    async def _discover_capabilities(self):
        """Discover available tools and resources from the MCP server"""
        # Discover tools
        tools_payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        # Use the server URL directly since it already includes the MCP path
        async with self.session.post(
            self.server_url,
            json=tools_payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
        ) as response:
            if response.status == 200:
                # Check if response is Server-Sent Events (SSE)
                content_type = response.headers.get('Content-Type', '')
                if 'text/event-stream' in content_type:
                    # Parse SSE response
                    text = await response.text()
                    # Extract JSON from SSE format (event: message\ndata: {...})
                    lines = text.strip().split('\n')
                    for line in lines:
                        if line.startswith('data: '):
                            json_data = line[6:]  # Remove 'data: ' prefix
                            result = json.loads(json_data)
                            break
                else:
                    result = await response.json()
                    
                if "result" in result and "tools" in result["result"]:
                    for tool_def in result["result"]["tools"]:
                        tool = MCPTool(
                            name=tool_def["name"],
                            description=tool_def["description"],
                            input_schema=tool_def["inputSchema"]
                        )
                        self.tools[tool.name] = tool
                        
        logger.info(f"Discovered {len(self.tools)} tools from MCP server")
        
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool on the MCP server
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments to pass to the tool
            
        Returns:
            Tool execution result
        """
        if not self.connected:
            raise Exception("MCP client not connected")
            
        if tool_name not in self.tools:
            raise Exception(f"Tool '{tool_name}' not available")
            
        execute_payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        # Use the server URL directly since it already includes the MCP path
        async with self.session.post(
            self.server_url,
            json=execute_payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
        ) as response:
            if response.status != 200:
                raise Exception(f"Tool execution failed: {response.status}")
                
            # Check if response is Server-Sent Events (SSE)
            content_type = response.headers.get('Content-Type', '')
            if 'text/event-stream' in content_type:
                # Parse SSE response
                text = await response.text()
                # Extract JSON from SSE format (event: message\ndata: {...})
                lines = text.strip().split('\n')
                for line in lines:
                    if line.startswith('data: '):
                        json_data = line[6:]  # Remove 'data: ' prefix
                        result = json.loads(json_data)
                        break
            else:
                result = await response.json()
                
            if "error" in result:
                raise Exception(f"Tool execution error: {result['error']}")
            
            # Handle different response structures from Composio MCP
            if "result" in result:
                return result["result"]
            elif "content" in result and isinstance(result["content"], list):
                # Handle content array response structure
                for content_item in result["content"]:
                    if content_item.get("type") == "text" and "text" in content_item:
                        try:
                            # Parse the JSON text content
                            json_text = content_item["text"]
                            parsed_data = json.loads(json_text)
                            return parsed_data
                        except json.JSONDecodeError:
                            continue
                # If we can't parse any content, check if there's an error
                if result.get("isError", False):
                    raise Exception(f"MCP server error: {result}")
                return result  # Return original if can't parse
            else:
                return result
            
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return list(self.tools.keys())
        
    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get the input schema for a specific tool"""
        if tool_name in self.tools:
            return self.tools[tool_name].input_schema
        return None

class SyncComposioMCPClient:
    """
    Synchronous wrapper for ComposioMCPClient
    
    Provides a synchronous interface for easier integration with existing code.
    """
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self._client: Optional[ComposioMCPClient] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
    def connect(self):
        """Establish connection to the MCP server (synchronous)"""
        try:
            # Try to get the current event loop
            self._loop = asyncio.get_event_loop()
            if self._loop.is_running():
                # If loop is already running, we can't use run_until_complete
                # Instead, we'll create a task and wait for it
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._connect_async)
                    future.result(timeout=30)  # 30 second timeout
            else:
                # Loop exists but not running, we can use it
                self._client = ComposioMCPClient(self.server_url)
                self._loop.run_until_complete(self._client.connect())
        except RuntimeError:
            # No event loop exists, create a new one
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._client = ComposioMCPClient(self.server_url)
            self._loop.run_until_complete(self._client.connect())
    
    def _connect_async(self):
        """Helper method to connect asynchronously in a new thread"""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            self._client = ComposioMCPClient(self.server_url)
            loop.run_until_complete(self._client.connect())
            self._loop = loop
        finally:
            # Don't close the loop here as we need it for future operations
            pass
        
    def disconnect(self):
        """Close connection to the MCP server (synchronous)"""
        if self._client and self._loop:
            try:
                self._loop.run_until_complete(self._client.disconnect())
            except Exception as e:
                logger.error(f"Error during MCP client disconnect: {e}")
            finally:
                try:
                    self._loop.close()
                except Exception as e:
                    logger.error(f"Error closing event loop: {e}")
                self._client = None
                self._loop = None
            
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on the MCP server (synchronous)"""
        if not self._client or not self._loop:
            raise Exception("MCP client not connected")
        
        # Handle event loop conflicts by using a thread-based approach
        try:
            # First try the simple approach
            return self._loop.run_until_complete(
                self._client.execute_tool(tool_name, arguments)
            )
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e) or "Cannot run the event loop while another loop is running" in str(e):
                # If we're in an async context, use a thread to run the async code
                import concurrent.futures
                import threading
                
                def run_in_thread():
                    # Create a new event loop for this thread
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        # Create a new client instance for this thread
                        thread_client = ComposioMCPClient(self.server_url)
                        result = new_loop.run_until_complete(thread_client.connect())
                        result = new_loop.run_until_complete(
                            thread_client.execute_tool(tool_name, arguments)
                        )
                        new_loop.run_until_complete(thread_client.disconnect())
                        return result
                    finally:
                        new_loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    return future.result(timeout=30)  # 30 second timeout
            else:
                raise
        
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names (synchronous)"""
        if not self._client:
            raise Exception("MCP client not connected")
        return self._client.get_available_tools()
        
    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get the input schema for a specific tool (synchronous)"""
        if not self._client:
            raise Exception("MCP client not connected")
        return self._client.get_tool_schema(tool_name)
        
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()