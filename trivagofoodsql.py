"""
INSERT no MySQL usando o schema do projeto (tbl_usuarios, tbl_restaurantes, etc.)
"""

from mysql.connector import Error, IntegrityError

from conexao import conectar


def _cursor(connection, dictionary=True):
    return connection.cursor(dictionary=dictionary)


def criar_tabelas():
    """Cria as tabelas do banco trivagofood1 (se ainda nao existirem)."""
    comandos = [
        """
        CREATE TABLE IF NOT EXISTS tbl_usuarios (
            id_usuario INT AUTO_INCREMENT PRIMARY KEY,
            nome_usuario VARCHAR(100) NOT NULL,
            email_usuario VARCHAR(100) UNIQUE NOT NULL,
            senha_usuario VARCHAR(255) NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS tbl_restaurantes (
            id_restaurante INT AUTO_INCREMENT PRIMARY KEY,
            nome_restaurante VARCHAR(100) NOT NULL,
            avaliacao_restaurante DECIMAL(10, 2),
            cozinha_restaurante VARCHAR(50)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS tbl_cardapio (
            id_cardapio INT AUTO_INCREMENT PRIMARY KEY,
            variedades_cardapio VARCHAR(100)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS tbl_comidas (
            id_comida INT AUTO_INCREMENT PRIMARY KEY,
            nome_comida VARCHAR(100) NOT NULL,
            tipo_comida INT,
            preco_comida DECIMAL(10, 2),
            CONSTRAINT fk_comida_cardapio
                FOREIGN KEY (tipo_comida) REFERENCES tbl_cardapio (id_cardapio)
        )
        """,
    ]

    conexao = conectar()
    try:
        cursor = _cursor(conexao)
        for comando in comandos:
            cursor.execute(comando)
        conexao.commit()
        print("Tabelas criadas ou ja existentes.")
    finally:
        conexao.close()


def inserir_usuario(nome, email, senha):
    """Insere em tbl_usuarios. Retorna id_usuario ou None se e-mail duplicado."""
    sql = """
        INSERT INTO tbl_usuarios (nome_usuario, email_usuario, senha_usuario)
        VALUES (%s, %s, %s)
    """
    conexao = conectar()
    try:
        cursor = _cursor(conexao, dictionary=False)
        cursor.execute(sql, (nome, email.strip().lower(), senha))
        conexao.commit()
        user_id = cursor.lastrowid
        print(f"Usuario inserido (id {user_id}): {email}")
        return user_id
    except IntegrityError:
        print(f"E-mail ja cadastrado: {email}")
        return None
    except Error as exc:
        print(f"Erro ao inserir usuario: {exc}")
        raise
    finally:
        conexao.close()


def inserir_restaurante(nome, avaliacao, cozinha, silent=False):
    """Insere em tbl_restaurantes. Retorna id_restaurante."""
    sql = """
        INSERT INTO tbl_restaurantes (nome_restaurante, avaliacao_restaurante, cozinha_restaurante)
        VALUES (%s, %s, %s)
    """
    conexao = conectar()
    try:
        cursor = _cursor(conexao, dictionary=False)
        cursor.execute(sql, (nome, avaliacao, cozinha))
        conexao.commit()
        restaurant_id = cursor.lastrowid
        if not silent:
            print(f"Restaurante inserido (id {restaurant_id}): {nome}")
        return restaurant_id
    except Error as exc:
        print(f"Erro ao inserir restaurante: {exc}")
        raise
    finally:
        conexao.close()


def inserir_cardapio(variedade):
    """Insere em tbl_cardapio. Retorna id_cardapio."""
    sql = "INSERT INTO tbl_cardapio (variedades_cardapio) VALUES (%s)"
    conexao = conectar()
    try:
        cursor = _cursor(conexao, dictionary=False)
        cursor.execute(sql, (variedade,))
        conexao.commit()
        cardapio_id = cursor.lastrowid
        print(f"Cardapio inserido (id {cardapio_id}): {variedade}")
        return cardapio_id
    except Error as exc:
        print(f"Erro ao inserir cardapio: {exc}")
        raise
    finally:
        conexao.close()


def inserir_comida(nome, id_cardapio, preco, silent=False):
    """Insere em tbl_comidas. tipo_comida = id do cardapio."""
    sql = """
        INSERT INTO tbl_comidas (nome_comida, tipo_comida, preco_comida)
        VALUES (%s, %s, %s)
    """
    conexao = conectar()
    try:
        cursor = _cursor(conexao, dictionary=False)
        cursor.execute(sql, (nome, id_cardapio, preco))
        conexao.commit()
        comida_id = cursor.lastrowid
        if not silent:
            print(f"Comida inserida (id {comida_id}): {nome}")
        return comida_id
    except Error as exc:
        print(f"Erro ao inserir comida: {exc}")
        raise
    finally:
        conexao.close()


def buscar_ou_criar_cardapio(variedade):
    conexao = conectar()
    try:
        cursor = _cursor(conexao)
        cursor.execute(
            "SELECT id_cardapio FROM tbl_cardapio WHERE variedades_cardapio = %s LIMIT 1",
            (variedade,),
        )
        row = cursor.fetchone()
        if row:
            return row["id_cardapio"]
    finally:
        conexao.close()
    return inserir_cardapio(variedade)


def restaurante_existe(nome):
    conexao = conectar()
    try:
        cursor = _cursor(conexao)
        cursor.execute(
            "SELECT 1 FROM tbl_restaurantes WHERE nome_restaurante = %s LIMIT 1",
            (nome,),
        )
        return cursor.fetchone() is not None
    finally:
        conexao.close()


def popular_catalogo_ifood():
    """Insere 10 restaurantes por categoria do iFood (idempotente por nome)."""
    from catalogo_ifood import (
        CATEGORIAS_IFOOD,
        exportar_dados_food99_json,
        exportar_dados_ifood_json,
        listar_restaurantes,
    )

    conexao = conectar()
    try:
        cursor = _cursor(conexao)
        cursor.execute("SELECT COUNT(*) AS total FROM tbl_restaurantes")
        if cursor.fetchone()["total"] >= 150:
            exportar_dados_ifood_json()
            exportar_dados_food99_json()
            return 0
    finally:
        conexao.close()

    inseridos = 0
    for restaurante in listar_restaurantes():
        nome = restaurante["name"]
        if restaurante_existe(nome):
            continue
        cozinha = restaurante["cuisine"]
        inserir_restaurante(nome, restaurante["rating"], cozinha, silent=True)
        cardapio_id = buscar_ou_criar_cardapio(cozinha.lower())
        for prato_nome, preco in restaurante["pratos_db"]:
            inserir_comida(prato_nome, cardapio_id, preco, silent=True)
        inseridos += 1

    for cat in CATEGORIAS_IFOOD.values():
        buscar_ou_criar_cardapio(cat["label"].lower())

    path_ifood, total_ifood = exportar_dados_ifood_json()
    path_99, total_99 = exportar_dados_food99_json()
    if inseridos:
        print(f"Catalogo: +{inseridos} no MySQL | iFood JSON: {total_ifood} | 99 JSON: {total_99}")
        print(f"  {path_ifood}")
        print(f"  {path_99}")
    return inseridos


def popular_dados_iniciais():
    conexao = conectar()
    try:
        cursor = _cursor(conexao)
        cursor.execute("SELECT COUNT(*) AS total FROM tbl_usuarios")
        if cursor.fetchone()["total"] == 0:
            inserir_usuario("Usuario Demo", "usuario@email.com", "123456")
            inserir_usuario("Gustavo", "gustavo@email.com", "123456")
            inserir_usuario("Demo SmartFood", "demo@smartfood.com", "123456")
        else:
            print("Usuarios ja existem.")
    except Error as exc:
        print(f"Erro MySQL: {exc}")
        raise
    finally:
        conexao.close()

    popular_catalogo_ifood()


def menu_interativo():
    print("\n=== Trivago Food - Inserir no MySQL ===\n")
    print("1 - Criar tabelas")
    print("2 - Popular dados iniciais (usuarios + catalogo iFood)")
    print("7 - Popular apenas catalogo iFood (10 por categoria)")
    print("3 - Inserir usuario (tbl_usuarios)")
    print("4 - Inserir restaurante (tbl_restaurantes)")
    print("5 - Inserir cardapio (tbl_cardapio)")
    print("6 - Inserir comida (tbl_comidas)")
    print("0 - Sair")

    while True:
        opcao = input("\nEscolha uma opcao: ").strip()

        if opcao == "0":
            break
        if opcao == "1":
            criar_tabelas()
        elif opcao == "2":
            criar_tabelas()
            popular_dados_iniciais()
        elif opcao == "3":
            nome = input("Nome: ").strip()
            email = input("E-mail: ").strip()
            senha = input("Senha: ").strip()
            inserir_usuario(nome, email, senha)
        elif opcao == "4":
            nome = input("Nome do restaurante: ").strip()
            avaliacao = float(input("Avaliacao (ex: 4.5): ").strip())
            cozinha = input("Cozinha (ex: japonesa): ").strip()
            inserir_restaurante(nome, avaliacao, cozinha)
        elif opcao == "5":
            variedade = input("Variedade do cardapio: ").strip()
            inserir_cardapio(variedade)
        elif opcao == "6":
            nome = input("Nome da comida: ").strip()
            id_cardapio = int(input("ID do cardapio (tipo_comida): ").strip())
            preco = float(input("Preco: ").strip())
            inserir_comida(nome, id_cardapio, preco)
        elif opcao == "7":
            criar_tabelas()
            popular_catalogo_ifood()
        else:
            print("Opcao invalida.")


if __name__ == "__main__":
    menu_interativo()
