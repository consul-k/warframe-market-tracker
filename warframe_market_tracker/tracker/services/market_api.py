import requests
import time
import logging

BASE_URL = "https://api.warframe.market/v1"

HEADERS = {
    "User-Agent": "warframe-market-tracker/1.0"
}

TIMEOUT = 10
RETRY_DELAY = 5


def get_item_prices(item_url_name: str, rank: int = None):
    url = f"{BASE_URL}/items/{item_url_name}/statistics"
    """
    Возвращает (минимальную, среднюю) цену за последние 48 часов
    по URL-имени предмета (например: 'wukong_prime_set').
    Если указан rank — фильтрует по mod_rank (например 0 или max).
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)

        if response.status_code == 429:
            raise ValueError(f"status=429 rate limited for '{item_url_name}'")

        if response.status_code != 200:
            raise ValueError(
                f"Item '{item_url_name}' error (status={response.status_code})"
            )

        data = response.json()

        stats_48h = data["payload"]["statistics_closed"]["48hours"]

        if not stats_48h:
            return None, None

        if rank is not None:
            ranked_stats = [s for s in stats_48h if s.get("mod_rank") == rank]
            if ranked_stats:
                stats_48h = ranked_stats
            else:
                logging.info(f"No data for rank={rank}, fallback to general")

        if not stats_48h:
            return None, None

        last_entry = stats_48h[-1]

        return (
            last_entry.get("min_price"),
            last_entry.get("avg_price"),
        )

    except requests.Timeout:
        logging.error(f"[TIMEOUT] {item_url_name}")
        return None, None

    except requests.RequestException as e:
        logging.error(f"[REQUEST ERROR] {item_url_name}: {e}")
        return None, None

    except (KeyError, IndexError):
        logging.error(f"[DATA ERROR] {item_url_name}")
        return None, None