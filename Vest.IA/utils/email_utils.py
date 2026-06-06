import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Configuração da API da Brevo para enviar os e-mails
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
REMETENTE_EMAIL = "vestia.noreply@gmail.com"
REMETENTE_NOME = "Vest.IA"

def enviar_email_codigo(destinatario: str, codigo: str) -> bool:

    if not BREVO_API_KEY:
        print("[email_utils_2] Erro: BREVO_API_KEY não configurada no ambiente.")
        return False

    url = "https://api.brevo.com/v3/smtp/email"
    
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    assunto = "Seu código de verificação - Vest.IA"
    corpo_texto = (
        f"Olá!\n\n"
        f"Seu código de verificação é: {codigo}\n\n"
        f"Se você não solicitou este código, ignore este e-mail."
    )
    
    # HTML simples para melhorar a entrega visual do código
    corpo_html = f"""
    <html>
        <body style="font-family: sans-serif; color: #333;">
            <h2 style="color: #4A90E2;">Vest.IA</h2>
            <p>Olá!</p>
            <p>Seu código de verificação é:</p>
            <div style="background: #f4f4f4; padding: 10px 20px; font-size: 24px; font-weight: bold; letter-spacing: 2px; display: inline-block; border-radius: 4px;">
                {codigo}
            </div>
            <p style="margin-top: 20px; font-size: 12px; color: #777;">Se você não solicitou este código, ignore este e-mail.</p>
        </body>
    </html>
    """

    payload = {
        "sender": {
            "name": REMETENTE_NOME,
            "email": REMETENTE_EMAIL
        },
        "to": [
            {
                "email": destinatario
            }
        ],
        "subject": assunto,
        "textContent": corpo_texto,
        "htmlContent": corpo_html
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code in [200, 201, 202]:
            return True
        else:
            print(f"[email_utils_2] Erro na API Brevo ({response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        print(f"[email_utils_2] Erro na requisição HTTP: {e}")
        return False