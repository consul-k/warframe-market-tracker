import requests

BASE_URL = "https://api.warframe.market/v1"

def get_item_prices(item_url_name: str, rank: int = None):
    """
    Возвращает (минимальную, среднюю) цену за последние 48 часов
    по URL-имени предмета (например: 'wukong_prime_set').
    Если указан rank — фильтрует по mod_rank (например 0 или max).
    """
    url = f"{BASE_URL}/items/{item_url_name}/statistics"
    response = requests.get(url)

    if response.status_code != 200:
        raise ValueError(
            f"Item '{item_url_name}' не найден или ошибка запроса (status={response.status_code})"
        )

    data = response.json()
    try:
        stats_48h = data["payload"]["statistics_closed"]["48hours"]
        if not stats_48h:
            raise ValueError(f"Нет статистики по '{item_url_name}' за 48 часов")

        # 🔹 фильтруем по mod_rank, если передан
        if rank is not None:
            ranked_stats = [s for s in stats_48h if s.get("mod_rank") == rank]
            if ranked_stats:
                stats_48h = ranked_stats
            else:
                print(f"[INFO] Нет данных для rank={rank}, используем общие данные.")

        if not stats_48h:
            return None, None

        last_entry = stats_48h[-1]
        min_price = last_entry.get("min_price")
        avg_price = last_entry.get("avg_price")

        return min_price, avg_price

    except (KeyError, IndexError):
        raise KeyError(
            f"Структура ответа API изменилась или данные отсутствуют для '{item_url_name}'"
        )