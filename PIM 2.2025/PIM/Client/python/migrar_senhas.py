# -*- coding: utf-8 -*-
"""
Script para migrar senhas em texto plano para bcrypt
Executa tanto nos arquivos locais quanto no servidor
"""
import sys
import os
import json
import bcrypt

# Adiciona o caminho do projeto
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, project_root)

# Tenta usar o proxy, se falhar usa arquivos locais
try:
    import client_proxy_io as proxy
    USE_PROXY = True
    print("[INFO] Usando modo PROXY (servidor)")
except ImportError:
    USE_PROXY = False
    print("[INFO] Usando modo LOCAL")
    DATA_DIR = os.path.join(project_root, 'data')

def criptografar_senha(senha_texto):
    """Criptografa uma senha usando bcrypt"""
    return bcrypt.hashpw(senha_texto.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def carregar_arquivo(nome_arquivo):
    """Carrega arquivo JSON (proxy ou local)"""
    if USE_PROXY:
        return proxy.carregar_dados_do_servidor(nome_arquivo)
    else:
        caminho = os.path.join(DATA_DIR, nome_arquivo)
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

def salvar_arquivo(nome_arquivo, dados):
    """Salva arquivo JSON (proxy ou local)"""
    if USE_PROXY:
        return proxy.salvar_dados_no_servidor(nome_arquivo, dados)
    else:
        caminho = os.path.join(DATA_DIR, nome_arquivo)
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        return True

def migrar_senhas_arquivo(nome_arquivo, tipo_usuario):
    """Migra senhas de um arquivo específico"""
    print(f"\n{'='*60}")
    print(f"Migrando senhas: {nome_arquivo} ({tipo_usuario})")
    print('='*60)
    
    usuarios = carregar_arquivo(nome_arquivo)
    alteracoes = 0
    
    for usuario in usuarios:
        senha = usuario.get('senha', '')
        usuario_nome = usuario.get('usuario', 'N/A')
        
        # Verifica se a senha já está criptografada
        if senha and not senha.startswith('$2b$'):
            print(f"  • {usuario_nome}: Senha '{senha}' → criptografando...")
            usuario['senha'] = criptografar_senha(senha)
            alteracoes += 1
        else:
            print(f"  • {usuario_nome}: Senha já está criptografada ✓")
    
    if alteracoes > 0:
        print(f"\n  Total de senhas migradas: {alteracoes}")
        print(f"  Salvando alterações em {nome_arquivo}...")
        if salvar_arquivo(nome_arquivo, usuarios):
            print(f"  ✅ Arquivo {nome_arquivo} atualizado com sucesso!")
        else:
            print(f"  ❌ ERRO ao salvar {nome_arquivo}")
            return False
    else:
        print(f"  ℹ️  Nenhuma senha precisou ser migrada.")
    
    return True

def main():
    print("\n" + "="*60)
    print("  MIGRAÇÃO DE SENHAS PARA BCRYPT")
    print("="*60)
    print(f"Modo: {'PROXY (Servidor)' if USE_PROXY else 'LOCAL'}")
    print("="*60)
    
    # Confirma ção
    resposta = input("\nDeseja continuar com a migração? (s/n): ")
    if resposta.lower() != 's':
        print("Migração cancelada.")
        return
    
    # Migra cada arquivo
    arquivos = [
        ('alunos.json', 'Alunos'),
        ('professores.json', 'Professores'),
        ('admin.json', 'Administradores')
    ]
    
    sucesso_total = True
    for arquivo, tipo in arquivos:
        if not migrar_senhas_arquivo(arquivo, tipo):
            sucesso_total = False
    
    print("\n" + "="*60)
    if sucesso_total:
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    else:
        print("⚠️  MIGRAÇÃO CONCLUÍDA COM ERROS")
    print("="*60)
    
    if USE_PROXY:
        print("\n⚠️  IMPORTANTE: Execute este script também no servidor (maq1)")
        print("   para atualizar os arquivos na pasta DATA do servidor.")
    
    input("\nPressione Enter para sair...")

if __name__ == '__main__':
    main()
