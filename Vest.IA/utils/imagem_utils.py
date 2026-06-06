import os
import uuid
import io
import base64

from PIL import Image


def salvar_imagem_base64(fb64: str, diretorio: str) -> str:
    """
    Decodifica uma imagem em base64, converte para JPEG e salva em disco.

    Args:
        fb64:      String base64 (com ou sem prefixo data:...;base64,).
        diretorio: Pasta de destino (criada automaticamente se não existir).

    Returns:
        Nome do arquivo salvo (ex.: 'a3f8...hex.jpg').
    """
    if ',' in fb64:
        fb64 = fb64.split(',')[1]

    conteudo = base64.b64decode(fb64)
    img = Image.open(io.BytesIO(conteudo)).convert('RGB')

    os.makedirs(diretorio, exist_ok=True)
    nome_arquivo = f"{uuid.uuid4().hex}.jpg"
    caminho_completo = os.path.join(diretorio, nome_arquivo)
    img.save(caminho_completo, 'JPEG')

    return nome_arquivo


def salvar_foto_perfil(stream, diretorio: str) -> str | None:
    """
    Abre um stream de arquivo de imagem (vindo de request.files),
    converte para JPEG e salva no diretório de perfis.

    Args:
        stream:    File-like object (ex.: foto.stream do Flask).
        diretorio: Pasta de destino (criada automaticamente se não existir).

    Returns:
        Nome do arquivo salvo, ou None em caso de erro.
    """
    try:
        img = Image.open(stream).convert('RGB')
        os.makedirs(diretorio, exist_ok=True)
        nome_arquivo = f"{uuid.uuid4().hex}.jpg"
        caminho_completo = os.path.join(diretorio, nome_arquivo)
        img.save(caminho_completo, 'JPEG')
        return nome_arquivo
    except Exception as e:
        print(f"[imagem_utils] Erro ao salvar foto de perfil: {e}")
        return None
