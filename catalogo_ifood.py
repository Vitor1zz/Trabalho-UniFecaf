"""
Catalogo de restaurantes por categoria do iFood (10 por tipo).
Usado para popular MySQL e dados_ifood.json.
"""

from datetime import date
from urllib.parse import quote_plus

# Categorias principais do iFood Brasil
CATEGORIAS_IFOOD = {
    "pizza": {
        "label": "Pizza",
        "pratos": [("Pizza Margherita M", 44.9), ("Pizza Calabresa M", 41.9)],
        "nomes": [
            "Domino's Pizza",
            "Pizza Hut",
            "Spoleto",
            "Pizza Crek",
            "Vero Pizza Bar",
            "Quintal do Espeto Pizza",
            "Forno de Minas Pizza",
            "Pizza Prime",
            "La Brasa Pizzaria",
            "Madero Steak House Pizza",
        ],
    },
    "hamburguer": {
        "label": "Hamburguer",
        "pratos": [("Combo Burger", 38.9), ("Smash Duplo", 42.9)],
        "nomes": [
            "Burger King",
            "McDonald's",
            "Bob's",
            "Outback Burger",
            "Madero",
            "The Fifties",
            "Habib's Burger",
            "Burguer Lab",
            "Vila do Hamburger",
            "Mequi",
        ],
    },
    "japonesa": {
        "label": "Japonesa",
        "pratos": [("Combo Sushi 20 pecas", 49.9), ("Temaki Salmao", 32.9)],
        "nomes": [
            "Poke Mania",
            "Gendai",
            "Sushi Bar",
            "Temaki House",
            "Sushiloko",
            "Yakitori San",
            "Koni Store",
            "Sushi Ten",
            "Origens do Sushi",
            "Kane Poke",
        ],
    },
    "brasileira": {
        "label": "Brasileira",
        "pratos": [("Prato Feito", 28.9), ("Feijoada Individual", 34.9)],
        "nomes": [
            "Madero",
            "Outback",
            "Coco Bambu",
            "Vivenda do Camarao",
            "Panela Mineira",
            "Brazuca Grill",
            "Sabor de Casa",
            "Restaurante do Zé",
            "Panela Quente",
            "Tempero Brasileiro",
        ],
    },
    "italiana": {
        "label": "Italiana",
        "pratos": [("Espaguete Bolonhesa", 36.9), ("Lasanha", 39.9)],
        "nomes": [
            "Spoleto",
            "Vivenda do Camarao Italiano",
            "Cantina do Bacco",
            "La Pasta",
            "Olive Garden",
            "Pasta Way",
            "Nonna Maria",
            "Trattoria Roma",
            "Bella Italia",
            "Massa & Cia",
        ],
    },
    "saudavel": {
        "label": "Saudavel",
        "pratos": [("Bowl Fit", 38.9), ("Salada Proteica", 34.9)],
        "nomes": [
            "Natural Garden",
            "Fresh Fit",
            "Green Life",
            "Saudavel Express",
            "Low Carb Kitchen",
            "Nutri Bowl",
            "Vida Leve",
            "Fit Food",
            "Organico House",
            "Bem Natural",
        ],
    },
    "arabe": {
        "label": "Arabe",
        "pratos": [("Esfiha Aberta 6un", 29.9), ("Shawarma", 27.9)],
        "nomes": [
            "Habib's",
            "Ragazzo Esfihas",
            "Beirut",
            "Arabian House",
            "Aladdin",
            "Damasco",
            "Libanes Grill",
            "Esfiharia do Líbano",
            "Sahara",
            "Kebab House",
        ],
    },
    "chinesa": {
        "label": "Chinesa",
        "pratos": [("Yakisoba", 32.9), ("Rolinho Primavera 8un", 24.9)],
        "nomes": [
            "China in Box",
            "Gendai Yakisoba",
            "Wok Express",
            "Dragao Oriental",
            "Casa China",
            "Mandarin",
            "Panda Express BR",
            "Sabor Oriental",
            "Wok & Co",
            "Imperio Chines",
        ],
    },
    "mexicana": {
        "label": "Mexicana",
        "pratos": [("Burrito", 34.9), ("Tacos 3un", 29.9)],
        "nomes": [
            "Giraffas Mex",
            "Taco Bell",
            "Burrito Loco",
            "Mexicana Grill",
            "El Torito",
            "Cantina Mexicana",
            "Chili's",
            "Guacamole",
            "La Mexicana",
            "Taco House",
        ],
    },
    "acai": {
        "label": "Acai",
        "pratos": [("Acai 500ml", 22.9), ("Acai com Nutella 700ml", 28.9)],
        "nomes": [
            "Acai da Barra",
            "Acai do Norte",
            "Bom Acai",
            "Acai Mix",
            "Acai Point",
            "Tropical Acai",
            "Acai Top",
            "Acai Mania",
            "Acai da Praia",
            "Acai Power",
        ],
    },
    "marmita": {
        "label": "Marmita",
        "pratos": [("Marmita Executiva", 24.9), ("Marmita Fit", 26.9)],
        "nomes": [
            "Marmitaria Fit",
            "Marmita Express",
            "Panela de Ferro",
            "Marmita da Vó",
            "Refeição Pronta",
            "Marmita Caseira",
            "Chef Marmita",
            "Marmita Gourmet",
            "Marmita do Dia",
            "Marmita Brasil",
        ],
    },
    "frango": {
        "label": "Frango",
        "pratos": [("Frango Assado", 29.9), ("Combo Frango Frito", 32.9)],
        "nomes": [
            "Giraffas",
            "KFC",
            "Frango Assado Ponto",
            "Spoleto Frango",
            "Frango no Pote",
            "Frango da Casa",
            "Frango Frito Top",
            "Assados do Frango",
            "Frango & Cia",
            "Golden Chicken",
        ],
    },
    "lanches": {
        "label": "Lanches",
        "pratos": [("X-Salada", 24.9), ("Misto Quente", 18.9)],
        "nomes": [
            "Subway",
            "Casa do Pao de Queijo",
            "Lanchonete da Esquina",
            "Mega Lanche",
            "Point do Lanche",
            "Lanche Cidade",
            "Hot Dog Mania",
            "Lancheria Central",
            "Sanduba Top",
            "Lanche & Cia",
        ],
    },
    "doces": {
        "label": "Doces e Bolos",
        "pratos": [("Bolo de Chocolate fatia", 14.9), ("Brigadeiro 4un", 16.9)],
        "nomes": [
            "Cacau Show",
            "Bacio di Latte",
            "Casa do Bolo",
            "Doceria da Vila",
            "Sweet House",
            "Confeitaria Arte Doce",
            "Bolos da Sogra",
            "Chocolateria",
            "Doce Mania",
            "Patisserie Francesa",
        ],
    },
    "padaria": {
        "label": "Padaria",
        "pratos": [("Cafe da Manha", 22.9), ("Pao na Chapa", 12.9)],
        "nomes": [
            "Padaria Central",
            "Padaria Sao Paulo",
            "Panificadora Real",
            "Padaria do Bairro",
            "Padaria Colonial",
            "Padaria Forno Quente",
            "Padaria Estrela",
            "Padaria Nova Era",
            "Padaria Artesanal",
            "Padaria & Cafe",
        ],
    },
    "vegana": {
        "label": "Vegana",
        "pratos": [("Hamburguer Vegano", 36.9), ("Bowl Vegano", 34.9)],
        "nomes": [
            "Veggie House",
            "Green Vegan",
            "Plant Based",
            "Vegan Kitchen",
            "Terra Vegana",
            "Vida Vegana",
            "Roots Vegan",
            "Sem Carne",
            "Vegan Express",
            "Alma Verde",
        ],
    },
}


def _url_ifood(nome):
    return f"https://www.ifood.com.br/busca?q={quote_plus(nome)}"


def _url_food99(nome):
    return f"https://food.99app.com/pt-BR/search?keyword={quote_plus(nome)}"


def _rating_base(indice):
    return round(4.1 + (indice % 9) * 0.1, 1)


def listar_restaurantes():
    """Lista plana de restaurantes com cozinha, pratos e metadados iFood."""
    saida = []
    for chave, cat in CATEGORIAS_IFOOD.items():
        for i, nome in enumerate(cat["nomes"][:10]):
            variacao = (i % 3) * 2.5
            pratos = [
                {
                    "name": prato[0],
                    "price": round(prato[1] + variacao, 2),
                }
                for prato in cat["pratos"]
            ]
            saida.append(
                {
                    "cuisine_key": chave,
                    "cuisine": cat["label"],
                    "name": nome,
                    "rating": _rating_base(i),
                    "reviews": 150 + i * 87 + hash(nome) % 500,
                    "deliveryTime": 25 + (i % 5) * 3,
                    "deliveryFee": round(3.99 + (i % 4) * 0.5, 2),
                    "url": _url_ifood(nome),
                    "items": pratos,
                    "pratos_db": [(p["name"], p["price"]) for p in pratos],
                }
            )
    return saida


def exportar_dados_ifood_json(caminho="dados_ifood.json"):
    import json
    from pathlib import Path

    merchants = []
    for r in listar_restaurantes():
        merchants.append(
            {
                "name": r["name"],
                "cuisine": r["cuisine"],
                "rating": r["rating"],
                "reviews": r["reviews"],
                "deliveryTime": r["deliveryTime"],
                "deliveryFee": r["deliveryFee"],
                "url": r["url"],
                "items": r["items"],
            }
        )
    payload = {
        "updatedAt": date.today().isoformat(),
        "source": "catalogo_ifood",
        "merchants": merchants,
    }
    path = Path(__file__).resolve().parent / caminho
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path, len(merchants)


def exportar_dados_food99_json(caminho="dados_food99.json"):
    import json
    from pathlib import Path

    merchants = []
    for i, r in enumerate(listar_restaurantes()):
        desconto = 0.92 + (i % 5) * 0.015
        items = [
            {"name": p["name"], "price": round(p["price"] * desconto, 2)}
            for p in r["items"]
        ]
        merchants.append(
            {
                "name": r["name"],
                "cuisine": r["cuisine"],
                "rating": round(r["rating"] - 0.05, 1) if r["rating"] > 4.2 else r["rating"],
                "reviews": max(80, int(r["reviews"] * 0.85)),
                "deliveryTime": r["deliveryTime"] + 2,
                "deliveryFee": round(r["deliveryFee"] * 0.9, 2),
                "url": _url_food99(r["name"]),
                "items": items,
            }
        )
    payload = {
        "updatedAt": date.today().isoformat(),
        "source": "catalogo_food99",
        "merchants": merchants,
    }
    path = Path(__file__).resolve().parent / caminho
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path, len(merchants)


if __name__ == "__main__":
    p1, t1 = exportar_dados_ifood_json()
    p2, t2 = exportar_dados_food99_json()
    print(f"{t1} restaurantes -> {p1}")
    print(f"{t2} restaurantes -> {p2}")
