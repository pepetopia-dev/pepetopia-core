import requests
import logging

logger = logging.getLogger(__name__)

class MarketService:
    
    @staticmethod
    def get_fear_and_greed():
        """
        Fetches the Fear and Greed Index from the Alternative.me API.
        """
        url = "https://api.alternative.me/fng/?limit=1"
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if data['data']:
                return data['data'][0] # {value: "25", value_classification: "Extreme Fear"}
        except Exception as e:
            logger.error(f"Fear&Greed API Error: {e}")
        return None

    @staticmethod
    def get_top_gainers():
        """
        Finds the top 5 gainers among the top 100 coins by market cap from CoinGecko.
        (Applies Top 100 filter to filter out junk coins)
        """
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc", # Biggest first
            "per_page": "100",          # Top 100 coins
            "page": "1",
            "sparkline": "false",
            "price_change_percentage": "24h"
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Sort by 24h change (Descending)
                sorted_coins = sorted(data, key=lambda x: x['price_change_percentage_24h'] if x['price_change_percentage_24h'] else 0, reverse=True)
                return sorted_coins[:5] # Return top 5
        except Exception as e:
            logger.error(f"CoinGecko API Error: {e}")
        return None

    @staticmethod
    def get_long_short_ratio(symbol="BTCUSDT"):
        """
        Fetches the Global Long/Short ratio via Binance Futures.
        BTCUSDT is used as the baseline as it determines market direction.
        """
        url = "https://fapi.binance.com/futures/data/globalLongShortAccountRatio"
        params = {
            "symbol": symbol,
            "period": "5m", # Last 5 minutes period
            "limit": 1
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return data[0] # {longAccount: "0.6", shortAccount: "0.4", longShortRatio: "1.5"}
        except Exception as e:
            logger.error(f"Binance API Error: {e}")
        return None