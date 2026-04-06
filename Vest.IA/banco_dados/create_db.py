import sqlite3

def criar_banco():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # tabela roupas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS roupas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        tipo TEXT,
        cor TEXT,
        ocasiao TEXT,
        imagem TEXT,
        vezes_usada INTEGER DEFAULT 0
    )
    ''')

    # tabela histórico
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roupa_id INTEGER,
        data_uso TEXT,
        FOREIGN KEY (roupa_id) REFERENCES roupas(id)
    )
    ''')

    conn.commit()
    conn.close()

    print("Banco criado com sucesso!")

# execute
if __name__ == "__main__":
    criar_banco()