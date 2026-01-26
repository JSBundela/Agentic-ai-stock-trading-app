"""
MCP Tools - Read-only tool implementations wrapping existing services.

All tools enforce strict read-only operations with validation and logging.
"""

import time
from typing import Dict, Any, List, Optional
from duckduckgo_search import DDGS
from app.mcp.mcp_schemas import *
from app.mcp.mcp_logger import logger
import yfinance as yf
from app.market.service import MarketService
from app.portfolio.service import PortfolioService
from app.orders.service import OrderService
from app.core.logger import logger as app_logger


class MCPTools:
    """
    Central registry of all MCP tools.
    Each tool is a read-only wrapper around existing services.
    """
    
    def __init__(self):
        self.market_service = MarketService()
        self.portfolio_service = PortfolioService()
        self.order_service = OrderService()
    
    async def get_quotes(self, input_data: GetQuotesInput) -> GetQuotesOutput:
        """
        Fetch live market quotes for symbols.
        
        Wraps: MarketService.get_quotes()
        """
        start_time = time.time()
        tool_name = "getQuotes"
        
        try:
            # Prepend nse_cm| if missing
            symbols = [s if "|" in s else f"nse_cm|{s}" for s in input_data.symbols]
            
            # Call underlying service (returns list directly)
            result = await self.market_service.get_quotes(symbols)
            
            # Parse response
            quotes = []
            errors = []
            
            # market_service.get_quotes returns a list directly
            if isinstance(result, list):
                for quote in result:
                    quotes.append(QuoteData(
                        symbol=quote.get("tradingSymbol", "UNKNOWN"),
                        ltp=quote.get("ltp"),
                        change=quote.get("netChange") or quote.get("change"),
                        percent_change=quote.get("percentChange") or quote.get("pChange"),
                        volume=quote.get("volume"),
                        timestamp=quote.get("ltt")
                    ))
            else:
                errors.append("Invalid response format")
            
            latency_ms = (time.time() - start_time) * 1000
            
           # Log successful call
            logger.log_tool_call(
                tool_name=tool_name,
                arguments=input_data.model_dump(),
                success=True,
                response_shape={"count": len(quotes), "fields": ["ltp", "change", "percent_change"]},
                latency_ms=latency_ms
            )
            
            return GetQuotesOutput(
                success=True,
                count=len(quotes),
                data=quotes,
                errors=errors if errors else None,
                response_shape={"count": len(quotes)}
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.log_tool_call(
                tool_name=tool_name,
                arguments=input_data.model_dump(),
                success=False,
                response_shape={},
                latency_ms=latency_ms,
                error=str(e)
            )
            
            return GetQuotesOutput(
                success=False,
                count=0,
                data=[],
                errors=[str(e)],
                response_shape={}
            )
    
    async def get_index_quotes(self, input_data: GetIndexQuotesInput) -> GetIndexQuotesOutput:
        """
        Fetch live index quotes (NIFTY 50, SENSEX, etc).
        
        Wraps: MarketService.get_quotes() with index-specific tokens.
        """
        start_time = time.time()
        tool_name = "getIndexQuotes"
        
        try:
            # Map index names to API tokens
            index_mapping = {
                "NIFTY 50": "Nifty 50",
                "NIFTY BANK": "Nifty Bank",
                "SENSEX": "SENSEX",
                "NIFTY IT": "Nifty IT"
            }
            
            # Determine the correct instrument token based on the index name
            # If it's SENSEX, use bse_cm|, otherwise default to nse_cm|
            if input_data.index.upper() == "SENSEX":
                index_token = f"bse_cm|{index_mapping.get(input_data.index, input_data.index)}"
            else:
                index_token = f"nse_cm|{index_mapping.get(input_data.index, input_data.index)}"
            
            # Call underlying service
            result = await self.market_service.get_quotes([index_token])
            
            # Parse response
            index_data = IndexQuoteData(
                index_name=input_data.index,
                error=None
            )
            
            # market_service.get_quotes returns a list directly
            if isinstance(result, list) and len(result) > 0:
                quote = result[0]
                index_data.ltp = quote.get("ltp")
                index_data.change = quote.get("netChange") or quote.get("change")
                index_data.percent_change = quote.get("percentChange") or quote.get("pChange")
                index_data.timestamp = quote.get("ltt")
            else:
                index_data.error = "Data unavailable"
            
            latency_ms = (time.time() - start_time) * 1000
            
            logger.log_tool_call(
                tool_name=tool_name,
                arguments=input_data.model_dump(),
                success=True,
                response_shape={"fields": ["ltp", "change", "percent_change"]},
                latency_ms=latency_ms
            )
            
            return GetIndexQuotesOutput(
                success=True,
                data=index_data,
                response_shape={"index": input_data.index}
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.log_tool_call(
                tool_name=tool_name,
                arguments=input_data.model_dump(),
                success=False,
                response_shape={},
                latency_ms=latency_ms,
                error=str(e)
            )
            
            return GetIndexQuotesOutput(
                success=False,
                data=IndexQuoteData(
                    index_name=input_data.index,
                    error=str(e)
                ),
                response_shape={}
            )
    
    async def get_market_depth(self, input_data: GetMarketDepthInput) -> GetMarketDepthOutput:
        """
        Fetch market depth (order book) for a symbol.
        
        Note: Kotak API may not expose full depth. Returns best available.
        """
        start_time = time.time()
        tool_name = "getMarketDepth"
        
        try:
            # Market depth is typically included in full quote response
            result = await self.market_service.get_quotes([input_data.symbol])
            
            depth_data = MarketDepthData(
                symbol=input_data.symbol,
                bids=[],
                asks=[]
            )
            
            if result.get("stat") == "Ok" and result.get("data"):
                quote = result["data"][0]
                
                # Parse bid/ask if available (depends on API fields)
                # NOTE: Kotak API documentation should be checked for exact field names
                # This is a placeholder structure
                depth_data.timestamp = quote.get("ltt")
            
            latency_ms = (time.time() - start_time) * 1000
            
            logger.log_tool_call(
                tool_name=tool_name,
                arguments=input_data.model_dump(),
                success=True,
                response_shape={"bids_count": len(depth_data.bids), "asks_count": len(depth_data.asks)},
                latency_ms=latency_ms
            )
            
            return GetMarketDepthOutput(
                success=True,
                data=depth_data,
                response_shape={}
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.log_tool_call(
                tool_name=tool_name,
                arguments=input_data.model_dump(),
                success=False,
                response_shape={},
                latency_ms=latency_ms,
                error=str(e)
            )
            
            return GetMarketDepthOutput(
                success=False,
                data=MarketDepthData(symbol=input_data.symbol, error=str(e)),
                response_shape={}
            )
    
    async def get_limits(self) -> GetLimitsOutput:
        """
        Fetch user funds and margin limits.
        
        Wraps: PortfolioService.get_limits()
        """
        start_time = time.time()
        tool_name = "getLimits"
        
        try:
            result = await self.portfolio_service.get_limits()
            
            limits_data = LimitsData()
            
            if result.get("stat") == "Ok":
                # Map API fields (Kotak API uses PascalCase at the root for limits)
                limits_data.cash_available = result.get("Net")
                limits_data.collateral = result.get("CollateralValue")
                limits_data.margin_used = result.get("MarginUsed")
                limits_data.total_limit = result.get("NotionalCash")
            else:
                limits_data.error = result.get("message", "Data unavailable")
            
            latency_ms = (time.time() - start_time) * 1000
            
            logger.log_tool_call(
                tool_name=tool_name,
                arguments={},
                success=True,
                response_shape={"fields": ["cash_available", "margin_used"]},
                latency_ms=latency_ms
            )
            
            return GetLimitsOutput(
                success=True,
                data=limits_data,
                response_shape={}
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.log_tool_call(
                tool_name=tool_name,
                arguments={},
                success=False,
                response_shape={},
                latency_ms=latency_ms,
                error=str(e)
            )
            
            return GetLimitsOutput(
                success=False,
                data=LimitsData(error=str(e)),
                response_shape={}
            )
    
    async def get_orders(self, input_data: GetOrdersInput) -> GetOrdersOutput:
        """
        Fetch order history with optional status filter.
        
        Wraps: OrderService.get_order_history()
        """
        start_time = time.time()
        tool_name = "getOrders"
        
        try:
            result = await self.order_service.get_order_history()
            
            orders = []
            
            if result.get("stat") == "Ok" and result.get("data"):
                for order in result["data"]:
                    # Apply status filter if provided
                    order_status = order.get("status", "")
                    if input_data.status and order_status != input_data.status:
                        continue
                    
                    orders.append(OrderData(
                        order_id=order.get("orderId", ""),
                        symbol=order.get("tradingSymbol", ""),
                        status=order_status,
                        quantity=order.get("quantity", 0),
                        price=order.get("price"),
                        order_type=order.get("orderValidity", ""),
                        product=order.get("product", ""),
                        timestamp=order.get("orderTimestamp")
                    ))
            
            latency_ms = (time.time() - start_time) * 1000
            
            logger.log_tool_call(
                tool_name=tool_name,
                arguments=input_data.model_dump(),
                success=True,
                response_shape={"count": len(orders)},
                latency_ms=latency_ms
            )
            
            return GetOrdersOutput(
                success=True,
                count=len(orders),
                data=orders,
                response_shape={"count": len(orders)}
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.log_tool_call(
                tool_name=tool_name,
                arguments=input_data.model_dump(),
                success=False,
                response_shape={},
                latency_ms=latency_ms,
                error=str(e)
            )
            
            return GetOrdersOutput(
                success=False,
                count=0,
                data=[],
                response_shape={}
            )
    
    async def get_positions(self) -> GetPositionsOutput:
        """
        Fetch current positions.
        
        Wraps: PortfolioService.get_positions()
        """
        start_time = time.time()
        tool_name = "getPositions"
        
        try:
            result = await self.portfolio_service.get_positions()
            
            positions = []
            
            if result.get("stat") == "Ok" and result.get("data"):
                for pos in result["data"]:
                    positions.append(PositionData(
                        symbol=pos.get("tradingSymbol", ""),
                        quantity=pos.get("netQty", 0),
                        average_price=pos.get("avgPrc", 0.0),
                        ltp=pos.get("ltp"),
                        pnl=pos.get("unrealisedMTM"),
                        product=pos.get("prod", "")
                    ))
            
            latency_ms = (time.time() - start_time) * 1000
            
            logger.log_tool_call(
                tool_name=tool_name,
                arguments={},
                success=True,
                response_shape={"count": len(positions)},
                latency_ms=latency_ms
            )
            
            return GetPositionsOutput(
                success=True,
                count=len(positions),
                data=positions,
                response_shape={"count": len(positions)}
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.log_tool_call(
                tool_name=tool_name,
                arguments={},
                success=False,
                response_shape={},
                latency_ms=latency_ms,
                error=str(e)
            )
            
            return GetPositionsOutput(
                success=False,
                count=0,
                data=[],
                response_shape={}
            )
    
    async def get_websocket_status(self) -> GetWebSocketStatusOutput:
        """
        Check WebSocket connection health.
        
        Note: Implementation depends on WebSocket manager structure.
        """
        start_time = time.time()
        tool_name = "getWebSocketStatus"
        
        try:
            # Placeholder: actual implementation needs WebSocket manager access
            ws_data = WebSocketStatusData(
                connected=True,  # TODO: Get actual status
                active_subscriptions=0,  # TODO: Get actual count
                last_heartbeat=None
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            logger.log_tool_call(
                tool_name=tool_name,
                arguments={},
                success=True,
                response_shape={"connected": ws_data.connected},
                latency_ms=latency_ms
            )
            
            return GetWebSocketStatusOutput(
                success=True,
                data=ws_data,
                response_shape={}
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.log_tool_call(
                tool_name=tool_name,
                arguments={},
                success=False,
                response_shape={},
                latency_ms=latency_ms,
                error=str(e)
            )
            
            return GetWebSocketStatusOutput(
                success=False,
                data=WebSocketStatusData(connected=False, active_subscriptions=0, error=str(e)),
                response_shape={}
            )
    
    async def search_news(self, input_data: SearchNewsInput) -> SearchNewsOutput:
        """
        Search news using DuckDuckGo.
        
        NO API key required.
        """
        start_time = time.time()
        tool_name = "searchNews"
        
        try:
            # Use DuckDuckGo search
            with DDGS() as ddgs:
                results = list(ddgs.news(
                    keywords=input_data.query,
                    max_results=input_data.max_results
                ))
            
            articles = []
            for result in results:
                articles.append(NewsArticle(
                    title=result.get("title", ""),
                    snippet=result.get("body", ""),
                    source=result.get("source", ""),
                    url=result.get("url", ""),
                    published_date=result.get("date")
                ))
            
            latency_ms = (time.time() - start_time) * 1000
            
            logger.log_tool_call(
                tool_name=tool_name,
                arguments=input_data.model_dump(),
                success=True,
                response_shape={"count": len(articles)},
                latency_ms=latency_ms
            )
            
            return SearchNewsOutput(
                success=True,
                count=len(articles),
                query=input_data.query,
                data=articles,
                response_shape={"count": len(articles)}
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.log_tool_call(
                tool_name=tool_name,
                arguments=input_data.model_dump(),
                success=False,
                response_shape={},
                latency_ms=latency_ms,
                error=str(e)
            )
            
            return SearchNewsOutput(
                success=False,
                count=0,
                query=input_data.query,
                data=[],
                response_shape={}
            )
    
    async def navigate_to(self, input_data: NavigateToInput) -> NavigateToOutput:
        """
        Generate UI navigation command.
        
        Returns JSON for frontend router.
        """
        start_time = time.time()
        tool_name = "navigateTo"
        
        try:
            latency_ms = (time.time() - start_time) * 1000
            
            logger.log_tool_call(
                tool_name=tool_name,
                arguments=input_data.model_dump(),
                success=True,
                response_shape={"action": "navigate", "route": input_data.route},
                latency_ms=latency_ms
            )
            
            return NavigateToOutput(
                success=True,
                action="navigate",
                route=input_data.route,
                response_shape={"route": input_data.route}
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.log_tool_call(
                tool_name=tool_name,
                arguments=input_data.model_dump(),
                success=False,
                response_shape={},
                latency_ms=latency_ms,
                error=str(e)
            )
            
            return NavigateToOutput(
                success=False,
                action="navigate",
                route="",
                response_shape={}
            )
    
    async def apply_filter(self, input_data: ApplyFilterInput) -> ApplyFilterOutput:
        """
        Generate UI filter command.
        
        Returns JSON for frontend state.
        """
        start_time = time.time()
        tool_name = "applyFilter"
        
        try:
            latency_ms = (time.time() - start_time) * 1000
            
            logger.log_tool_call(
                tool_name=tool_name,
                arguments=input_data.model_dump(),
                success=True,
                response_shape={"action": "filter", "params": input_data.params},
                latency_ms=latency_ms
            )
            
            return ApplyFilterOutput(
                success=True,
                action="filter",
                params=input_data.params,
                response_shape={"params": input_data.params}
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.log_tool_call(
                tool_name=tool_name,
                arguments=input_data.model_dump(),
                success=False,
                response_shape={},
                latency_ms=latency_ms,
                error=str(e)
            )
            
            return ApplyFilterOutput(
                success=False,
                action="filter",
                params={},
                response_shape={}
            )

    async def generate_chart(self, input_data: GenerateChartInput) -> GenerateChartOutput:
        """
        Generate chart data for a symbol.
        
        Uses yfinance to fetch historical data.
        """
        start_time = time.time()
        tool_name = "generateChart"
        
        try:
            symbol = input_data.symbol
            
            # 1. Specialized Symbol Mapping (yfinance specific)
            mapping = {
                "NIFTY 50": "^NSEI",
                "NIFTY BANK": "^NSEBANK",
                "SENSEX": "^BSESN",
                "NIFTY IT": "^CNXIT"
            }
            
            yf_symbol = mapping.get(symbol.upper(), symbol)
            
            # 2. Add exchange suffix if needed (default to .NS for NSE)
            if not any(yf_symbol.endswith(s) for s in [".NS", ".BO", "^NSEI", "^BSESN", "^NSEBANK", "^CNXIT"]):
                yf_symbol = f"{yf_symbol}.NS"
                
            # Fetch data with retry logic for different exchanges
            hist = yf.Ticker(yf_symbol).history(period=input_data.period)
            
            if hist.empty and ".NS" in yf_symbol:
                # Try BSE if NSE failed
                yf_symbol = yf_symbol.replace(".NS", ".BO")
                hist = yf.Ticker(yf_symbol).history(period=input_data.period)
            
            data_points = []
            for date, row in hist.iterrows():
                data_points.append(ChartDataPoint(
                    time=date.strftime("%Y-%m-%d"),
                    value=float(row['Close'])
                ))
            
            latency_ms = (time.time() - start_time) * 1000
            
            logger.log_tool_call(
                tool_name=tool_name,
                arguments=input_data.model_dump(),
                success=True,
                response_shape={"count": len(data_points)},
                latency_ms=latency_ms
            )
            
            return GenerateChartOutput(
                success=True,
                symbol=input_data.symbol,
                data=data_points,
                period=input_data.period,
                response_shape={"count": len(data_points)}
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.log_tool_call(
                tool_name=tool_name,
                arguments=input_data.model_dump(),
                success=False,
                response_shape={},
                latency_ms=latency_ms,
                error=str(e)
            )
            
            return GenerateChartOutput(
                success=False,
                symbol=input_data.symbol,
                data=[],
                period=input_data.period,
                response_shape={"error": str(e)}
            )


# Export singleton instance
mcp_tools = MCPTools()
