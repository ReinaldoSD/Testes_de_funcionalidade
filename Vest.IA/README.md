<div align="center">

<img src="static/logo2.png" alt="Vest.IA Logo" width="180"/>

# Vest.IA — Seu Guarda-Roupa Digital

**Guarda-roupa digital com inteligência artificial**



> Projeto acadêmico desenvolvido pelo **Grupo 2** da disciplina de **PIEC 1** — Engenharia da Computação, UABJ/UFRPE.

</div>

---

## 📋 Índice



- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Arquitetura](#arquitetura)
- [Tecnologias](#tecnologias)
- [Banco de Dados](#banco-de-dados)
- [Módulos de IA](#módulos-de-ia)
- [Como Executar](#como-executar)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Estrutura de Arquivos](#estrutura-de-arquivos)
- [Equipe](#equipe)
---

## 🧠 Sobre o Projeto

O **Vest.IA** resolve um problema cotidiano: pessoas com muitas roupas que perdem tempo escolhendo o que vestir, esquecem peças que possuem e raramente consideram o clima do dia.

O sistema funciona como um **guarda-roupa digital inteligente**. O usuário fotografa suas peças e a IA identifica automaticamente o tipo, a cor, a ocasião e o clima ideal de cada uma. A partir daí, o sistema sugere combinações de looks prontos levando em conta o **clima em tempo real** e o **contexto descrito pelo usuário**.

---

## ✨ Funcionalidades

### 👗 Guarda-Roupa Digital
- **Cadastro por foto com IA** — envie uma ou mais fotos de uma peça e o sistema preenche tipo, cor, ocasião e clima automaticamente usando o modelo Fashion-CLIP
- **Cadastro manual** — ajuste ou preencha os dados diretamente antes de salvar
- **Catálogo completo** — visualize todas as suas peças com filtros por tipo, cor e ocasião
- **Edição e exclusão** — atualize dados ou remova peças a qualquer momento; os arquivos de imagem são deletados junto com o registro

### 🤖 Inteligência Artificial
- **Classificação automática de imagens** — reconhece 13 tipos de peças, 13 cores/padrões, 5 ocasiões e 3 faixas climáticas
- **Sugestão de looks por clima** — três combinações prontas (para calor, frio e meia-estação) exibidas automaticamente no painel de sugestões
- **Stylist virtual por chat** — descreva em texto livre o que você precisa ("quero ir a uma festa hoje com frio") e o sistema monta um look completo com superior, inferior e calçado
- **Busca personalizada** — filtre suas peças por texto livre com interpretação de intenção (ocasião, clima, cor)
- **Variedade garantida** — peças menos usadas ganham prioridade nas sugestões; looks já mostrados são excluídos automaticamente ao pedir uma nova sugestão

### 🌤️ Clima em Tempo Real
- Consulta automática à API **Open-Meteo** com base na localização configurada
- Classifica o dia como **Calor** (≥ 25°C), **Frio** (≤ 19°C) ou **Meia-estação** (entre os dois)
- Fallback automático para meia-estação caso a consulta falhe — o sistema nunca trava

### 📊 Histórico e Estatísticas
- **Histórico de uso** — registro cronológico de cada vez que uma peça foi marcada como usada
- **Contador de utilizações** — cada peça acumula quantas vezes foi usada
- **Destaques no dashboard** — as 5 peças menos utilizadas ficam em evidência na tela inicial, junto com o total do guarda-roupa

### 👤 Conta e Perfil
- **Cadastro com verificação por e-mail** — um código de 6 dígitos é enviado ao e-mail informado; a conta só é criada após a confirmação
- **Recuperação de senha** — fluxo seguro com código de verificação por e-mail
- **Atualização de dados** — troca de nome, e-mail (com confirmação por código) e foto de perfil
- **Alteração de senha** — com validação da senha atual antes de permitir a troca

### 🔒 Segurança
- Senhas armazenadas com hash **PBKDF2** (Werkzeug Security) — nunca em texto puro
- Todas as rotas protegidas por decorador de autenticação (`@login_obrigatorio`)
- Isolamento total de dados — cada usuário acessa apenas suas próprias peças
- Limite de 16 MB por upload de imagem
- Chaves de API em variáveis de ambiente, nunca no código

---

## 🏗️ Arquitetura

O sistema segue o padrão **MVC (Model-View-Controller)** sobre o framework Flask:


```text
Navegador  ──►  routes.py (Controller)  ──►  banco_dados/ (Model)
                      │                            │
                      ├──►  modulos/  (IA)         ├──► create_db.py (Setup)
                      ├──►  utils/   (apoio)       ├──► database.py  (CRUD)
                      └──►  templates/ (View)      └──► vest.ia.db   (SQLite)
```

- **Model** → `banco_dados/database.py` gerencia todas as operações no SQLite
- **View** → `templates/` com páginas HTML renderizadas pelo Jinja2
- **Controller** → `routes.py` centraliza todas as rotas e endpoints da API REST

---

## 🛠️ Tecnologias

| Camada | Tecnologia | Função |
|---|---|---|
| Back-end | Python 3.11+ / Flask | Servidor web e lógica de negócio |
| Banco de Dados | SQLite 3 (modo WAL) | Persistência local de dados |
| Segurança | Werkzeug Security (PBKDF2) | Hash criptográfico de senhas |
| Front-end | HTML5 + Tailwind CSS | Interface responsiva via CDN |
| Motor de IA | PyTorch + HuggingFace Transformers | Infraestrutura para o modelo de visão |
| Modelo de Visão | Fashion-CLIP (patrickjohncyh) | Classificação de roupas por imagem |
| Clima | API Open-Meteo | Temperatura atual em tempo real |
| E-mail | API Brevo | Envio de códigos de verificação |
| Imagens | Pillow (PIL) | Conversão e salvamento de fotos |

---

## 🗄️ Banco de Dados

Quatro tabelas relacionais no arquivo `banco_dados/vest.ia.db`:

```
usuarios          roupas               fotos_roupas      historico
─────────         ──────────           ────────────      ─────────
id (PK)           id (PK)              id (PK)           id (PK)
nome              usuario_id (FK)      roupa_id (FK)     roupa_id (FK)
email (único)     nome                 caminho           data_uso
senha (hash)      tipo
foto_url          cor
data_cadastro     ocasiao
                  clima_ideal
                  vezes_usada
                  data_cadastro
```

> Uma roupa pode ter **múltiplas fotos** (relação 1:N com `fotos_roupas`).
> A exclusão de uma peça remove automaticamente seus registros em cascata e os arquivos físicos do servidor.

---

## 🤖 Módulos de IA

### `modulos/ia_classificador.py`
Usa o **Fashion-CLIP** para comparar cada foto enviada com descrições textuais de cada categoria e retornar a mais compatível. Quando o usuário envia várias fotos da mesma peça, o atributo mais votado entre todas as imagens é o resultado final.

**Categorias reconhecidas:**

| Atributo | Opções |
|---|---|
| Tipo | Camisa, Camiseta, Camisa de Time, Blusa, Casaco, Calça, Bermuda, Saia, Vestido, Acessório, Calçado *(11 tipos)* |
| Cor | Preto, Branco, Cinza, Azul, Vermelho, Verde, Amarelo, Rosa, Marrom, Bege, Listrado, Xadrez, Colorido *(13 opções)* |
| Ocasião | Casual, Formal, Trabalho, Festa, Esporte |
| Clima | Calor, Frio, Meia-estação |

O modelo é carregado **uma única vez** na inicialização e fica em memória. Se não estiver em cache local (`instance/fashion-clip/`), é baixado automaticamente do HuggingFace. Executa em **GPU (CUDA)** se disponível, ou em **CPU** caso contrário.

### `modulos/ia_sugestoes.py`
Motor de recomendação baseado em **pontuação heurística** — rápido e determinístico:

- `detectar_intencao()` — interpreta texto livre e extrai ocasião, clima, cor e tipo a excluir
- `_score_peca()` — pontua cada peça: **+4** por ocasião, **+3** por clima, **+2** por cor, **-0,1** por utilização prévia
- `montar_look()` — seleciona o melhor conjunto: 1 superior + 1 inferior + 1 calçado (ou vestido + calçado)
- `gerar_look_por_clima()` — monta look aleatório por faixa climática para os cards automáticos
- `gerar_texto_look()` — gera a resposta em linguagem natural apresentada ao usuário

---

## 🚀 Como Executar

### Pré-requisitos
- Python 3.11 ou superior
- pip

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/vest-ia.git
cd vest-ia
```

### 2. Crie e ative um ambiente virtual
```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto (veja a seção abaixo).

### 5. Inicie o servidor
```bash
python app.py
```

Acesse em: **http://localhost:7860**

> **Primeira execução:** o banco de dados é criado automaticamente. Se o modelo Fashion-CLIP não estiver em cache, o download será feito automaticamente (~600 MB).

---

## ⚙️ Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:

```env
FLASK_SECRET_KEY=sua_chave_secreta_longa_e_aleatoria
BREVO_API_KEY=sua_chave_da_api_brevo
```

| Variável | Descrição |
|---|---|
| `FLASK_SECRET_KEY` | Chave usada para assinar os cookies de sessão. Use qualquer string longa e aleatória. |
| `BREVO_API_KEY` | Chave obtida no painel da plataforma [Brevo](https://brevo.com), necessária para envio de e-mails. |

---

## 📁 Estrutura de Arquivos

```
vest-ia/
│
├── app.py                      # Ponto de entrada — inicializa Flask e banco
├── routes.py                   # Todas as rotas e endpoints da API REST
│
├── banco_dados/
│   ├── create_db.py            # Criação das tabelas do banco
│   ├── database.py             # Funções de acesso e consulta ao SQLite
│   └── vest.ia.db              # Banco de dados (gerado automaticamente)
│
├── modulos/
│   ├── ia_classificador.py     # Classificação de roupas via Fashion-CLIP
│   └── ia_sugestoes.py         # Motor de sugestão e montagem de looks
│
├── utils/
│   ├── auth_utils.py           # Decorador de autenticação @login_obrigatorio
│   ├── clima_utils.py          # Consulta de temperatura via Open-Meteo
│   ├── email_utils.py          # Envio de e-mails de verificação via Brevo
│   └── imagem_utils.py         # Salvamento e conversão de imagens (Pillow)
│
├── templates/                  # Páginas HTML (Jinja2)
│   ├── layout.html             # Template base com sidebar e scripts comuns
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── cadastrar_roupa.html
│   ├── minhas_roupas.html
│   ├── sugestoes.html
│   ├── historico.html
│   ├── perfil.html
│   ├── alterar_dados.html
│   └── esquecisenha.html
│
├── static/
│   ├── logo.png
│   └── uploads/                # Fotos das roupas (organizadas por tipo)
│
├── instance/
│   └── fashion-clip/           # Cache local do modelo Fashion-CLIP
│
├── .env                        # Variáveis de ambiente (não versionado)
├── .gitignore
└── requirements.txt
```

---

## 👥 Equipe

Projeto desenvolvido pelo **Grupo 2** da disciplina de **PIEC 1** — Engenharia da Computação, UABJ/UFRPE.

| Integrante | Responsabilidade principal |
|---|---|
| Reinaldo Sergio Dias da Silva | Estrutura do servidor e autenticação |
| José Ednaldo dos Santos Filho | Integração climática e sugestões por look |
| Luiz Eduardo Cordeiro Araujo | Classificação de imagens com IA |
| Everton Guilherme Marinho Silva | Interface visual e tela de chatbot |
| William Rodrigues de Freitas | Modelagem e estruturação do banco de dados |

> **Orientador:** Prof. Dr. Sabi Yari Moïse BANDIRI

---

<div align="center">

</div>
