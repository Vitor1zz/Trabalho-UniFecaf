"""
Assistente de dieta: escolhe o melhor prato e gera resposta em linguagem natural.
Usa OpenAI se houver chave no .env; senao usa mensagem local.
"""

import json
import os
import re

from dotenv import load_dotenv

load_dotenv()

GOAL_LABELS = {
    "equilibrada": "refeicao equilibrada",
    "perder_peso": "perder peso",
    "ganhar_massa": "ganhar massa muscular",
}


def _choose_platform(item, platform):
    if platform == "iFood":
        return {"name": "iFood", "price": item["iFoodPrice"], "delivery": item["iFoodDelivery"]}
    if platform == "99 Food":
        return {"name": "99 Food", "price": item["food99Price"], "delivery": item["food99Delivery"]}
    if item["iFoodPrice"] <= item["food99Price"]:
        return {"name": "iFood", "price": item["iFoodPrice"], "delivery": item["iFoodDelivery"]}
    return {"name": "99 Food", "price": item["food99Price"], "delivery": item["food99Delivery"]}


def _score_item(item, goal):
    if goal == "ganhar_massa":
        return item["protein"] * 2 - item["calories"] * 0.01
    if goal == "perder_peso":
        return item["protein"] * 1.5 - item["calories"] * 0.03
    return item["protein"] - abs(item["calories"] - 500) * 0.01


def _match_preference(preference_text, restaurant, item):
    preference_text = (preference_text or "").strip().lower()
    if not preference_text:
        return True
    haystack = f"{restaurant.get('cuisine', '')} {item.get('dish', '')}".lower()
    tokens = re.split(r"[,;\s]+", preference_text)
    return any(token in haystack for token in tokens if len(token) >= 2)


def _collect_options(restaurants, goal, preferences, budget, platform):
    options = []
    for restaurant in restaurants:
        for item in restaurant.get("items") or []:
            selected = _choose_platform(item, platform)
            options.append(
                {
                    "restaurant": restaurant,
                    "item": item,
                    "platform": selected,
                    "score": _score_item(item, goal),
                    "within_budget": selected["price"] <= budget,
                }
            )
    if not options:
        return None

    preferred = [
        o for o in options if _match_preference(preferences, o["restaurant"], o["item"])
    ]
    pool = preferred if preferred else options

    within = [o for o in pool if o["within_budget"]]
    if within:
        within.sort(key=lambda o: (o["score"], o["restaurant"]["rating"]), reverse=True)
        return within, False

    pool.sort(key=lambda o: (o["platform"]["price"], -o["score"]))
    return [pool[0]], True


def _link_for_platform(restaurant, item, platform_name):
    if platform_name == "99 Food":
        block = restaurant.get("food99") or {}
        return block.get("url") or item.get("link", "#")
    block = restaurant.get("ifood") or {}
    return block.get("url") or item.get("link", "#")


def _option_to_payload(option, budget_warning=False):
    platform_name = option["platform"]["name"]
    return {
        "dish": option["item"]["dish"],
        "restaurant": option["restaurant"]["name"],
        "rating": option["restaurant"]["rating"],
        "cuisine": option["restaurant"].get("cuisine", ""),
        "price": option["platform"]["price"],
        "platform": platform_name,
        "protein": option["item"]["protein"],
        "calories": option["item"]["calories"],
        "deliveryTime": option["platform"]["delivery"],
        "link": _link_for_platform(option["restaurant"], option["item"], platform_name),
        "budgetWarning": budget_warning,
    }


def _mensagem_local(payload, goal, preferences, budget):
    objetivo = GOAL_LABELS.get(goal, goal)
    pref = f" considerando sua preferencia por {preferences}" if preferences else ""
    aviso = ""
    if payload.get("budgetWarning"):
        aviso = (
            f" Seu orcamento de R$ {budget:.2f} ficou um pouco abaixo; "
            "escolhi a opcao mais barata disponivel."
        )

    return (
        f"Para {objetivo}{pref}, recomendo o **{payload['dish']}** "
        f"no **{payload['restaurant']}** ({payload['rating']:.1f} estrelas). "
        f"No {payload['platform']}, custa R$ {payload['price']:.2f} "
        f"com entrega estimada de {payload['deliveryTime']} min. "
        f"Nutricao aproximada: {payload['protein']}g de proteina e "
        f"{payload['calories']} kcal.{aviso}"
    )


def _mensagem_openai(payload, goal, preferences, budget, restaurants):
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("link_api")
    if not api_key or not api_key.startswith("sk-"):
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        catalogo = []
        for r in restaurants[:8]:
            pratos = ", ".join(
                f"{i['dish']} (R${min(i['iFoodPrice'], i['food99Price']):.0f})"
                for i in (r.get("items") or [])[:4]
            )
            catalogo.append(f"- {r['name']} ({r.get('cuisine', '')}): {pratos}")

        prompt = f"""Voce e a assistente do app Trivago Food.
Objetivo do usuario: {GOAL_LABELS.get(goal, goal)}
Preferencias: {preferences or 'nenhuma informada'}
Orcamento maximo: R$ {budget:.2f}
Plataforma preferida: {payload['platform']}

Melhor opcao calculada pelo sistema:
- Prato: {payload['dish']}
- Restaurante: {payload['restaurant']} ({payload['rating']} estrelas)
- Preco: R$ {payload['price']:.2f} no {payload['platform']}
- Proteina: {payload['protein']}g | Calorias: {payload['calories']} kcal
- Entrega: ~{payload['deliveryTime']} min
{"AVISO: opcao ligeiramente acima do orcamento informado." if payload.get('budgetWarning') else ""}

Cardapio disponivel:
{chr(10).join(catalogo)}

Escreva em portugues (Brasil), tom amigavel e direto, 3 a 5 frases.
Explique POR QUE essa escolha faz sentido para o objetivo.
Nao invente pratos fora da melhor opcao."""

        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "Assistente nutricional do Trivago Food."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=350,
            temperature=0.7,
        )
        text = (response.choices[0].message.content or "").strip()
        return text or None
    except Exception:
        return None


def gerar_recomendacao(restaurants, goal, preferences, budget, platform):
    if not restaurants:
        return None

    if budget <= 0:
        return {"error": "Informe um orcamento maior que zero."}

    collected = _collect_options(restaurants, goal, preferences, budget, platform)
    if not collected:
        return None

    options, budget_warning = collected
    payload = _option_to_payload(options[0], budget_warning)

    ai_message = _mensagem_openai(payload, goal, preferences, budget, restaurants)
    used_ai = bool(ai_message)
    if not ai_message:
        ai_message = _mensagem_local(payload, goal, preferences, budget)

    payload["aiMessage"] = ai_message
    payload["usedAI"] = used_ai
    return payload
