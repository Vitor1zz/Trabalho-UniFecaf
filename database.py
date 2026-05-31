"""Leituras para a API Flask usando tbl_usuarios, tbl_restaurantes, tbl_comidas."""

from mysql.connector import Error

from conexao import conectar
import trivagofoodsql


class DatabaseError(Exception):
    pass


def init_database():
    try:
        trivagofoodsql.criar_tabelas()
        trivagofoodsql.popular_dados_iniciais()
    except Error as exc:
        raise DatabaseError(f"Erro ao inicializar banco: {exc}") from exc


def user_exists(email):
    conexao = conectar()
    try:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute(
            "SELECT 1 FROM tbl_usuarios WHERE email_usuario = %s LIMIT 1",
            (email.lower(),),
        )
        return cursor.fetchone() is not None
    except Error as exc:
        raise DatabaseError(str(exc)) from exc
    finally:
        conexao.close()


def get_user_by_email(email):
    conexao = conectar()
    try:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT nome_usuario AS name, email_usuario AS email, senha_usuario AS password
            FROM tbl_usuarios
            WHERE email_usuario = %s
            LIMIT 1
            """,
            (email.lower(),),
        )
        return cursor.fetchone()
    except Error as exc:
        raise DatabaseError(str(exc)) from exc
    finally:
        conexao.close()


def create_user(name, email, password):
    try:
        user_id = trivagofoodsql.inserir_usuario(name, email, password)
    except Error as exc:
        raise DatabaseError(f"Erro ao cadastrar: {exc}") from exc
    if user_id is None:
        raise DatabaseError("E-mail ja cadastrado.")


def _comida_para_item(row):
    preco = float(row["preco_comida"] or 0)
    return {
        "dish": row["nome_comida"],
        "protein": 25,
        "calories": 500,
        "iFoodPrice": preco,
        "food99Price": round(preco * 0.95, 2),
        "iFoodDelivery": 30,
        "food99Delivery": 28,
        "link": "#",
    }


def fetch_restaurants():
    conexao = conectar()
    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id_restaurante, nome_restaurante, avaliacao_restaurante, cozinha_restaurante
            FROM tbl_restaurantes
            ORDER BY avaliacao_restaurante DESC, nome_restaurante ASC
            """
        )
        restaurants = cursor.fetchall()

        cursor.execute(
            """
            SELECT c.nome_comida, c.preco_comida, ca.variedades_cardapio
            FROM tbl_comidas c
            LEFT JOIN tbl_cardapio ca ON c.tipo_comida = ca.id_cardapio
            ORDER BY c.id_comida ASC
            """
        )
        todas_comidas = cursor.fetchall()

        result = []
        for restaurant in restaurants:
            cozinha = (restaurant["cozinha_restaurante"] or "").lower()
            itens_cozinha = [
                _comida_para_item(row)
                for row in todas_comidas
                if (row.get("variedades_cardapio") or "").lower() == cozinha
            ]
            if not itens_cozinha and todas_comidas:
                itens_cozinha = [_comida_para_item(row) for row in todas_comidas]

            result.append(
                {
                    "name": restaurant["nome_restaurante"],
                    "rating": float(restaurant["avaliacao_restaurante"] or 0),
                    "nutritionSeal": cozinha in ("saudavel", "japonesa", "vegana", "marmita"),
                    "cuisine": restaurant["cozinha_restaurante"] or "",
                    "items": itens_cozinha,
                }
            )
        return result
    except Error as exc:
        raise DatabaseError(str(exc)) from exc
    finally:
        conexao.close()
