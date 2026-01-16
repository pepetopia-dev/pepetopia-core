import aiohttp
import logging

logger = logging.getLogger(__name__)

class PriceService:
    @staticmethod
    async def get_token_info(symbol: str):
        """
        Fetches ticker data directly from AscendEX (CEX) Public API.
        Reference: https://ascendex.github.io/ascendex-pro-api/#ticker
        """
        # AscendEX Public Ticker Endpoint
        url = f"https://ascendex.com/api/pro/v1/ticker?symbol={symbol}"
        
        logger.info(f"DEBUG: Requesting AscendEX URL -> {url}")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        json_response = await response.json()
                        logger.info(f"DEBUG: AscendEX Response -> {json_response}")
                        
                        # AscendEX standard response format:
                        # { "code": 0, "data": { "symbol": "...", "close": "...", ... } }
                        
                        if json_response.get("code") != 0:
                            logger.error(f"DEBUG: API returned error code: {json_response.get('code')}")
                            return None

                        data = json_response.get("data")
                        if not data:
                            logger.warning("DEBUG: 'data' field is empty.")
                            return None
                        
                        # Data Mapping
                        # CEXs don't show "Liquidity" in generic tickers, they show 24h Volume.
                        return {
                            "name": symbol.split("/")[0], # PEPETOPIA
                            "symbol": symbol,
                            "priceUsd": float(data.get("close", 0)),
                            "change24h": float(data.get("close", 0)) - float(data.get("open", 0)), # Calculate change roughly or use if available
                            "changePercent": ((float(data.get("close", 0)) - float(data.get("open", 0))) / float(data.get("open", 1))) * 100,
                            "volume": float(data.get("volume", 0)), # 24h Volume
                            "high": float(data.get("high", 0)),
                            "low": float(data.get("low", 0)),
                            "url": f"https://ascendex.com/en/cashtrade-spottrading/usdt/{symbol.split('/')[0].lower()}"
                        }
                    else:
                        logger.error(f"API Error: Status Code {response.status}")
                        return None
            except Exception as e:
                logger.error(f"Connection Error: {e}")
                return None