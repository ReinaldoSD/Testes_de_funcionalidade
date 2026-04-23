import requests


url = 'http://127.0.0.1:5000/cadastrar_via_imagem'


caminho_da_imagem = 'teste_camisa.jpg' 

print(f"Enviando a imagem '{caminho_da_imagem}' para a IA analisar...")

try:
   
    with open(caminho_da_imagem, 'rb') as arquivo_imagem:
        
        arquivos = {'imagem': arquivo_imagem}
        
        resposta = requests.post(url, files=arquivos)
        
        
    
    
   
    print(f"Status Code: {resposta.status_code}")
    print("Resposta do Servidor:")
    print(resposta.json())

except FileNotFoundError:
    print("Erro: Arquivo de imagem não encontrado. Verifique o caminho.")

    