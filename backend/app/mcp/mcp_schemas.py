"""
MCP Schemas - Pydantic validation models for all MCP tools.

All schemas enforce strict read-only operations with comprehensive validation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime


# ===========================
# Input Schemas
# ===========================

class GetQuotesInput(BaseModel):
    """Input schema for getQuotes tool."""
    symbols: List[str] = Field(
        ..., 
        min_length=1, 
        max_length=20,
        description="List of trading symbols (max 20)"
    )
    
    @field_validator('symbols')
    @classmethod
    def validate_symbols(cls, v):
        if not all(isinstance(s, str) and len(s) > 0 for s in v):
            raise ValueError("All symbols must be non-empty strings")
        return v


class GetIndexQuotesInput(BaseModel):
    """Input schema for getIndexQuotes tool."""
    index: Literal["NIFTY 50", "NIFTY BANK", "SENSEX", "NIFTY IT"] = Field(
        ...,
        description="Index name"
    )


class GetMarketDepthInput(BaseModel):
    """Input schema for getMarketDepth tool."""
    symbol: str = Field(
        ...,
        min_length=1,
        description="Trading symbol for market depth"
    )


class GetOrdersInput(BaseModel):
    """Input schema for getOrders tool."""
    status: Optional[Literal["COMPLETE", "REJECTED", "PENDING", "TRIGGER PENDING"]] = Field(
        None,
        description="Filter by order status"
    )


class SearchNewsInput(BaseModel):
    """Input schema for searchNews tool."""
    query: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="News search query"
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of results to return"
    )


class NavigateToInput(BaseModel):
    """Input schema for navigateTo tool."""
    route: Literal[
        "/dashboard",        # Main Dashboard
        "/portfolio",        # Portfolio/Holdings page
        "/funds",            # Funds & Limits
        "/order-book",       # Order Book (view orders)
        "/order-entry",      # Place Order page
        "/orders",           # Alias for order-book
        "/positions",        # Alias for portfolio
        "/holdings",         # Alias for portfolio
        "/market-watch"      # Market Watch
    ] = Field(
        ...,
        description="Target route for navigation"
    )


class ApplyFilterInput(BaseModel):
    """Input schema for applyFilter tool."""
    params: Dict[str, Any] = Field(
        ...,
        description="Filter parameters (e.g., {'status': 'REJECTED', 'product': 'MIS'})"
    )


# ===========================
# Output Schemas
# ===========================

class QuoteData(BaseModel):
    """Individual quote data structure."""
    symbol: str
    ltp: Optional[float] = None
    change: Optional[float] = None
    percent_change: Optional[float] = None
    volume: Optional[int] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None


class GetQuotesOutput(BaseModel):
    """Output schema for getQuotes tool."""
    success: bool
    count: int
    data: List[QuoteData]
    errors: Optional[List[str]] = None
    response_shape: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata about response structure"
    )


class IndexQuoteData(BaseModel):
    """Index quote data structure."""
    index_name: str
    ltp: Optional[float] = None
    change: Optional[float] = None
    percent_change: Optional[float] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None


class GetIndexQuotesOutput(BaseModel):
    """Output schema for getIndexQuotes tool."""
    success: bool
    data: IndexQuoteData
    response_shape: Dict[str, Any] = Field(default_factory=dict)


class MarketDepthLevel(BaseModel):
    """Market depth bid/ask level."""
    price: float
    quantity: int
    orders: int


class MarketDepthData(BaseModel):
    """Market depth data structure."""
    symbol: str
    bids: List[MarketDepthLevel] = Field(default_factory=list)
    asks: List[MarketDepthLevel] = Field(default_factory=list)
    timestamp: Optional[str] = None
    error: Optional[str] = None


class GetMarketDepthOutput(BaseModel):
    """Output schema for getMarketDepth tool."""
    success: bool
    data: MarketDepthData
    response_shape: Dict[str, Any] = Field(default_factory=dict)


class LimitsData(BaseModel):
    """User limits/funds data structure."""
    cash_available: Optional[float] = None
    collateral: Optional[float] = None
    margin_used: Optional[float] = None
    total_limit: Optional[float] = None
    error: Optional[str] = None


class GetLimitsOutput(BaseModel):
    """Output schema for getLimits tool."""
    success: bool
    data: LimitsData
    response_shape: Dict[str, Any] = Field(default_factory=dict)


class OrderData(BaseModel):
    """Individual order data structure."""
    order_id: str
    symbol: str
    status: str
    quantity: int
    price: Optional[float] = None
    order_type: str
    product: str
    timestamp: Optional[str] = None


class GetOrdersOutput(BaseModel):
    """Output schema for getOrders tool."""
    success: bool
    count: int
    data: List[OrderData]
    response_shape: Dict[str, Any] = Field(default_factory=dict)


class PositionData(BaseModel):
    """Individual position data structure."""
    symbol: str
    quantity: int
    average_price: float
    ltp: Optional[float] = None
    pnl: Optional[float] = None
    product: str


class GetPositionsOutput(BaseModel):
    """Output schema for getPositions tool."""
    success: bool
    count: int
    data: List[PositionData]
    response_shape: Dict[str, Any] = Field(default_factory=dict)


class WebSocketStatusData(BaseModel):
    """WebSocket status data structure."""
    connected: bool
    active_subscriptions: int
    last_heartbeat: Optional[str] = None
    error: Optional[str] = None


class GetWebSocketStatusOutput(BaseModel):
    """Output schema for getWebSocketStatus tool."""
    success: bool
    data: WebSocketStatusData
    response_shape: Dict[str, Any] = Field(default_factory=dict)


class NewsArticle(BaseModel):
    """Individual news article structure."""
    title: str
    snippet: str
    source: str
    url: str
    published_date: Optional[str] = None


class SearchNewsOutput(BaseModel):
    """Output schema for searchNews tool."""
    success: bool
    count: int
    query: str
    data: List[NewsArticle]
    response_shape: Dict[str, Any] = Field(default_factory=dict)


class NavigateToOutput(BaseModel):
    """Output schema for navigateTo tool."""
    success: bool
    action: Literal["navigate"]
    route: str
    response_shape: Dict[str, Any] = Field(default_factory=dict)


class ApplyFilterOutput(BaseModel):
    """Output schema for applyFilter tool."""
    success: bool
    action: Literal["filter"]
    params: Dict[str, Any]
    response_shape: Dict[str, Any] = Field(default_factory=dict)


class GenerateChartInput(BaseModel):
    """Input schema for generateChart tool."""
    symbol: str = Field(
        ...,
        description="Trading symbol to chart (e.g. RELIANCE, NIFTY 50)"
    )
    period: Literal["1d", "1w", "1m", "3m", "1y"] = Field(
        default="1m",
        description="Time period for the chart"
    )

class ChartDataPoint(BaseModel):
    """Single data point for a chart."""
    time: str
    value: float

class GenerateChartOutput(BaseModel):
    """Output schema for generateChart tool."""
    success: bool
    type: Literal["chart"] = "chart"
    symbol: str
    data: List[ChartDataPoint]
    period: str
    response_shape: Dict[str, Any] = Field(default_factory=dict)


# ===========================
# Tool Call Log Schema
# ===========================

class MCPToolCallLog(BaseModel):
    """Schema for logging MCP tool calls."""
    timestamp: datetime
    tool_name: str
    arguments: Dict[str, Any]
    success: bool
    response_shape: Dict[str, Any]
    latency_ms: float
    error: Optional[str] = None
