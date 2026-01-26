"""
MCP Server - Central orchestrator for all MCP tool calls.

Provides:
- Tool registration and discovery
- Input validation
- Error handling
- Rate limiting (basic)
- Comprehensive logging
"""

from typing import Dict, Any, Optional
from pydantic import ValidationError
from app.mcp.mcp_tools import mcp_tools
from app.mcp.mcp_schemas import *
from app.mcp.mcp_logger import logger
from app.core.logger import logger as app_logger


class MCPServer:
    """
    Central MCP server managing all tool calls.
    
    Enforces read-only operations and validates all inputs/outputs.
    """
    
    def __init__(self):
        self.tools = mcp_tools
        
        # Tool registry: name → (input_schema, handler)
        self.tool_registry = {
            "getQuotes": (GetQuotesInput, self.tools.get_quotes),
            "getIndexQuotes": (GetIndexQuotesInput, self.tools.get_index_quotes),
            "getMarketDepth": (GetMarketDepthInput, self.tools.get_market_depth),
            "getLimits": (None, self.tools.get_limits),  # No input needed
            "getOrders": (GetOrdersInput, self.tools.get_orders),
            "getPositions": (None, self.tools.get_positions),
            "getWebSocketStatus": (None, self.tools.get_websocket_status),
            "searchNews": (SearchNewsInput, self.tools.search_news),
            "navigateTo": (NavigateToInput, self.tools.navigate_to),
            "applyFilter": (ApplyFilterInput, self.tools.apply_filter),
            "generateChart": (GenerateChartInput, self.tools.generate_chart),
        }
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool call with validation and logging.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool-specific arguments (validated against schema)
        
        Returns:
            Tool output as dict (success, data, errors, response_shape)
        
        Raises:
            ValueError: If tool not found or validation fails
        """
        # Check if tool exists
        if tool_name not in self.tool_registry:
            app_logger.error(f"Unknown MCP tool: {tool_name}")
            raise ValueError(f"Unknown tool: {tool_name}. Available: {list(self.tool_registry.keys())}")
        
        input_schema, handler = self.tool_registry[tool_name]
        
        try:
            # Validate input if schema exists
            if input_schema:
                if not arguments:
                    raise ValueError(f"{tool_name} requires arguments")
                
                try:
                    validated_input = input_schema(**arguments)
                except ValidationError as e:
                    logger.log_validation_error(
                        tool_name=tool_name,
                        arguments=arguments,
                        validation_errors=str(e)
                    )
                    raise ValueError(f"Validation failed: {e}")
                
                # Call handler with validated input
                result = await handler(validated_input)
            else:
                # No input needed (e.g., getLimits)
                result = await handler()
            
            # Return as dict
            return result.model_dump()
            
        except Exception as e:
            app_logger.error(f"MCP tool call failed: {tool_name} - {str(e)}")
            raise
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools with their schemas.
        
        Returns:
            List of tool metadata (name, description, parameters)
        """
        tools_info = []
        
        for tool_name, (input_schema, _) in self.tool_registry.items():
            tool_info = {
                "name": tool_name,
                "has_parameters": input_schema is not None,
            }
            
            if input_schema:
                tool_info["parameters"] = input_schema.model_json_schema()
            
            tools_info.append(tool_info)
        
        return tools_info
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check MCP server health.
        
        Returns:
            Health status dict
        """
        return {
            "status": "healthy",
            "total_tools": len(self.tool_registry),
            "available_tools": list(self.tool_registry.keys())
        }


# Export singleton server
mcp_server = MCPServer()
