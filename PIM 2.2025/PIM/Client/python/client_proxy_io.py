#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===============================================================
  MÓDULO DE I/O PROXY - CLIENTE
===============================================================
  Contém as funções que abstraem a comunicação HTTP
  com o Servidor Proxy, substituindo as funções de I/O local.
===============================================================
"""

import json
import os
import sys
import urllib.request
import urllib.error
from tkinter import messagebox

# ---------------------------------------------------------------
# CONFIGURAÇÃO DE CONEXÃO
# ---------------------------------------------------------------

# Aumenta o timeout para acomodar o tempo de espera na fila do servidor
REQUEST_TIMEOUT = 35 

# Desabilita proxy corporativo para redes locais (192.168.x.x)
# CRÍTICO: Em redes com Forefront TMG, o proxy bloqueia conexões internas
os.environ['NO_PROXY'] = '192.168.0.0/16,127.0.0.1,localhost'

# Lógica para carregar config_cliente.json (espera-se que esteja na mesma pasta)
try:
  # Acessa config_cliente.json que está na mesma pasta do client_proxy_io.py
  config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config_cliente.json')
  
  with open(config_path, 'r', encoding='utf-8') as f:
    CONFIG_CLIENT = json.load(f)
    
except FileNotFoundError:
  print("-> ERRO FATAL: Arquivo 'config_cliente.json' não encontrado.")
  print(f"Caminho procurado: {config_path}")
  sys.exit(1)
except json.JSONDecodeError:
  print("-> ERRO FATAL: Falha ao ler 'config_cliente.json'. Verifique a formatação JSON.")
  sys.exit(1)


SERVER_HOST = CONFIG_CLIENT.get('server_host', '127.0.0.1')
SERVER_PORT = CONFIG_CLIENT.get('server_port', 8080)
BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}/api"


# ---------------------------------------------------------------
# FUNÇÕES CORE DE COMUNICAÇÃO HTTP
# ---------------------------------------------------------------

def carregar_dados_do_servidor(filename):
  """Realiza um GET (Leitura) para o Servidor Proxy."""
  url = f"{BASE_URL}/read/{filename}"
  try:
    # SOLUÇÃO para Forefront TMG: Usa urllib sem ProxyHandler
    proxy_handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy_handler)
    
    req = urllib.request.Request(url)
    response = opener.open(req, timeout=REQUEST_TIMEOUT)
    
    response_data = response.read().decode('utf-8')
    data = json.loads(response_data)
    
    if data.get('success'):
      print(f"[PROXY] Leitura bem-sucedida: {filename}")
      return data.get('data', [])
    else:
      messagebox.showerror("Erro de Leitura", f"Erro ao ler {filename}: {data.get('error', 'Resposta inesperada do servidor')}")
      return []

  except urllib.error.URLError as e:
    if 'timed out' in str(e).lower():
      messagebox.showerror("Erro de Conexão", f"Tempo limite esgotado ({REQUEST_TIMEOUT}s). O servidor está lento ou a rede falhou.")
    else:
      messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao servidor em {SERVER_HOST}:{SERVER_PORT}.\nErro: {e}")
    return []
  except Exception as e:
    messagebox.showerror("Erro Inesperado", f"Erro desconhecido ao carregar {filename}: {e}")
    return []

def salvar_dados_no_servidor(filename, data):
  """Realiza um POST (Escrita) para o Servidor Proxy (usando a fila)."""
  url = f"{BASE_URL}/write/{filename}"
  payload = {'data': data}
  
  try:
    # SOLUÇÃO para Forefront TMG: Usa urllib sem ProxyHandler
    proxy_handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy_handler)
    
    # Codifica o payload como JSON
    json_data = json.dumps(payload).encode('utf-8')
    
    # Cria a requisição POST
    req = urllib.request.Request(url, data=json_data, headers={'Content-Type': 'application/json'})
    response = opener.open(req, timeout=REQUEST_TIMEOUT)
    
    response_data = response.read().decode('utf-8')
    result = json.loads(response_data)
    
    if result.get('success'):
      print(f"[PROXY] Escrita bem-sucedida: {filename}")
      return True
    else:
      error_msg = result.get('error', 'Falha desconhecida no servidor.')
      messagebox.showerror("Erro de Escrita", f"Falha ao salvar {filename}: {error_msg}")
      return False

  except urllib.error.URLError as e:
    if 'timed out' in str(e).lower():
      messagebox.showerror("Erro de Conexão", f"Tempo limite esgotado ({REQUEST_TIMEOUT}s) durante a escrita. O servidor está sobrecarregado.")
    else:
      messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao servidor em {SERVER_HOST}:{SERVER_PORT}.\nErro: {e}")
    return False
  except Exception as e:
    messagebox.showerror("Erro Inesperado", f"Erro desconhecido ao salvar {filename}: {e}")
    return False


# ---------------------------------------------------------------
# FUNÇÕES DE APLICAÇÃO (WRAPPER)
# ---------------------------------------------------------------
# Estas funções devem substituir TODAS as chamadas de I/O de arquivo
# em seu client.py ou app_gui.py

# --- Alunos ---
def carregar_alunos():
  return carregar_dados_do_servidor('alunos.json')

def salvar_alunos(dados):
  return salvar_dados_no_servidor('alunos.json', dados)

# --- Professores ---
def carregar_professores():
  return carregar_dados_do_servidor('professores.json')

def salvar_professores(dados):
  return salvar_dados_no_servidor('professores.json', dados)

# --- Admin ---
def carregar_admin():
  """Carrega 'admin.json', substituindo o antigo 'usuarios_admin.json'"""
  return carregar_dados_do_servidor('admin.json')

def salvar_admin(dados):
  """Salva 'admin.json', substituindo o antigo 'usuarios_admin.json'"""
  return salvar_dados_no_servidor('admin.json', dados)

# --- Turmas ---
def carregar_turmas():
  return carregar_dados_do_servidor('turmas.json')

def salvar_turmas(dados):
  return salvar_dados_no_servidor('turmas.json', dados)

# --- Matérias (antigo Disciplinas) ---
def carregar_materias():
  """Carrega 'materias.json', usado no app_gui.py"""
  return carregar_dados_do_servidor('materias.json')

def salvar_materias(dados):
  """Salva 'materias.json', usado no app_gui.py"""
  return salvar_dados_no_servidor('materias.json', dados)

# --- Pedidos ---
def carregar_pedidos():
  return carregar_dados_do_servidor('pedidos.json')

def salvar_pedidos(dados):
  return salvar_dados_no_servidor('pedidos.json', dados)

# --- Notas ---
def carregar_notas():
  return carregar_dados_do_servidor('notas.json')

def salvar_notas(dados):
  return salvar_dados_no_servidor('notas.json', dados)

# --- Registros de Aula ---
def carregar_registros_aula():
  return carregar_dados_do_servidor('registros_aula.json')

def salvar_registros_aula(dados):
  return salvar_dados_no_servidor('registros_aula.json', dados)

# --- Respostas de Alunos ---
def carregar_respostas_alunos():
  """Carrega 'respostas_alunos.json'"""
  return carregar_dados_do_servidor('respostas_alunos.json')

def salvar_respostas_alunos(dados):
  """Salva 'respostas_alunos.json'"""
  return salvar_dados_no_servidor('respostas_alunos.json', dados)


# ---------------------------------------------------------------
# FUNÇÕES DE LÓGICA DE USUÁRIO (ABSTRAÍDAS)
# ---------------------------------------------------------------
# Funções que replicam a lógica do app_gui.py para gerenciamento
# de usuários, agora usando o proxy.

def carregar_todos_usuarios():
  """Combina dados de diferentes arquivos para login/gestão de usuários."""
  alunos = carregar_alunos()
  professores = carregar_professores()
  admins = carregar_admin() # ATUALIZADO
  
  for user in alunos: user['tipo'] = 'aluno'
  for user in professores: user['tipo'] = 'professor'
  for user in admins: user['tipo'] = 'admin'
  
  return alunos + professores + admins

def salvar_usuario_por_tipo(usuario):
  """Função adaptada para salvar o usuário no arquivo correto via proxy."""
  tipo = usuario.get('tipo')
  
  # 1. Carrega todos os usuários do tipo em questão
  if tipo == 'aluno':
    todos = carregar_alunos()
  elif tipo == 'professor':
    todos = carregar_professores()
  elif tipo == 'admin':
    todos = carregar_admin() # ATUALIZADO
  else:
    messagebox.showerror("Erro de Salvar", "Tipo de usuário não reconhecido.")
    return False
    
  # 2. Atualiza/Substitui o usuário na lista
  # Lógica de app_gui.py: alunos são únicos por 'ra' ou 'usuario', outros por 'usuario'
  if tipo == 'aluno':
    # Remove o antigo (se existir) baseado no 'usuario' OU 'ra'
    todos = [u for u in todos if (u.get('usuario') != usuario.get('usuario') and 
                   u.get('ra') != usuario.get('ra'))]
  else:
    todos = [u for u in todos if u.get('usuario') != usuario.get('usuario')] # Remove o antigo
  
  todos.append(usuario) # Adiciona o novo
  
  # 3. Salva a lista completa de volta ao servidor
  if tipo == 'aluno':
    return salvar_alunos(todos)
  elif tipo == 'professor':
    return salvar_professores(todos)
  elif tipo == 'admin':
    return salvar_admin(todos) # ATUALIZADO
  
  return False

def remover_usuario_por_tipo(usuario_login, tipo, ra_aluno=None):
  """Função adaptada para remover o usuário do arquivo correto via proxy."""
  # 1. Carrega todos os usuários do tipo em questão
  if tipo == 'aluno':
    todos = carregar_alunos()
  elif tipo == 'professor':
    todos = carregar_professores()
  elif tipo == 'admin':
    todos = carregar_admin() # ATUALIZADO
  else:
    messagebox.showerror("Erro ao Remover", "Tipo de usuário não reconhecido.")
    return False
    
  # 2. Remove o usuário da lista (lógica do app_gui.py)
  if tipo == 'aluno' and ra_aluno:
    todos_filtrados = [u for u in todos if u.get('ra') != ra_aluno]
  else:
    todos_filtrados = [u for u in todos if u.get('usuario') != usuario_login]
  
  # 3. Salva a lista filtrada de volta ao servidor
  if tipo == 'aluno':
    return salvar_alunos(todos_filtrados)
  elif tipo == 'professor':
    return salvar_professores(todos_filtrados)
  elif tipo == 'admin':
    return salvar_admin(todos_filtrados) # ATUALIZADO
  
  return False

def checar_primeiro_admin():
  """Verifica se há algum administrador cadastrado."""
  try:
    admins = carregar_admin() # ATUALIZADO
    return len(admins) == 0
  except:
    # Em caso de falha de conexão, pode retornar True para forçar o setup
    # mas a função carregar_admin já trata o erro com messagebox.
    return True

def gerar_mapa_professores():
  """Gera o mapa de login → nome do professor (usado pelo app_gui)"""
  professores = carregar_professores()
  return {p['usuario']: p.get('nome', p['usuario']) for p in professores}

def verificar_atividade_ja_respondida(atividade_id, ra_aluno):
  """Verifica se um aluno específico já respondeu uma atividade específica."""
  respostas = carregar_respostas_alunos() # Usa a nova função
  
  for resposta in respostas:
    if (str(resposta.get('ra_aluno')) == str(ra_aluno) and 
      str(resposta.get('atividade_id')) == str(atividade_id)):
      return True, resposta.get('data_resposta', 'Data não disponível')
  
  return False, None