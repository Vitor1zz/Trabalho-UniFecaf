CREATE DATABASE IF NOT EXISTS trivagofood1;
USE trivagofood1;

CREATE TABLE IF NOT EXISTS tbl_usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nome_usuario VARCHAR(100) NOT NULL,
    email_usuario VARCHAR(100) UNIQUE NOT NULL,
    senha_usuario VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS tbl_restaurantes (
    id_restaurante INT AUTO_INCREMENT PRIMARY KEY,
    nome_restaurante VARCHAR(100) NOT NULL,
    avaliacao_restaurante DECIMAL(10, 2),
    cozinha_restaurante VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS tbl_cardapio (
    id_cardapio INT AUTO_INCREMENT PRIMARY KEY,
    variedades_cardapio VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS tbl_comidas (
    id_comida INT AUTO_INCREMENT PRIMARY KEY,
    nome_comida VARCHAR(100) NOT NULL,
    tipo_comida INT,
    preco_comida DECIMAL(10, 2),
    CONSTRAINT fk_comida_cardapio
        FOREIGN KEY (tipo_comida) REFERENCES tbl_cardapio (id_cardapio)
);
