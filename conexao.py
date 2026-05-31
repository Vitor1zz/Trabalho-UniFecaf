import mysql.connector


def conectar():
    conexao = mysql.connector.connect(
        host="localhost",
        user="root",
        password="241272ita",
        database="trivagofood1"
    )

    return conexao