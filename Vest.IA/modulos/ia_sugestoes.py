import random

# Mapas de palavras-chave 

MAPA_OCASIAO: dict[str, str] = {
    'faculdade': 'Casual',    'escola': 'Casual',       'aula': 'Casual',
    'universidade': 'Casual', 'passeio': 'Casual',      'casual': 'Casual',
    'compras': 'Casual',      'shopping': 'Casual',     'viagem': 'Casual',
    'praia': 'Casual',        'parque': 'Casual',
    'trabalho': 'Trabalho',   'escritório': 'Trabalho', 'escritorio': 'Trabalho',
    'reunião': 'Trabalho',    'reuniao': 'Trabalho',    'corporativo': 'Trabalho',
    'empresa': 'Trabalho',
    'festa': 'Festa',         'balada': 'Festa',        'aniversário': 'Festa',
    'aniversario': 'Festa',   'comemoração': 'Festa',   'comemoracao': 'Festa',
    'bar': 'Festa',           'jantar': 'Festa',
    'casamento': 'Formal',    'formal': 'Formal',       'cerimônia': 'Formal',
    'cerimonia': 'Formal',    'formatura': 'Formal',    'evento': 'Formal',
    'academia': 'Esporte',    'treino': 'Esporte',      'corrida': 'Esporte',
    'esporte': 'Esporte',     'ginástica': 'Esporte',   'ginastica': 'Esporte',
    'musculação': 'Esporte',  'musculacao': 'Esporte',  'futebol': 'Esporte',
    'jogo': 'Esporte',
}

MAPA_CLIMA: dict[str, str] = {
    'frio': 'Frio',       'inverno': 'Frio',      'gelado': 'Frio',
    'friozinho': 'Frio',  'neve': 'Frio',
    'calor': 'Calor',     'verão': 'Calor',       'verao': 'Calor',
    'quente': 'Calor',    'sol': 'Calor',
    'ameno': 'Meia-estação',  'outono': 'Meia-estação', 'primavera': 'Meia-estação',
}

MAPA_COR: dict[str, str] = {
    'preto': 'Preto',     'branco': 'Branco',   'azul': 'Azul',
    'vermelho': 'Vermelho', 'verde': 'Verde',   'amarelo': 'Amarelo',
    'rosa': 'Rosa',       'cinza': 'Cinza',     'marrom': 'Marrom',
    'bege': 'Bege',       'listrado': 'Listrado',
}

MAPA_TIPO_EXCLUIR: dict[str, str] = {
    'sem casaco': 'Casaco',   'sem jaqueta': 'Casaco',
    'sem bermuda': 'Bermuda', 'sem calça': 'Calça',
    'sem saia': 'Saia',       'sem vestido': 'Vestido',
}

# Mapeamento de clima retornado pela API → rótulo interno
MAPA_CLIMA_API: dict[str, str] = {
    'calor': 'Calor', 'frio': 'Frio', 'meia_estacao': 'Meia-estação',
}

# Categorias de tipo por posição no corpo
TIPOS_SUPERIORES = frozenset([
    'camisa', 'camiseta', 'blusa', 'casaco', 'jaqueta',
    'moletom', 'top', 'regata', 'camisa de time ou seleção', 'camisa de time',
])
TIPOS_INFERIORES = frozenset(['calça', 'bermuda', 'short', 'saia', 'jeans'])
TIPOS_CALCADOS   = frozenset(['calçado', 'calçados', 'tenis', 'sapato', 'bota', 'sandália', 'sandalia'])
TIPOS_VESTIDO    = frozenset(['vestido'])

# Dicas de estilo por ocasião
DICAS_ESTILO: dict[str, str] = {
    'Casual':   'Confortável e despojado — ideal para o dia a dia.',
    'Trabalho': 'Elegante mas sem exagero — transmite profissionalismo.',
    'Festa':    'Estiloso e marcante — você vai arrasar!',
    'Formal':   'Sofisticado e impecável — perfeito para a ocasião.',
    'Esporte':  'Leve e funcional — ideal para o movimento.',
}

# Tipos superiores/inferiores/calçados para os looks por clima
_LOOK_SUPERIORES = {'camisa', 'camiseta', 'blusa', 'casaco', 'jaqueta', 'top', 'moletom'}
_LOOK_INFERIORES = {'calça', 'bermuda', 'short', 'saia', 'jeans'}
_LOOK_CALCADOS   = {'calçado', 'tenis', 'sapato'}


def detectar_intencao(mensagem: str, clima_api: str | None = None) -> dict:
    """
    Analisa o texto livre do usuário e extrai intenções de look.

    Args:
        mensagem:  Texto digitado pelo usuário (ex.: "quero ir à faculdade").
        clima_api: Clima retornado pela API Open-Meteo ('calor'/'frio'/'meia_estacao')
                   usado como fallback quando o clima não é mencionado na frase.

    Returns:
        Dict com chaves: ocasiao, clima, cor, tipo_excluido (podem ser None).
    """
    msg = mensagem.lower()

    ocasiao      = next((v for k, v in MAPA_OCASIAO.items()     if k in msg), None)
    clima        = next((v for k, v in MAPA_CLIMA.items()       if k in msg), None)
    cor          = next((v for k, v in MAPA_COR.items()         if k in msg), None)
    tipo_excluido= next((v for k, v in MAPA_TIPO_EXCLUIR.items() if k in msg), None)

    # Fallback de clima via API
    if not clima and clima_api:
        clima = MAPA_CLIMA_API.get(clima_api)

    return {
        'ocasiao':       ocasiao,
        'clima':         clima,
        'cor':           cor,
        'tipo_excluido': tipo_excluido,
    }


def _score_peca(peca: dict, intencao: dict) -> float:
    """
    Calcula pontuação de adequação de uma peça para a intenção detectada.

    Critérios (acumulativos):
        +4  → ocasião coincide
        +3  → clima coincide
        +2  → cor coincide
        -0.1× vezes_usada  → favorece variedade
    """
    s = 0.0
    ocasiao = intencao.get('ocasiao')
    clima   = intencao.get('clima')
    cor     = intencao.get('cor')

    if ocasiao and peca.get('ocasiao') and ocasiao.lower() in peca['ocasiao'].lower():
        s += 4
    if clima and peca.get('clima_ideal') and clima.lower() in peca['clima_ideal'].lower():
        s += 3
    if cor and peca.get('cor') and cor.lower() in peca['cor'].lower():
        s += 2
    s -= (peca.get('vezes_usada') or 0) * 0.1
    return s


def montar_look(roupas: list[dict], intencao: dict, excluir_ids: set) -> list[dict]:
    """
    Seleciona as melhores peças para compor um look completo.

    Estratégia:
        1. Filtra por categoria (superior / inferior / calçado / vestido).
        2. Exclui peças já exibidas (excluir_ids) e tipos indesejados.
        3. Ordena por score e pega a top-1 de cada categoria.
        4. Fallback: se nenhuma categoria encaixar, retorna top-3 geral.

    Args:
        roupas:      Lista de dicts de roupa (com chaves: id, tipo, cor, ocasiao, etc.).
        intencao:    Dict retornado por detectar_intencao().
        excluir_ids: Set de IDs já mostrados (para evitar repetição).

    Returns:
        Lista de dicts de roupa (look montado), pode ser vazia se não houver peças.
    """
    tipo_excluido = intencao.get('tipo_excluido')

    def _filtrar(tipos_alvo: frozenset) -> list[dict]:
        candidatos = [
            r for r in roupas
            if r.get('tipo') and r['tipo'].lower() in tipos_alvo
            and r['id'] not in excluir_ids
            and (not tipo_excluido or r['tipo'].lower() != tipo_excluido.lower())
        ]
        return sorted(candidatos, key=lambda r: _score_peca(r, intencao), reverse=True)

    superiores = _filtrar(TIPOS_SUPERIORES)
    inferiores = _filtrar(TIPOS_INFERIORES)
    calcados   = _filtrar(TIPOS_CALCADOS)
    vestidos   = _filtrar(TIPOS_VESTIDO)

    look: list[dict] = []

    if vestidos and not superiores and not inferiores:
        look.append(vestidos[0])
        if calcados:
            look.append(calcados[0])
    else:
        if superiores: look.append(superiores[0])
        if inferiores: look.append(inferiores[0])
        if calcados:   look.append(calcados[0])

    # Fallback: guarda-roupa sem categorias suficientes
    if not look:
        todos = sorted(
            [r for r in roupas if r['id'] not in excluir_ids],
            key=lambda r: _score_peca(r, intencao),
            reverse=True,
        )
        look = todos[:3]

    return look


def gerar_look_por_clima(roupas: list[dict], clima_alvo: str) -> list[dict]:
    """
    Monta um look aleatório para o clima especificado.
    Usado pelos cards automáticos de clima (calor / frio / meia-estação).

    Args:
        roupas:     Lista de dicts de todas as roupas do usuário.
        clima_alvo: String de clima ('Calor', 'Frio', 'Meia').

    Returns:
        Lista de dicts de roupa (look montado, pode ser vazia).
    """
    pecas_clima = [
        r for r in roupas
        if r.get('clima_ideal') and clima_alvo.lower() in r['clima_ideal'].lower()
    ]
    if not pecas_clima:
        pecas_clima = roupas  # fallback: sem tag de clima

    superiores = [p for p in pecas_clima if p.get('tipo') and p['tipo'].lower() in _LOOK_SUPERIORES]
    inferiores = [p for p in pecas_clima if p.get('tipo') and p['tipo'].lower() in _LOOK_INFERIORES]
    calcados   = [p for p in pecas_clima if p.get('tipo') and p['tipo'].lower() in _LOOK_CALCADOS]

    look: list[dict] = []
    if superiores: look.append(random.choice(superiores))
    if inferiores: look.append(random.choice(inferiores))
    if calcados:   look.append(random.choice(calcados))

    if not look and pecas_clima:
        look = random.sample(pecas_clima, min(2, len(pecas_clima)))

    return look


def gerar_texto_look(look_pecas: list[dict], intencao: dict, clima_api: str | None) -> dict:
    """
    Gera título, descrição e resposta textual para o look montado.

    Returns:
        Dict com: titulo, descricao, resposta_ia, clima, ocasiao.
    """
    ocasiao = intencao.get('ocasiao')
    clima   = intencao.get('clima') or clima_api or '—'

    ocasiao_label = ocasiao or 'o seu dia'
    nomes_tipos   = [p.get('tipo') or p['nome'] for p in look_pecas]

    if len(nomes_tipos) == 1:
        desc_pecas = nomes_tipos[0]
    elif len(nomes_tipos) == 2:
        desc_pecas = f"{nomes_tipos[0]} com {nomes_tipos[1]}"
    else:
        desc_pecas = f"{', '.join(nomes_tipos[:-1])} e {nomes_tipos[-1]}"

    dica = DICAS_ESTILO.get(ocasiao, 'Uma combinação equilibrada para o seu estilo.')

    frases_intro = [
        f"Montei um look pensando em <strong>{ocasiao_label}</strong>! 🎯",
        f"Aqui está uma combinação perfeita para <strong>{ocasiao_label}</strong>! ✨",
        f"Separei esse look especialmente para <strong>{ocasiao_label}</strong>! 👗",
    ]
    resposta_ia = f"{random.choice(frases_intro)} Combinei <em>{desc_pecas}</em>. {dica} Gostou? 😊"

    cores = list({p['cor'] for p in look_pecas if p.get('cor')})
    desc_look = f"<strong>{desc_pecas.capitalize()}</strong> — {dica}"
    if cores:
        desc_look += f" Paleta de cores: {', '.join(cores)}."
    if clima and clima != '—':
        desc_look += f" Adequado para clima <strong>{clima}</strong>."

    return {
        'titulo':      f"Look para {ocasiao_label.capitalize()}" if ocasiao else "Look do Dia",
        'descricao':   desc_look,
        'resposta_ia': resposta_ia,
        'clima':       clima,
        'ocasiao':     ocasiao or '—',
    }
