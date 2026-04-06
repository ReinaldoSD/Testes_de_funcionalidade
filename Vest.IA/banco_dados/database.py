import sqlite3

def conectar():
    return sqlite3.connect('database.db')

def cadastrar_roupa(nome, tipo, cor, ocasiao, imagem=None):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO roupas (nome, tipo, cor, ocasiao, imagem)
    VALUES (?, ?, ?, ?, ?)
    """, (nome, tipo, cor, ocasiao, imagem))

    conn.commit()
    conn.close()

    print("Roupa cadastrada com sucesso")