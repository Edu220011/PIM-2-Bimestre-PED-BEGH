# -*- coding: utf-8 -*-
"""
Script simples para testar a conexao HTTP com o servidor proxy,
retornando um codigo de saida (Exit Code) para o script .bat.
- 0: Sucesso
- 1: Falha
"""
import json
import os
import sys
from datetime import datetime

# Configura saida para evitar erros de codificacao no Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Tenta usar requests primeiro (mais robusto para bypass de proxy)
try:
    import requests
    USE_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    USE_REQUESTS = False

# Aumenta o timeout para 30s para redes com proxy corporativo lento
REQUEST_TIMEOUT = 30 

# Desabilita proxy corporativo para redes locais (192.168.x.x)
# CRITICO: Em redes com Forefront TMG, o proxy bloqueia conexoes internas
os.environ['NO_PROXY'] = '192.168.0.0/16,127.0.0.1,localhost'

def testar_conexao_servidor():
    """
    Tenta conectar ao servidor e retorna o codigo de saida.
    """
    # --- 1. Carregar Configuracoes ---
    try:
        # Carrega config_cliente.json da mesma pasta (maq2)
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config_cliente.json') 
        
        with open(config_path, 'r', encoding='utf-8') as f:
            CONFIG_CLIENT = json.load(f)
            
    except FileNotFoundError:
        # Mensagem de erro que aparece no terminal
        print("-> ERRO FATAL: Arquivo 'config_cliente.json' nao encontrado.")
        print(f"Caminho procurado: {config_path}")
        return 1
    except json.JSONDecodeError:
        print("-> ERRO FATAL: Falha ao ler 'config_cliente.json'. Verifique a formatacao JSON.")
        return 1

    SERVER_HOST = CONFIG_CLIENT.get('server_host', '127.0.0.1')
    SERVER_PORT = CONFIG_CLIENT.get('server_port', 8080)
    
    BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
    PING_URL = f"{BASE_URL}/ping"

    print("=" * 60)
    print(f">> Testando conexao com: {BASE_URL}")
    print("=" * 60)
    
    # --- 2. Conectar ---
    try:
        if USE_REQUESTS:
            # Metodo 1: Requests com trust_env=False (mais agressivo)
            session = requests.Session()
            session.trust_env = False  # Ignora TODAS as variaveis de proxy
            session.proxies = {'http': None, 'https': None, 'no': '*'}
            
            response = session.get(PING_URL, timeout=REQUEST_TIMEOUT)
            data = response.json()
        else:
            # Metodo 2: urllib sem ProxyHandler (fallback)
            proxy_handler = urllib.request.ProxyHandler({})
            opener = urllib.request.build_opener(proxy_handler)
            
            req = urllib.request.Request(PING_URL)
            response = opener.open(req, timeout=REQUEST_TIMEOUT)
            
            response_data = response.read().decode('utf-8')
            data = json.loads(response_data)
        
        # Analisa a resposta
        if data.get('status') == 'online':
            print("\n[SUCESSO] CONEXAO BEM-SUCEDIDA! Servidor Online.")
            print(f"   Servidor respondeu em: {data.get('timestamp')}")
            return 0 # SUCESSO!
        else:
            print(f"\n[AVISO] Servidor respondeu, mas com status inesperado.")
            return 1

    except Exception as e:
        error_msg = str(e).lower()
        if 'timed out' in error_msg or 'timeout' in error_msg:
            print("\n[FALHA] TEMPO ESGOTADO (TIMEOUT):")
            print("   O servidor esta muito lento ou o trafego de rede esta sendo bloqueado.")
        else:
            print("\n[FALHA] FALHA NA CONEXAO:")
            print(f"   Nao foi possivel alcancar {BASE_URL}. Erro: {e}")
            print("   Verifique o IP e o Firewall da Maquina 1.")
        return 1

if __name__ == '__main__':
    # Define o codigo de saida do script
    sys.exit(testar_conexao_servidor())
