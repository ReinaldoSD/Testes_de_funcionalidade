import sqlite3
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
DB_FOLDER = os.path.join(project_root, 'banco_dados')
DB_PATH = os.path.join(DB_FOLDER, 'vest.ia.db')

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def cadastrar_roupa(nome, tipo, cor, ocasiao, clima_ideal, imagem=None):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO roupas (nome, tipo, cor, ocasiao, clima_ideal, imagem)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (nome, tipo, cor, ocasiao, clima_ideal, imagem))
    conn.commit()
    conn.close()
    print("Roupa cadastrada com sucesso")

def editar_roupa(roupa_id, nome, tipo, cor, ocasiao, clima_ideal, imagem=None):
    conn = conectar()
    cursor = conn.cursor()
    if imagem:
        cursor.execute("""
        UPDATE roupas 
        SET nome = ?, tipo = ?, cor = ?, ocasiao = ?, clima_ideal = ?, imagem = ?
        WHERE id = ?
        """, (nome, tipo, cor, ocasiao, clima_ideal, imagem, roupa_id))
    else:
        cursor.execute("""
        UPDATE roupas 
        SET nome = ?, tipo = ?, cor = ?, ocasiao = ?, clima_ideal = ?
        WHERE id = ?
        """, (nome, tipo, cor, ocasiao, clima_ideal, roupa_id))
    conn.commit()
    conn.close()
    print(f"Roupa {roupa_id} atualizada com sucesso")

def excluir_roupa(roupa_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM historico WHERE roupa_id = ?", (roupa_id,))
    cursor.execute("DELETE FROM roupas WHERE id = ?", (roupa_id,))
    conn.commit()
    conn.close()
    print(f"Roupa {roupa_id} excluída com sucesso")
