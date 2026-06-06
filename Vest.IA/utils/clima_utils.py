import requests

#  Configuração de localização padrão: Belo Jardim-PE
LATITUDE  = -8.33
LONGITUDE = -36.42
TIMEOUT   = 5       # Tempo em segundos

# Referências para temperatura (°C)
LIMITE_CALOR = 25
LIMITE_FRIO  = 19


def obter_clima_local() -> tuple[str | None, float | None]:
    """
    Consulta a temperatura atual via Open-Meteo e classifica o clima.

    Returns:
        Tupla (clima, temperatura):
            clima       → 'calor' | 'frio' | 'meia_estacao' | None
            temperatura → float em °C ou None em caso de falha
    """

    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={LATITUDE}&longitude={LONGITUDE}"
        f"&current=temperature_2m"
    )
    try:
        resposta = requests.get(url, timeout=TIMEOUT)
        resposta.raise_for_status()
        dados = resposta.json()
        temp = dados.get("current", {}).get("temperature_2m")
        if temp is not None:
            if temp >= LIMITE_CALOR:
                return "calor", temp
            elif temp <= LIMITE_FRIO:
                return "frio", temp
            else:
                return "meia_estacao", temp
    except Exception as e:
        print(f"[clima_utils] Erro na API de Clima: {e}. Retornando fallback.")
    return None, None
