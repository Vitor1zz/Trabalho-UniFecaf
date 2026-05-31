"""
Integracao iFood com o Trivago Food.
- Cache em dados_ifood.json
- Sessao opcional em ifood_session.json ou variaveis .env
- API ao vivo quando houver autenticacao
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
CACHE_FILE = ROOT / "dados_ifood.json"
SESSION_FILE = ROOT / "ifood_session.json"


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


def _ifood_headers():
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "platform": "Desktop",
        "app_version": "9.6.0",
        "country_code": "BR",
        "language": "pt-BR",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Origin": "https://www.ifood.com.br",
        "Referer": "https://www.ifood.com.br/",
    }
    session = _load_session_file()
    env_map = {
        "authorization": "IFOOD_AUTHORIZATION",
        "x-ifood-session-id": "IFOOD_SESSION_ID",
        "x-ifood-device-id": "IFOOD_DEVICE_ID",
        "x-ifood-user-id": "IFOOD_USER_ID",
        "x-client-application-key": "IFOOD_CLIENT_KEY",
    }
    for header_key, env_key in env_map.items():
        value = (session.get(header_key) or os.getenv(env_key, "")).strip()
        if value:
            headers[header_key] = value
    return headers


def _has_live_credentials():
    headers = _ifood_headers()
    return bool(headers.get("authorization"))


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
    return f"https://www.ifood.com.br/busca?q={quote_plus(nome)}"


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
    """Garante cache iFood carregado ao iniciar o servidor."""
    cache = _load_cache()
    if cache.get("merchants"):
        return status_conexao()
    if _has_live_credentials():
        data, _ = buscar_ifood_api("")
        if data:
            return status_conexao()
    return status_conexao()


def buscar_ifood_api(termo="", limit=30):
    if not _has_live_credentials():
        return None, "Configure ifood_session.json ou variaveis IFOOD_* no .env"

    lat = os.getenv("IFOOD_LAT", "-23.5505")
    lng = os.getenv("IFOOD_LNG", "-46.6333")
    query = quote_plus(termo or "restaurante")
    url = (
        "https://marketplace.ifood.com.br/v2/cardstack/search/results"
        f"?term={query}&latitude={lat}&longitude={lng}&size={limit}&page=0"
    )

    request = Request(url, headers=_ifood_headers())
    try:
        with urlopen(request, timeout=25) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return None, f"Falha na API iFood: {exc}"

    merchants = _parse_search_payload(payload)
    if not merchants:
        return None, "Nenhum restaurante retornado. Verifique se a sessao ainda e valida."

    data = {"source": "ifood_api", "merchants": merchants}
    _save_cache(data)
    return data, None


def _parse_search_payload(payload):
    merchants = []

    def walk(node):
        if isinstance(node, dict):
            name = (
                node.get("name")
                or node.get("title")
                or node.get("tradingName")
                or node.get("merchantName")
            )
            rating = (
                node.get("userRating")
                or node.get("rating")
                or node.get("evaluationAverage")
            )
            if name and rating is not None:
                try:
                    rating = float(rating)
                except (TypeError, ValueError):
                    rating = None
                if rating and 0 < rating <= 5:
                    slug = node.get("slug") or node.get("merchantSlug")
                    url = _busca_url(name)
                    if slug:
                        url = f"https://www.ifood.com.br/delivery/{slug}"
                    merchants.append(
                        {
                            "name": str(name).strip(),
                            "rating": round(rating, 1),
                            "reviews": int(node.get("evaluationCount") or node.get("reviews") or 0),
                            "deliveryTime": int(
                                node.get("deliveryTime") or node.get("minDeliveryTime") or 30
                            ),
                            "deliveryFee": float(node.get("deliveryFee") or node.get("fee") or 0),
                            "url": url,
                            "items": [],
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


def _ifood_block(ifood, restaurant_name, source):
    return {
        "rating": float(ifood.get("rating", 0)),
        "reviews": int(ifood.get("reviews") or 0),
        "deliveryTime": int(ifood.get("deliveryTime") or 30),
        "deliveryFee": float(ifood.get("deliveryFee") or 0),
        "url": ifood.get("url") or _busca_url(restaurant_name),
        "source": source,
    }


def _items_from_ifood(ifood):
    items = []
    for entry in ifood.get("items") or []:
        price = float(entry.get("price") or 0)
        if price <= 0:
            continue
        items.append(
            {
                "dish": entry.get("name", "Item"),
                "protein": 25,
                "calories": 500,
                "iFoodPrice": price,
                "food99Price": round(price * 0.97, 2),
                "iFoodDelivery": int(ifood.get("deliveryTime") or 30),
                "food99Delivery": int(ifood.get("deliveryTime") or 30) + 3,
                "link": ifood.get("url") or "#",
            }
        )
    return items


def _match_item_price(ifood_items, dish_name):
    dish_key = _normalize_name(dish_name)
    for item in ifood_items or []:
        if _normalize_name(item.get("name")) == dish_key:
            return float(item.get("price", 0))
        if dish_key in _normalize_name(item.get("name", "")):
            return float(item.get("price", 0))
    return None


def merge_restaurants(db_restaurants, ifood_data=None):
    cache = ifood_data or _load_cache()
    ifood_list = cache.get("merchants") or []
    source = cache.get("source", "local")
    by_name = {_normalize_name(m["name"]): m for m in ifood_list}
    used_ifood_keys = set()
    merged = []

    for restaurant in db_restaurants:
        key = _normalize_name(restaurant["name"])
        ifood = by_name.get(key)
        row = dict(restaurant)

        if ifood:
            used_ifood_keys.add(key)
            row["rating"] = float(ifood.get("rating") or row["rating"])
            row["ifood"] = _ifood_block(ifood, restaurant["name"], source)
            for item in row.get("items") or []:
                price = _match_item_price(ifood.get("items"), item["dish"])
                if price:
                    item["iFoodPrice"] = price
                item["link"] = row["ifood"]["url"]
        else:
            row["ifood"] = _ifood_block(
                {
                    "rating": row["rating"],
                    "reviews": 0,
                    "deliveryTime": 30,
                    "deliveryFee": 0,
                    "url": _busca_url(restaurant["name"]),
                },
                restaurant["name"],
                "local",
            )
            for item in row.get("items") or []:
                item["link"] = row["ifood"]["url"]

        merged.append(row)

    for ifood in ifood_list:
        key = _normalize_name(ifood["name"])
        if key in used_ifood_keys:
            continue
        items = _items_from_ifood(ifood)
        if not items:
            items = [
                {
                    "dish": "Ver cardapio no iFood",
                    "protein": 0,
                    "calories": 0,
                    "iFoodPrice": 0,
                    "food99Price": 0,
                    "iFoodDelivery": int(ifood.get("deliveryTime") or 30),
                    "food99Delivery": 35,
                    "link": ifood.get("url") or _busca_url(ifood["name"]),
                }
            ]
        cuisine = (ifood.get("cuisine") or "Parceiro iFood").strip()
        merged.append(
            {
                "name": ifood["name"],
                "rating": float(ifood.get("rating") or 0),
                "cuisine": cuisine,
                "nutritionSeal": cuisine.lower() in ("saudavel", "japonesa", "vegana"),
                "items": items,
                "ifood": _ifood_block(ifood, ifood["name"], source),
                "onlyIfood": True,
            }
        )

    merged.sort(key=lambda r: (r.get("ifood", {}).get("rating", 0), r["name"]), reverse=True)
    return merged, source, cache.get("updatedAt")


def atualizar_precos_ifood(termo=""):
    if _has_live_credentials():
        data, error = buscar_ifood_api(termo)
        if data:
            return {
                "ok": True,
                "source": data["source"],
                "message": "iFood conectado! Precos e avaliacoes atualizados.",
                "status": status_conexao(),
            }
        return {"ok": False, "message": error, "status": status_conexao()}

    cache = _load_cache()
    if cache.get("merchants"):
        return {
            "ok": True,
            "source": cache.get("source", "demo"),
            "message": "iFood ligado via dados_ifood.json. Para API ao vivo, rode conectar_ifood.bat.",
            "status": status_conexao(),
        }
    return {
        "ok": False,
        "message": "Sem dados iFood. Execute conectar_ifood.bat ou confira dados_ifood.json.",
        "status": status_conexao(),
    }
