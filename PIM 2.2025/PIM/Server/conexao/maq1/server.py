#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===============================================================
    SERVIDOR PROXY - SISTEMA ACADÊMICO
===============================================================
    Servidor proxy para gerenciar conexões LAN e sincronização
    de dados entre múltiplos clientes do sistema acadêmico.
    
    Funcionalidades:
    - Gerenciamento de fila de requisições (Escrita)
    - Sincronização de arquivos JSON
    - Controle de concorrência (Locks por arquivo)
===============================================================
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import threading
import queue
import time
from datetime import datetime
import logging

# ===============================================================
# CONFIGURAÇÃO DO SERVIDOR
# ===============================================================

app = Flask(__name__)
CORS(app) # Permitir CORS para requisições de diferentes máquinas

# Configurar logging
logging.basicConfig(
  level=logging.INFO,
  # Usando tags de texto simples nos logs: [ERRO], [INFO], etc.
  format='%(asctime)s - %(levelname)s - %(message)s',
  handlers=[
    logging.FileHandler('server.log', encoding='utf-8'),
    logging.StreamHandler()
  ]
)
logger = logging.getLogger(__name__)

# --- CORREÇÃO DE CAMINHO ABSOLUTO ---
# Define o diretório base do script. Isso garante que os arquivos são 
# procurados no mesmo diretório do 'server.py'.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Carregar configurações
try:
  # Tenta carregar config_server.json
  config_path = os.path.join(BASE_DIR, 'config_server.json')
  
  with open(config_path, 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)
    
except FileNotFoundError:
  logger.error(f"[ERRO] Arquivo 'config_server.json' não encontrado em: {config_path}.")
  # Força a interrupção, pois a configuração é essencial
  raise FileNotFoundError(f"config_server.json não encontrado. Verifique o caminho: {config_path}")
  
except Exception as e:
  logger.error(f"[ERRO] Erro ao carregar config_server.json: {e}")
  raise e

# Garante que DATA_DIR seja um caminho absoluto baseado no BASE_DIR
data_dir_relative = CONFIG.get('data_dir', './DATA').lstrip('./').lstrip('../')
DATA_DIR = os.path.join(BASE_DIR, data_dir_relative)

# Criar o diretório de dados se ele não existir
os.makedirs(DATA_DIR, exist_ok=True)
logger.info(f"[DIR] Diretório de dados configurado: {os.path.abspath(DATA_DIR)}")
# --- FIM DA CORREÇÃO DE CAMINHO ABSOLUTO ---


# ===============================================================
# SISTEMA DE FILA E LOCKS
# ===============================================================

# Fila para requisições de escrita (evita concorrência)
write_queue = queue.Queue()

# Locks por arquivo para sincronização
file_locks = {}
lock_manager = threading.Lock()

def get_file_lock(filename):
  """Obtém ou cria um lock para um arquivo específico"""
  with lock_manager:
    if filename not in file_locks:
      file_locks[filename] = threading.Lock()
    return file_locks[filename]

# ===============================================================
# FUNÇÕES DE MANIPULAÇÃO DE ARQUIVOS JSON
# ===============================================================

def load_json(filename):
  """Carrega arquivo JSON com tratamento de erros"""
  filepath = os.path.join(DATA_DIR, filename)
  file_lock = get_file_lock(filename)
  
  with file_lock:
    try:
      if not os.path.exists(filepath):
        logger.warning(f"[WARN] Arquivo não encontrado: {filename}. Criando novo...")
        return []
      
      if os.path.getsize(filepath) == 0:
        logger.warning(f"[WARN] Arquivo vazio: {filename}")
        return []
      
      with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        logger.info(f"[LOAD] Arquivo carregado: {filename} ({len(data) if isinstance(data, list) else 'objeto'} registros)")
        return data
    except json.JSONDecodeError as e:
      logger.error(f"[ERRO JSON] Erro ao decodificar JSON {filename}: {e}")
      return []
    except Exception as e:
      logger.error(f"[ERRO] Erro ao carregar {filename}: {e}")
      return []

def save_json(filename, data):
  """Salva arquivo JSON com tratamento de erros e backup"""
  filepath = os.path.join(DATA_DIR, filename)
  file_lock = get_file_lock(filename)
  
  with file_lock:
    try:
      # Backup antes de salvar
      if os.path.exists(filepath):
        backup_path = filepath + '.backup'
        # Cópia segura para o backup
        with open(filepath, 'r', encoding='utf-8') as f_read, \
          open(backup_path, 'w', encoding='utf-8') as f_write:
          f_write.write(f_read.read())
      
      # Salvar novo arquivo
      with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
      
      logger.info(f"[SAVE] Arquivo salvo: {filename} ({len(data) if isinstance(data, list) else 'objeto'} registros)")
      return True
    except Exception as e:
      logger.error(f"[ERRO] Erro ao salvar {filename}: {e}")
      # Restaurar backup em caso de erro
      if os.path.exists(filepath + '.backup'):
        os.replace(filepath + '.backup', filepath)
        logger.warning(f"[WARN] Backup de {filename} restaurado.")
      return False

# ===============================================================
# WORKER THREAD - PROCESSADOR DE FILA
# ===============================================================

def queue_worker():
  """Worker thread que processa a fila de requisições de escrita"""
  logger.info("[WORKER] Worker thread iniciado")
  
  while True:
    try:
      # Aguardar requisição na fila
      task = write_queue.get(timeout=1)
      
      if task is None: # Sinal de parada
        break
      
      operation = task.get('operation')
      filename = task.get('filename')
      data = task.get('data')
      callback = task.get('callback')
      
      logger.info(f"[PROC] Processando: {operation} em {filename}")
      
      # Executar operação de escrita segura
      result = save_json(filename, data)
      
      # Callback com resultado
      if callback:
        callback(result)
      
      write_queue.task_done()
      
    except queue.Empty:
      continue
    except Exception as e:
      logger.error(f"[ERRO WORKER] Erro no worker: {e}")

# Iniciar worker thread
worker_thread = threading.Thread(target=queue_worker, daemon=True)
worker_thread.start()

# ===============================================================
# ROTAS DA API
# ===============================================================

@app.route('/ping', methods=['GET'])
def ping():
  """Endpoint para verificar se o servidor está ativo"""
  return jsonify({
    'status': 'online',
    'timestamp': datetime.now().isoformat(),
    'version': '1.0.0'
  })

@app.route('/api/read/<filename>', methods=['GET'])
def read_file(filename):
  """Lê um arquivo JSON"""
  try:
    # Validar nome do arquivo (previne path traversal)
    if not filename.endswith('.json'):
      return jsonify({'error': 'Arquivo deve ter extensão .json'}), 400
    
    # Previne path traversal (../, ..\, etc)
    if '..' in filename or '/' in filename or '\\' in filename:
      return jsonify({'error': 'Nome de arquivo inválido'}), 400
    
    data = load_json(filename)
    return jsonify({
      'success': True,
      'data': data,
      'timestamp': datetime.now().isoformat()
    })
  except Exception as e:
    logger.error(f"[ERRO] Erro ao ler {filename}: {e}")
    return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/write/<filename>', methods=['POST'])
def write_file(filename):
  """Escreve em um arquivo JSON (usando fila)"""
  try:
    # Validar nome do arquivo (previne path traversal)
    if not filename.endswith('.json'):
      return jsonify({'error': 'Arquivo deve ter extensão .json'}), 400
    
    # Previne path traversal (../, ..\, etc)
    if '..' in filename or '/' in filename or '\\' in filename:
      return jsonify({'error': 'Nome de arquivo inválido'}), 400
    
    # Obter dados do request
    data = request.json.get('data')
    if data is None:
      return jsonify({'error': 'Dados não fornecidos'}), 400
    
    # Criar evento para aguardar conclusão
    result_event = threading.Event()
    result_container = {'success': False}
    
    def callback(success):
      result_container['success'] = success
      result_event.set()
    
    # Adicionar à fila
    write_queue.put({
      'operation': 'write',
      'filename': filename,
      'data': data,
      'callback': callback
    })
    
    # Aguardar processamento (timeout configurável)
    timeout = CONFIG.get('timeout', 30)
    if result_event.wait(timeout=timeout):
      if result_container['success']:
        return jsonify({
          'success': True,
          'message': f'Arquivo {filename} salvo com sucesso',
          'timestamp': datetime.now().isoformat()
        })
      else:
        return jsonify({'success': False, 'error': 'Falha ao salvar arquivo (Erro de I/O)'}), 500
    else:
      return jsonify({'success': False, 'error': f'Timeout ({timeout}s) ao processar requisição. Fila cheia?'}), 408
      
  except Exception as e:
    logger.error(f"[ERRO] Erro ao escrever {filename}: {e}")
    return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/list', methods=['GET'])
def list_files():
  """Lista todos os arquivos JSON disponíveis"""
  try:
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
    return jsonify({
      'success': True,
      'files': files,
      'count': len(files)
    })
  except Exception as e:
    return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def server_status():
  """Retorna status detalhado do servidor"""
  try:
    return jsonify({
      'status': 'running',
      'queue_size': write_queue.qsize(),
      'active_locks': len(file_locks),
      'config': {k: v for k, v in CONFIG.items() if k not in ['allowed_client_ip']}, # Não expõe configurações sensíveis
 'timestamp': datetime.now().isoformat()
    })
  except Exception as e:
    return jsonify({'error': str(e)}), 500

# ===============================================================
# INICIALIZAÇÃO DO SERVIDOR
# ===============================================================

if __name__ == '__main__':
    # Bloco de inicialização com caracteres ASCII simples para máxima compatibilidade
    print("+----------------------------------------------------------+")
    print("|          [SERVIDOR PROXY] - SISTEMA ACADÊMICO            |")
    print("+----------------------------------------------------------+")
    print()
    print(f"[HOST] Host: {CONFIG['host']}")
    print(f"[PORTA] Porta: {CONFIG['port']}")
    print(f"[DIR] Diretório de dados: {DATA_DIR}")
    print(f"[CONEX] Máximo de conexões: {CONFIG.get('max_connections', 'Não especificado')}")
    print()
    print("[SUCESSO] Servidor iniciado com sucesso!")
    print("[THREAD] Worker thread ativo para processar fila")
    print()
    print("[STOP] Pressione Ctrl+C para parar o servidor")
    print("-----------------------------------------------------------")
    print()
    
    try:
        app.run(
            host=CONFIG['host'],
            port=CONFIG['port'],
            debug=CONFIG.get('debug', False),
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n[ENCERRAR] Encerrando servidor...")
        write_queue.put(None)  # Sinal para parar worker
        worker_thread.join(timeout=5)
        print("[SUCESSO] Servidor encerrado com sucesso!")
    except Exception as e:
        logger.error(f"[ERRO FATAL] Erro fatal: {e}")
        print(f"\n[ERRO FATAL] ERRO FATAL: {e}")