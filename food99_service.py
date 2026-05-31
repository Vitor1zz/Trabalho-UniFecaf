"""
Integracao 99 Food com o Trivago Food.
- Cache em dados_food99.json
- Sessao opcional em food99_session.json ou variaveis .env
"""

import json
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent
CACHE_FILE = ROOT / "dados_food99.json"
SESSION_FILE = ROOT / "food99_session.json"


def _normalize_name(value):
    text = unicodedata.normalize("NFKD", (value or "").lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", text)


def _load_session_file():
    if not SESSION_FILE.is_file():
        return {}
    try:
        with SESSION_FILE.open(encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def _food99_headers():
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Origin": "https://food.99app.com",
        "Referer": "https://food.99app.com/",
    }
    session = _load_session_file()
    token = (session.get("authorization") or os.getenv("FOOD99_AUTHORIZATION", "")).strip()
    if token:
        headers["Authorization"] = token
    return headers


def _has_live_credentials():
    return bool(_food99_headers().get("Authorization"))


def _load_cache():
    if not CACHE_FILE.is_file():
        return {"merchants": [], "source": "none"}
    with CACHE_FILE.open(encoding="utf-8") as file:
        return json.load(file)


def _save_cache(data):
    data["updatedAt"] = datetime.now().isoformat(timespec="seconds")
    with CACHE_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def _busca_url(nome):
    return f"https://food.99app.com/pt-BR/search?keyword={quote_plus(nome)}"


def status_conexao():
    cache = _load_cache()
    return {
        "conectado": bool(cache.get("merchants")),
        "liveApi": _has_live_credentials(),
        "source": cache.get("source", "none"),
        "updatedAt": cache.get("updatedAt"),
        "totalRestaurantes": len(cache.get("merchants") or []),
        "sessionFile": SESSION_FILE.is_file(),
    }


def inicializar():
    cache = _load_cache()
    if cache.get("merchants"):
        return status_conexao()
    return status_conexao()


def buscar_food99_api(termo="", limit=30):
    if not _has_live_credentials():
        return None, "Configure food99_session.json ou FOOD99_AUTHORIZATION no .env"

    lat = os.getenv("FOOD99_LAT", os.getenv("IFOOD_LAT", "-23.5505"))
    lng = os.getenv("FOOD99_LNG", os.getenv("IFOOD_LNG", "-46.6333"))
    query = quote_plus(termo or "restaurante")
    url = os.getenv(
        "FOOD99_SEARCH_URL",
        f"https://food.99app.com/api/search?keyword={query}&lat={lat}&lng={lng}&limit={limit}",
    )

    request = Request(url, headers=_food99_headers())
    try:
        with urlopen(request, timeout=25) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return None, f"Falha na API 99 Food: {exc}"

    merchants = _parse_search_payload(payload)
    if not merchants:
        return None, "Nenhum restaurante retornado pela 99 Food."

    data = {"source": "food99_api", "merchants": merchants}
    _save_cache(data)
    return data, None


def _parse_search_payload(payload):
    merchants = []

    def walk(node):
        if isinstance(node, dict):
            name = (
                node.get("name")
                or node.get("shopName")
                or node.get("title")
                or node.get("merchantName")
            )
            rating = node.get("rating") or node.get("score") or node.get("userRating")
            if name and rating is not None:
                try:
                    rating = float(rating)
                except (TypeError, ValueError):
                    rating = None
                if rating and 0 < rating <= 5:
                    merchants.append(
                        {
                            "name": str(name).strip(),
                            "rating": round(rating, 1),
                            "reviews": int(node.get("reviewCount") or node.get("reviews") or 0),
                            "deliveryTime": int(node.get("deliveryTime") or 30),
                            "deliveryFee": float(node.get("deliveryFee") or 0),
                            "url": node.get("url") or _busca_url(name),
                            "items": node.get("items") or [],
                        }
                    )
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    unique = {}
    for merchant in merchants:
        key = _normalize_name(merchant["name"])
        if key and key not in unique:
            unique[key] = merchant
    return list(unique.values())[:40]


def _food99_block(food99, restaurant_name, source):
    return {
        "rating": float(food99.get("rating", 0)),
        "reviews": int(food99.get("reviews") or 0),
        "deliveryTime": int(food99.get("deliveryTime") or 30),
        "deliveryFee": float(food99.get("deliveryFee") or 0),
        "url": food99.get("url") or _busca_url(restaurant_name),
        "source": source,
    }


def _match_item_price(food99_items, dish_name):
    dish_key = _normalize_name(dish_name)
    for item in food99_items or []:
        if _normalize_name(item.get("name")) == dish_key:
            return float(item.get("price", 0))
        if dish_key in _normalize_name(item.get("name", "")):
            return float(item.get("price", 0))
    return None


def _items_from_food99(food99):
    items = []
    for entry in food99.get("items") or []:
        price = float(entry.get("price") or 0)
        if price <= 0:
            continue
        url = food99.get("url") or "#"
        items.append(
            {
                "dish": entry.get("name", "Item"),
                "protein": 25,
                "calories": 500,
                "iFoodPrice": round(price * 1.03, 2),
                "food99Price": price,
                "iFoodDelivery": int(food99.get("deliveryTime") or 30) + 2,
                "food99Delivery": int(food99.get("deliveryTime") or 30),
                "link": url,
            }
        )
    return items


def merge_food99(restaurants):
    """Aplica precos e links da 99 Food sobre lista ja mesclada com iFood."""
    cache = _load_cache()
    food99_list = cache.get("merchants") or []
    source = cache.get("source", "local")
    by_name = {_normalize_name(m["name"]): m for m in food99_list}
    used_keys = set()
    merged = []

    for restaurant in restaurants:
        key = _normalize_name(restaurant["name"])
        food99 = by_name.get(key)
        row = dict(restaurant)

        if food99:
            used_keys.add(key)
            row["food99"] = _food99_block(food99, restaurant["name"], source)
            for item in row.get("items") or []:
                price = _match_item_price(food99.get("items"), item["dish"])
                if price:
                    item["food99Price"] = price
        else:
            row["food99"] = _food99_block(
                {
                    "rating": row.get("rating", 0),
                    "reviews": 0,
                    "deliveryTime": row.get("ifood", {}).get("deliveryTime", 30),
                    "deliveryFee": 0,
                    "url": _busca_url(restaurant["name"]),
                },
                restaurant["name"],
                "local",
            )
            for item in row.get("items") or []:
                ifood_p = float(item.get("iFoodPrice") or 0)
                if not item.get("food99Price") and ifood_p > 0:
                    item["food99Price"] = round(ifood_p * 0.95, 2)

        merged.append(row)

    existing = {_normalize_name(r["name"]) for r in merged}
    for food99 in food99_list:
        key = _normalize_name(food99["name"])
        if key in used_keys or key in existing:
            continue
        items = _items_from_food99(food99)
        if not items:
            items = [
                {
                    "dish": "Ver cardapio na 99",
                    "protein": 0,
                    "calories": 0,
                    "iFoodPrice": 0,
                    "food99Price": 0,
                    "iFoodDelivery": 30,
                    "food99Delivery": 30,
                    "link": food99.get("url") or _busca_url(food99["name"]),
                }
            ]
        cuisine = (food99.get("cuisine") or "Parceiro 99 Food").strip()
        merged.append(
            {
                "name": food99["name"],
                "rating": float(food99.get("rating") or 0),
                "cuisine": cuisine,
                "nutritionSeal": False,
                "items": items,
                "food99": _food99_block(food99, food99["name"], source),
                "ifood": {
                    "rating": float(food99.get("rating") or 0),
                    "reviews": 0,
                    "deliveryTime": int(food99.get("deliveryTime") or 30),
                    "deliveryFee": 0,
                    "url": f"https://www.ifood.com.br/busca?q={quote_plus(food99['name'])}",
                    "source": "local",
                },
                "onlyFood99": True,
            }
        )

    return merged, source, cache.get("updatedAt")


def atualizar_precos_food99(termo=""):
    if _has_live_credentials():
        data, error = buscar_food99_api(termo)
        if data:
            return {
                "ok": True,
                "source": data["source"],
                "message": "99 Food atualizado.",
                "status": status_conexao(),
            }
        return {"ok": False, "message": error, "status": status_conexao()}

    cache = _load_cache()
    if cache.get("merchants"):
        return {
            "ok": True,
            "source": cache.get("source", "demo"),
            "message": "99 Food via dados_food99.json.",
            "status": status_conexao(),
        }
    return {
        "ok": False,
        "message": "Sem dados 99 Food. Execute popular_catalogo_ifood ou confira dados_food99.json.",
        "status": status_conexao(),
    }
