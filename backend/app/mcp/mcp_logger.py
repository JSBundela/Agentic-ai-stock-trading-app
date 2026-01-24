"""
MCP Logger - Centralized logging for MCP tool calls with full observability.

Logs every tool invocation with arguments, response shape, latency, and errors.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from app.mcp.mcp_schemas import MCPToolCallLog

# Create logs directory if it doesn't exist
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Configure MCP-specific logger
mcp_logger = logging.getLogger("mcp_tools")
mcp_logger.setLevel(logging.INFO)

# File handler for MCP tool calls
mcp_file_handler = logging.FileHandler(LOG_DIR / "mcp_tool_calls.log")
mcp_file_handler.setLevel(logging.INFO)

# Format: JSON lines for easy parsing
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "tool_data"):
            log_data.update(record.tool_data)
        return json.dumps(log_data)

mcp_file_handler.setFormatter(JSONFormatter())
mcp_logger.addHandler(mcp_file_handler)

# Console handler for development
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s - MCP - %(levelname)s - %(message)s'
))
mcp_logger.addHandler(console_handler)


class MCPLogger:
    """
    Centralized logger for MCP tool interactions.
    
    Provides full trace visibility: tool_name → args → response → latency.
    """
    
    @staticmethod
    def log_tool_call(
        tool_name: str,
        arguments: Dict[str, Any],
        success: bool,
        response_shape: Dict[str, Any],
        latency_ms: float,
        error: Optional[str] = None
    ) -> None:
        """
        Log a complete MCP tool call with all metadata.
        
        Args:
            tool_name: Name of the MCP tool invoked
            arguments: Input arguments passed to the tool
            success: Whether the tool call succeeded
            response_shape: Metadata about the response (count, fields)
            latency_ms: Execution time in milliseconds
            error: Error message if failed
        """
        log_entry = MCPToolCallLog(
            timestamp=datetime.utcnow(),
            tool_name=tool_name,
            arguments=arguments,
            success=success,
            response_shape=response_shape,
            latency_ms=latency_ms,
            error=error
        )
        
        # Create log record with extra data
        tool_data = log_entry.model_dump()
        tool_data["timestamp"] = tool_data["timestamp"].isoformat()
        
        if success:
            mcp_logger.info(
                f"Tool: {tool_name} | Latency: {latency_ms:.2f}ms | Success: True",
                extra={"tool_data": tool_data}
            )
        else:
            mcp_logger.error(
                f"Tool: {tool_name} | Latency: {latency_ms:.2f}ms | Error: {error}",
                extra={"tool_data": tool_data}
            )
    
    @staticmethod
    def log_validation_error(
        tool_name: str,
        arguments: Dict[str, Any],
        validation_errors: str
    ) -> None:
        """Log input validation failures."""
        mcp_logger.warning(
            f"Validation failed for {tool_name}: {validation_errors}",
            extra={
                "tool_data": {
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "validation_errors": validation_errors,
                    "success": False,
                }
            }
        )
    
    @staticmethod
    def log_rate_limit(tool_name: str) -> None:
        """Log rate limiting events."""
        mcp_logger.warning(
            f"Rate limit exceeded for {tool_name}",
            extra={
                "tool_data": {
                    "tool_name": tool_name,
                    "event": "rate_limit_exceeded",
                }
            }
        )


# Export singleton logger
logger = MCPLogger()
