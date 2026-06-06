import os
import io
from collections import Counter

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

# Configuração
BASE_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODELO_PATH = os.path.join(BASE_DIR, 'instance', 'fashion-clip')
device      = "cuda" if torch.cuda.is_available() else "cpu"


# Candidatos de classificação 
CANDIDATOS_TIPO = {
    "Camisa":                  "uma camisa social de botão de manga longa ou curta",
    "Camiseta":                "uma camiseta casual basica de algodão manga curta t-shirt",
    "Camisa de Time ou Seleção": (
        "uma camisa esportiva de futebol, camisa de time, camisa de seleção nacional, "
        "uniforme esportivo oficial, jersey de clube, camisa da seleção brasileira, "
        "camisa de jogador com escudo ou patrocinador"
    ),
    "Blusa":    "uma blusa feminina ou blusa delicada de frio ou calor",
    "Casaco":   "um casaco grosso, jaqueta, moletom, blazer ou casaco de frio",
    "Calça":    "uma calça comprida jeans, sarja, moletom ou calça social",
    "Bermuda":  "uma bermuda ou short curto casual",
    "Saia":     "uma saia feminina curta, média ou longa",
    "Vestido":  "um vestido feminino de peça única",
    "Acessório": (
        "qualquer item usado para complementar o visual, como boné, chapéu, cachecol, "
        "lenço, cinto, meia, relógio, óculos, brinco, colar, pulseira, bolsa, luva ou "
        "cachecol, não serve para cobrir o corpo principal"
    ),
    "Calçado":  "um calçado, sapato, tênis, bota ou sandália nos pés",
}

CANDIDATOS_COR = {
    "Preto":    "uma peça de roupa totalmente preta escura lisa",
    "Branco":   "uma peça de roupa totalmente branca clara lisa",
    "Cinza":    "uma peça de roupa cinza ou de cor grafite",
    "Azul":     "uma peça de roupa azul clara ou escura",
    "Vermelho": "uma peça de roupa vermelha viva ou vinho",
    "Verde":    "uma peça de roupa verde oliva, musgo ou claro",
    "Amarelo":  "uma peça de roupa amarela brilhante",
    "Rosa":     "uma peça de roupa rosa ou fúcsia",
    "Marrom":   "uma peça de roupa marrom ou cor de terra",
    "Bege":     "uma peça de roupa beige, creme ou caqui claro",
    "Listrado": "uma peça de roupa com duas cores e com listras verticais, horizontais ou diagonais",
    "Xadrez":   "uma peça que é formada somente de quadrados por toda a roupa",
    "Colorido": "uma peça de roupa colorida, estampada com muitas cores misturadas, multicolorida",
}

CANDIDATOS_OCASIAO = {
    "Casual":   "roupa casual do dia a dia, despojada e confortável para ficar em casa ou sair com amigos",
    "Formal":   "roupa formal de gala, terno completo, alfaiataria ou vestido sofisticado de casamento",
    "Trabalho": "roupa de trabalho formal-casual, escritório ou ambiente corporativo sério",
    "Festa":    "roupa estilosa de festa, balada ou evento noturno comemorativo",
    "Esporte":  "roupa esportiva de academia, treino, corrida, tactel ou dry-fit",
}

CANDIDATOS_CLIMA = {
    "Calor":        "uma roupa fresca de verão, sem mangas, curta, ideal para dias de sol forte e calor",
    "Frio":         "uma roupa pesada de inverno, grossa, de lã ou couro, feita para proteger de frio intenso",
    "Meia-estação": (
        "uma roupa leve de outono ou primavera, de meia manga, nem muito quente nem muito fresca, "
        "perfeita para clima ameno ou meia-estação"
    ),
}



def _carregar_modelo() -> tuple:
    """Carrega o modelo e processador Fashion-CLIP (local ou download)."""
    try:
        m = CLIPModel.from_pretrained(MODELO_PATH, local_files_only=True).to(device)
        p = CLIPProcessor.from_pretrained(MODELO_PATH, local_files_only=True)
        print("[ia_classificador] Modelo carregado do cache local.")
    except Exception:
        print("[ia_classificador] Cache não encontrado — baixando Fashion-CLIP...")
        m = CLIPModel.from_pretrained("patrickjohncyh/fashion-clip").to(device)
        p = CLIPProcessor.from_pretrained("patrickjohncyh/fashion-clip")
        os.makedirs(MODELO_PATH, exist_ok=True)
        m.save_pretrained(MODELO_PATH)
        p.save_pretrained(MODELO_PATH)
        print("[ia_classificador] Modelo salvo em cache.")
    return m, p


# Carregamento único na importação do módulo
modelo, processador = _carregar_modelo()


def _classificar(image: Image.Image, candidatos: dict) -> str:
    """
    Classifica uma imagem PIL contra um dicionário de candidatos texto→descrição.

    Args:
        image:      Imagem PIL em modo RGB.
        candidatos: Dict {rótulo: descrição_textual}.

    Returns:
        Rótulo vencedor (maior similaridade CLIP).
    """
    rotulos  = list(candidatos.keys())
    textos   = list(candidatos.values())
    inputs   = processador(text=textos, images=image, return_tensors="pt", padding=True).to(device)
    with torch.no_grad():
        outputs = modelo(**inputs)
    probs = outputs.logits_per_image.softmax(dim=-1)
    return rotulos[probs.argmax().item()]


def classificar_imagem(img_bytes_list: list[bytes]) -> dict:
    """
    Classifica uma ou mais imagens (bytes) e retorna os atributos por votação.

    Args:
        img_bytes_list: Lista de conteúdo bruto de imagens (bytes).

    Returns:
        Dict com chaves: nome, tipo, cor, ocasiao, clima.
    """
    votos_tipo    = []
    votos_cor     = []
    votos_ocasiao = []
    votos_clima   = []

    for img_bytes in img_bytes_list:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        votos_tipo.append(_classificar(img, CANDIDATOS_TIPO))
        votos_cor.append(_classificar(img, CANDIDATOS_COR))
        votos_ocasiao.append(_classificar(img, CANDIDATOS_OCASIAO))
        votos_clima.append(_classificar(img, CANDIDATOS_CLIMA))

    tipo    = Counter(votos_tipo).most_common(1)[0][0]
    cor     = Counter(votos_cor).most_common(1)[0][0]
    ocasiao = Counter(votos_ocasiao).most_common(1)[0][0]
    clima   = Counter(votos_clima).most_common(1)[0][0]

    sufixo = cor.lower() if cor in ("Listrado", "Colorido") else cor
    nome   = f"{tipo} {sufixo}"

    return {"nome": nome, "tipo": tipo, "cor": cor, "ocasiao": ocasiao, "clima": clima}
