import sqlite3
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
DB_FOLDER = os.path.join(project_root, 'banco_dados')
DB_PATH = os.path.join(DB_FOLDER, 'vest.ia.db')

def conectar():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    
    conn.execute("PRAGMA journal_mode=WAL") 
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def cadastrar_roupa(nome, tipo, cor, ocasiao, clima_ideal, caminhos_fotos):
    conn = conectar()
    cursor = conn.cursor()
    
    
    cursor.execute("""
    INSERT INTO roupas (nome, tipo, cor, ocasiao, clima_ideal)
    VALUES (?, ?, ?, ?, ?)
    """, (nome, tipo, cor, ocasiao, clima_ideal))
    
    
    roupa_id = cursor.lastrowid
    
    
    for caminho in caminhos_fotos:
        cursor.execute("INSERT INTO fotos_roupas (roupa_id, caminho) VALUES (?, ?)", (roupa_id, caminho))
        
    conn.commit()
    conn.close()
    return roupa_id

def editar_roupa(roupa_id, nome, tipo, cor, ocasiao, clima_ideal):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE roupas 
    SET nome = ?, tipo = ?, cor = ?, ocasiao = ?, clima_ideal = ?
    WHERE id = ?
    """, (nome, tipo, cor, ocasiao, clima_ideal, roupa_id))
    conn.commit()
    conn.close()

def excluir_roupa(roupa_id):
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute("SELECT caminho FROM fotos_roupas WHERE roupa_id = ?", (roupa_id,))
    fotos = cursor.fetchall()
    
    cursor.execute("SELECT nome FROM roupas WHERE id = ?", (roupa_id,))
    resultado = cursor.fetchone()
    nome_roupa = resultado['nome'] if resultado else "Peça"
    
    conn.commit() 

    cursor.execute("DELETE FROM fotos_roupas WHERE roupa_id = ?", (roupa_id,))
    
    try:
        cursor.execute("DELETE FROM historico WHERE roupa_id = ?", (roupa_id,))
    except sqlite3.OperationalError:
        pass 
    cursor.execute("DELETE FROM roupas WHERE id = ?", (roupa_id,))
    
    conn.commit()
    conn.close()
    
    for foto in fotos:
        caminho_relativo = foto['caminho'].replace('/', os.sep) 
        caminho_completo = os.path.join(project_root, caminho_relativo)
        if os.path.exists(caminho_completo):
            try:
                os.remove(caminho_completo)
            except Exception as e:
                print(f"Erro ao apagar arquivo {caminho_completo}: {e}")
                
    return nome_roupa
