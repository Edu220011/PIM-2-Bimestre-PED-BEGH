# Verificação e importação de dependências
try:
    import customtkinter
except ImportError:
    print("Erro: customtkinter não está instalado.")
    print("Para instalar, execute: pip install customtkinter")
    input("Pressione Enter para sair...")
    exit(1)

try:
    import bcrypt
except ImportError:
    print("Erro: bcrypt não está instalado.")
    print("Para instalar, execute: pip install bcrypt")
    input("Pressione Enter para sair...")
    exit(1)

from tkinter import ttk, messagebox, simpledialog
import tkinter as tk
import json
import os
import re
import time
import unicodedata
from datetime import datetime
import datetime as dt
import sys

# Importa o módulo de proxy para comunicação com o servidor
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, os.path.join(project_root, 'conexao', 'maq2'))

try:
    import client_proxy_io as proxy
    USE_PROXY = True
    print("[MODO REDE] Conectando ao servidor proxy...")
except ImportError:
    USE_PROXY = False
    print("[MODO LOCAL] Proxy não encontrado, usando arquivos locais...")

DATA_DIR = os.path.join(project_root, 'data')
os.makedirs(DATA_DIR, exist_ok=True)


def carregar_json(file_path):
    """Carrega dados do arquivo JSON - usa proxy se disponível, senão usa arquivo local"""
    if USE_PROXY:
        # Extrai apenas o nome do arquivo (ex: alunos.json)
        filename = os.path.basename(file_path)
        return proxy.carregar_dados_do_servidor(filename)
    else:
        # Modo local (fallback)
        if not os.path.exists(file_path):
            return []
        try:
            if os.path.getsize(file_path) == 0:
                return []
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return []

def salvar_json(file_path, data):
    """Salva dados no arquivo JSON - usa proxy se disponível, senão usa arquivo local"""
    if USE_PROXY:
        # Extrai apenas o nome do arquivo (ex: alunos.json)
        filename = os.path.basename(file_path)
        return proxy.salvar_dados_no_servidor(filename, data)
    else:
        # Modo local (fallback)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


ALUNOS_FILE = os.path.join(DATA_DIR, 'alunos.json')
PROFESSORES_FILE = os.path.join(DATA_DIR, 'professores.json')
ADMIN_FILE = os.path.join(DATA_DIR, 'admin.json')


QUESTOES_FILE = os.path.join(DATA_DIR, 'questoes.json')
TURMAS_FILE = os.path.join(DATA_DIR, 'turmas.json')
MATERIAS_FILE = os.path.join(DATA_DIR, 'materias.json')
RESPOSTAS_FILE = os.path.join(DATA_DIR, 'respostas_alunos.json')
REGISTROS_AULA_FILE = os.path.join(DATA_DIR, 'registros_aula.json')
NOTAS_FILE = os.path.join(DATA_DIR, 'notas.json')

PEDIDOS_FILE = os.path.join(DATA_DIR, 'pedidos.json')

def carregar_todos_usuarios():
    """Carrega todos os usuários de todos os arquivos e retorna uma lista unificada"""
    todos_usuarios = []
    
    # Mapeamento dos tipos de usuário
    tipos_arquivo = [
        (ALUNOS_FILE, 'aluno'),
        (PROFESSORES_FILE, 'professor'), 
        (ADMIN_FILE, 'admin')
    ]
    
    for arquivo, tipo in tipos_arquivo:
        usuarios = carregar_json(arquivo)
        for usuario in usuarios:
            if 'tipo' not in usuario:
                usuario['tipo'] = tipo
            todos_usuarios.append(usuario)
    
    return todos_usuarios

def salvar_usuario_por_tipo(usuario_data):
    """Salva um usuário no arquivo correspondente ao seu tipo"""
    tipo = usuario_data.get('tipo')
    
    # Mapeamento de tipo para arquivo
    arquivos_tipo = {
        'aluno': ALUNOS_FILE,
        'professor': PROFESSORES_FILE,
        'admin': ADMIN_FILE
    }
    
    arquivo = arquivos_tipo.get(tipo)
    if not arquivo:
        return
    
    usuarios = carregar_json(arquivo)
    
    # Lógica unificada para encontrar e atualizar/adicionar usuário
    for i, usuario in enumerate(usuarios):
        # Para alunos, verificar tanto usuário quanto RA
        if (tipo == 'aluno' and 
            (usuario.get('usuario') == usuario_data.get('usuario') or 
             usuario.get('ra') == usuario_data.get('ra'))):
            usuarios[i] = usuario_data
            break
        # Para outros tipos, verificar apenas por usuário
        elif tipo in ['professor', 'admin'] and usuario.get('usuario') == usuario_data.get('usuario'):
            usuarios[i] = usuario_data
            break
    else:
        # Se não encontrou, adicionar novo usuário
        usuarios.append(usuario_data)
    
    salvar_json(arquivo, usuarios)

def remover_usuario_por_tipo(usuario_login, tipo_usuario, ra_aluno=None):
    """Remove um usuário do arquivo correspondente ao seu tipo"""
    arquivos_tipo = {
        'aluno': ALUNOS_FILE,
        'professor': PROFESSORES_FILE,
        'admin': ADMIN_FILE
    }
    
    arquivo = arquivos_tipo.get(tipo_usuario)
    if not arquivo:
        return
    
    usuarios = carregar_json(arquivo)
    
    if tipo_usuario == 'aluno' and ra_aluno:
        usuarios = [u for u in usuarios if u.get('ra') != ra_aluno]
    else:
        usuarios = [u for u in usuarios if u.get('usuario') != usuario_login]
    
    salvar_json(arquivo, usuarios)


def gerar_mapa_professores():
    """Gera o mapa de login → nome do professor"""
    professores = carregar_json(PROFESSORES_FILE)
    return {p['usuario']: p.get('nome', p['usuario']) for p in professores}

# Funções centralizadas de validação
def validar_data(data_str, formato='%d/%m/%Y'):
    """Valida formato de data"""
    try:
        datetime.strptime(data_str, formato)
        return True, ""
    except ValueError:
        return False, f"Data deve estar no formato {formato.replace('%d', 'DD').replace('%m', 'MM').replace('%Y', 'AAAA')} e conter apenas números válidos"

def validar_data_entrega_atividade(data_str):
    """Valida data de entrega de atividade (não pode ser passada)"""
    try:
        data_obj = datetime.strptime(data_str, '%d/%m/%Y')
        data_atual = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if data_obj < data_atual:
            return False, "A data de entrega não pode ser anterior à data atual"
        
        return True, ""
    except ValueError:
        return False, "Data deve estar no formato DD/MM/AAAA e conter apenas números válidos"

def validar_idade_minima(data_nascimento_str, idade_minima=18):
    """Valida se a pessoa tem idade mínima"""
    try:
        data_nascimento_obj = datetime.strptime(data_nascimento_str, '%d/%m/%Y')
        hoje = datetime.now()
        idade = hoje.year - data_nascimento_obj.year - ((hoje.month, hoje.day) < (data_nascimento_obj.month, data_nascimento_obj.day))
        
        if idade < idade_minima:
            return False, f"A idade deve ser pelo menos {idade_minima} anos. Idade atual: {idade} anos"
        
        return True, ""
    except ValueError:
        return False, "Data de nascimento deve estar no formato DD/MM/AAAA"

def validar_nome(nome):
    """Valida nome completo"""
    if not nome or len(nome.strip()) < 2:
        return False, "Nome deve ter pelo menos 2 caracteres"
    if not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', nome):
        return False, "Nome deve conter apenas letras e espaços"
    return True, ""

def validar_usuario(usuario, usuarios_existentes, usuario_atual=None):
    """Valida nome de usuário"""
    if not usuario or len(usuario) < 3:
        return False, "Usuário deve ter pelo menos 3 caracteres"
    if not re.match(r'^[a-zA-Z0-9._]+$', usuario):
        return False, "Usuário deve conter apenas letras, números, pontos e underscores"
    if usuario != usuario_atual and any(u.get('usuario') == usuario for u in usuarios_existentes):
        return False, f'O usuário "{usuario}" já existe'
    return True, ""

def normalizar_texto(texto):
    """Remove acentos e normaliza texto para nomes de usuário"""
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9.]', '', texto.lower())

def verificar_prazo_atividade(data_entrega_str):
    """Verifica se a atividade ainda está dentro do prazo"""
    try:
        data_entrega = datetime.strptime(data_entrega_str, '%d/%m/%Y')
        data_atual = datetime.now()
        # Considera que a atividade expira no fim do dia da data de entrega
        data_limite = data_entrega.replace(hour=23, minute=59, second=59)
        return data_atual <= data_limite
    except:
        return False

def verificar_atividade_ja_respondida(atividade_id, ra_aluno):
    """Verifica se um aluno específico já respondeu uma atividade específica"""
    RESPOSTAS_FILE = os.path.join(DATA_DIR, 'respostas_alunos.json')
    respostas = carregar_json(RESPOSTAS_FILE)
    
    for resposta in respostas:
        if (str(resposta.get('ra_aluno')) == str(ra_aluno) and 
            str(resposta.get('atividade_id')) == str(atividade_id)):
            return True, resposta.get('data_resposta', 'Data não disponível')
    
    return False, None

def obter_status_atividade_aluno(atividade, ra_aluno):
    """Obtém o status da atividade para o aluno específico"""
    if atividade.get('status') != 'Liberada':
        return 'Não Liberada'
    
    if not verificar_prazo_atividade(atividade.get('data_entrega', '')):
        return 'Expirada'
    
    # Verificar se já foi respondida
    ja_respondida, _ = verificar_atividade_ja_respondida(atividade.get('id'), ra_aluno)
    if ja_respondida:
        return 'Respondida'
    
    return 'Disponível'


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title('Sistema Acadêmico')
        self.resizable(True, True)
        self.usuario_logado = None
        self.mapa_professores = {}
        self.series_disponiveis = [f"{i}ª Série" for i in range(1, 10)]
        self.turmas_disponiveis = ['A', 'B', 'C', 'D', 'E']
        
        # Cache simples para dados frequentemente acessados
        self._cache_usuarios = None
        self._cache_timestamp = 0

        customtkinter.set_appearance_mode("System")
        customtkinter.set_default_color_theme("blue")

        # Style for ttk.Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background="#2a2d2e",
                        foreground="white",
                        rowheight=25,
                        fieldbackground="#2a2d2e",
                        bordercolor="#343638",
                        borderwidth=0)
        style.map('Treeview', background=[('selected', '#22559b')])
        style.configure("Treeview.Heading",
                        background="#565b5e",
                        foreground="white",
                        relief="flat")
        style.map("Treeview.Heading",
                  background=[('active', '#3484F0')])

        # Define tamanho mínimo e padrão da janela
        self.geometry("1024x768")
        self.minsize(800, 600)
        
        # Tenta maximizar após um delay para garantir que a janela foi criada
        self.after(100, lambda: self.state('zoomed'))

        self._build_login()

    def _validar_senha(self, senha):
        """Valida a complexidade da senha."""
        if len(senha) < 6:
            return False, "A senha deve ter no mínimo 6 caracteres."
        if not re.search(r"[a-zA-Z]", senha):
            return False, "A senha deve conter pelo menos uma letra."
        if not re.search(r"[0-9]", senha):
            return False, "A senha deve conter pelo menos um número."
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha):
            return False, "A senha deve conter pelo menos um caractere especial (ex: !@#$%)."
        return True, ""

    # ================= LOGIN =================
    def _build_login(self):
        self.login_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.login_frame.pack(expand=True, fill='both')

        # Container centralizado para login
        login_container = customtkinter.CTkFrame(self.login_frame)
        login_container.pack(expand=True, fill='both', padx=20, pady=20)

        # Frame interno para centralizar o login
        inner_frame = customtkinter.CTkFrame(login_container, width=350, height=400)
        inner_frame.place(relx=0.5, rely=0.5, anchor='center')

        # Título do sistema
        customtkinter.CTkLabel(inner_frame, text='Sistema Acadêmico', 
                              font=customtkinter.CTkFont(size=24, weight="bold")).pack(pady=(30, 10))
        
        customtkinter.CTkLabel(inner_frame, text='Faça login para acessar o sistema', 
                              font=customtkinter.CTkFont(size=12), 
                              text_color=("gray50", "gray50")).pack(pady=(0, 20))

        # Campos de login
        customtkinter.CTkLabel(inner_frame, text='Usuário ou RA', anchor='w').pack(fill='x', padx=30, pady=(10, 5))
        self.entry_user = customtkinter.CTkEntry(inner_frame, placeholder_text="Digite seu usuário ou RA", height=40)
        self.entry_user.pack(fill='x', padx=30, pady=(0, 15))

        customtkinter.CTkLabel(inner_frame, text='Senha', anchor='w').pack(fill='x', padx=30, pady=(0, 5))

        # Frame da senha com botão de visibilidade
        pass_frame = customtkinter.CTkFrame(inner_frame, fg_color="transparent")
        pass_frame.pack(fill='x', padx=30, pady=(0, 20))
        
        self.entry_pass = customtkinter.CTkEntry(pass_frame, show='*', placeholder_text="Digite sua senha", height=40)
        self.entry_pass.pack(side='left', fill='x', expand=True)
        
        show_pass_btn = customtkinter.CTkButton(pass_frame, text="👁", width=40, height=40)
        show_pass_btn.pack(side='left', padx=(5,0))

        def toggle_login_pass():
            if self.entry_pass.cget('show') == '*':
                self.entry_pass.configure(show='')
                show_pass_btn.configure(text="🙈")
            else:
                self.entry_pass.configure(show='*')
                show_pass_btn.configure(text="👁")
        show_pass_btn.configure(command=toggle_login_pass)

        # Botões
        customtkinter.CTkButton(inner_frame, text='Entrar', command=self.autenticar, 
                               height=45, font=customtkinter.CTkFont(size=14, weight="bold")).pack(fill='x', padx=30, pady=(0, 15))
        
        # Botão para solicitar matrícula
        customtkinter.CTkButton(inner_frame, text='Solicitar Matrícula', 
                               fg_color="#28a745", hover_color="#218838",
                               height=40, command=self._abrir_form_matricula).pack(fill='x', padx=30, pady=(0, 15))
        
        customtkinter.CTkButton(inner_frame, text='Sair do Sistema', 
                               fg_color="transparent", border_width=2, 
                               text_color=("gray10", "#DCE4EE"), 
                               command=self.sair_app, height=40).pack(fill='x', padx=30)

        # Bind Enter key
        self.bind('<Return>', lambda e: self.autenticar())

    def _abrir_form_matricula(self):
        """Abre o formulário para solicitar matrícula"""
        top = customtkinter.CTkToplevel(self)
        top.title('Solicitar Matrícula')
        top.geometry('500x400')  # Tamanho reduzido para formulário simplificado
        top.resizable(False, False)
        top.grab_set()  # Torna a janela modal
        
        customtkinter.CTkLabel(top, text="Formulário de Solicitação de Matrícula", 
                              font=customtkinter.CTkFont(size=18, weight="bold")).pack(pady=(20, 10), padx=20)
        
        # Frame principal para os campos do formulário
        main_frame = customtkinter.CTkFrame(top)
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # === DADOS DO ALUNO (SIMPLIFICADO) ===
        customtkinter.CTkLabel(main_frame, text="📚 DADOS DO ALUNO", 
                              font=customtkinter.CTkFont(size=14, weight="bold"),
                              text_color=("#1f538d", "#3b8ed0")).pack(anchor='w', padx=20, pady=(15, 10))
        
        # Nome Completo do Aluno
        customtkinter.CTkLabel(main_frame, text="Nome Completo do Aluno:*", 
                              font=customtkinter.CTkFont(weight="bold")).pack(anchor='w', padx=20, pady=(10, 0))
        e_nome = customtkinter.CTkEntry(main_frame, placeholder_text="Digite o nome completo do aluno", height=35)
        e_nome.pack(fill='x', padx=20, pady=(0, 10))
        
        # Data de Nascimento do Aluno
        customtkinter.CTkLabel(main_frame, text="Data de Nascimento do Aluno (DD/MM/AAAA):*",
                              font=customtkinter.CTkFont(weight="bold")).pack(anchor='w', padx=20, pady=(10, 0))
        e_nascimento = customtkinter.CTkEntry(main_frame, placeholder_text="Ex.: 01/01/2010", height=35)
        e_nascimento.pack(fill='x', padx=20, pady=(0, 20))
        
        def enviar_solicitacao():
            # Validar campos simplificados
            nome = e_nome.get().strip()
            nascimento = e_nascimento.get().strip()
            
            # Validar campos obrigatórios
            if not nome or not nascimento:
                messagebox.showerror("Erro", "Todos os campos marcados com * são obrigatórios!", parent=top)
                return
            
            # Validar formato da data
            try:
                dt.datetime.strptime(nascimento, '%d/%m/%Y')
            except ValueError:
                messagebox.showerror('Erro', 'Data de nascimento deve estar no formato DD/MM/AAAA', parent=top)
                return
            
            # Criar descrição simplificada para o pedido
            descricao = f"""=== SOLICITAÇÃO DE MATRÍCULA ===

Nome do Aluno: {nome}
Data de Nascimento: {nascimento}"""
            
            # Salvar pedido
            pedidos = carregar_json(PEDIDOS_FILE)
            
            # Gerar novo ID
            novo_id = max([p.get('id', 0) for p in pedidos], default=0) + 1
            
            # Data atual formatada
            data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
            
            # Criar novo pedido com dados simplificados
            novo_pedido = {
                "id": novo_id,
                "data": data_atual,
                "tipo": "Matrícula",
                "status": "Pendente",
                "descricao": descricao,
                "aluno_ra": None,  # Não tem RA pois ainda não é aluno
                "solicitante_nome": nome,
                # Dados simplificados
                "Nome": nome,
                "Data de Nascimento": nascimento
            }
            
            # Adicionar à lista e salvar
            pedidos.append(novo_pedido)
            salvar_json(PEDIDOS_FILE, pedidos)
            
            messagebox.showinfo("Sucesso", f"Solicitação de matrícula enviada com sucesso!\n\nAluno: {nome}\nProtocolo: {novo_id:06d}\n\nEntraremos em contato em breve.", parent=top)
            top.destroy()
        
        # Botões de ação
        botoes_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        botoes_frame.pack(fill='x', padx=20, pady=20)
        
        customtkinter.CTkButton(botoes_frame, text="❌ Cancelar", 
                              fg_color="#dc3545", hover_color="#c82333",
                              height=40,
                              font=customtkinter.CTkFont(size=13, weight="bold"),
                              command=top.destroy).pack(side='left', padx=(0, 10), expand=True, fill='x')
        
        customtkinter.CTkButton(botoes_frame, text="📩 Enviar Solicitação", 
                              fg_color="#28a745", hover_color="#218838",
                              height=40,
                              font=customtkinter.CTkFont(size=13, weight="bold"),
                              command=enviar_solicitacao).pack(side='right', padx=(10, 0), expand=True, fill='x')

    def autenticar(self):
        user_input = self.entry_user.get().strip()
        pwd_input = self.entry_pass.get().strip()
        
        usuarios = carregar_todos_usuarios()
        # Permite login com 'usuario' ou 'ra'
        u = next((x for x in usuarios if x['usuario'] == user_input or x.get('ra') == user_input), None)
        
        if not u:
            messagebox.showerror('Erro', 'Credenciais inválidas.')
            return

        senha_armazenada = u['senha']
        autenticado = False

        # Verifica se a senha armazenada já está criptografada
        if senha_armazenada.startswith('$2b$'):
            if bcrypt.checkpw(pwd_input.encode('utf-8'), senha_armazenada.encode('utf-8')):
                autenticado = True
        else:
            # Se não estiver, compara como texto plano (para migração)
            if senha_armazenada == pwd_input:
                autenticado = True
                # Criptografa a senha e atualiza o arquivo
                valida, msg = self._validar_senha(pwd_input)
                if valida:
                    hashed_pw = bcrypt.hashpw(pwd_input.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    u['senha'] = hashed_pw
                    salvar_usuario_por_tipo(u)
                else:
                    messagebox.showwarning("Senha Fraca", f"Sua senha é fraca e precisa ser atualizada. Por favor, contate um administrador.\nMotivo: {msg}")

        if not autenticado:
            messagebox.showerror('Erro', 'Credenciais inválidas.')
            return

        self.usuario_logado = u
        # atualizar mapa de professores sempre que houver login (útil após CRUD de usuários)
        self.mapa_professores = gerar_mapa_professores()
        self.login_frame.destroy()
        self._build_dashboard()

    # ================= DASHBOARD =================
    def _build_dashboard(self):
        tipo = self.usuario_logado['tipo']
        frame = customtkinter.CTkFrame(self)
        # manter referência para permitir logout sem fechar o app
        self.dashboard_frame = frame
        frame.pack(expand=True, fill='both')

        customtkinter.CTkLabel(frame, text=f"Bem-vindo, {self.usuario_logado.get('nome', '')} ({tipo})", font=customtkinter.CTkFont(size=16, weight="bold")).pack(pady=(5, 10), padx=10, anchor='w')
        tabs = customtkinter.CTkTabview(frame)
        tabs.pack(expand=True, fill='both', padx=5, pady=5)

        if tipo == 'admin':
            tab_admin = tabs.add('Admin')
            self._tab_admin(tab_admin)
        elif tipo == 'professor':
            self.mapa_professores = gerar_mapa_professores()
            tab_prof = tabs.add('Professor')
            self._tab_prof(tab_prof)
        elif tipo == 'aluno':
            tab_aluno = tabs.add('Aluno')
            self._tab_aluno(tab_aluno)
        else:
            messagebox.showwarning("Aviso", f"Tipo de usuário não reconhecido: '{tipo}'. Contacte o administrador.")

    def sair_da_conta(self):
        """Faz logout: destrói o dashboard e volta para a tela de login sem fechar o app."""
        # limpar usuário logado
        self.usuario_logado = None
        # destruir frame do dashboard se existir
        try:
            if hasattr(self, 'dashboard_frame') and self.dashboard_frame:
                self.dashboard_frame.destroy()
        except Exception:
            pass
        # reconstruir login
        self._build_login()

    def sair_app(self):
        """Fecha o aplicativo com confirmação a partir da tela de login."""
        if messagebox.askyesno('Sair', 'Deseja sair do aplicativo?'):
            self.destroy()

    # ================= ALUNO =================
    def _tab_aluno(self, parent_tab):
        """Cria a aba específica para alunos"""
        customtkinter.CTkLabel(parent_tab, text="Painel do Aluno", font=customtkinter.CTkFont(size=18, weight="bold")).pack(pady=(10, 5), padx=10, anchor='w')

        tabs_inner = customtkinter.CTkTabview(parent_tab)
        tabs_inner.pack(expand=True, fill='both')

        # Aba de Notas e Frequência
        self._aluno_notas_tab(tabs_inner.add('Minhas Notas'))
        
        # Aba de Boletim Bimestral
        self._aluno_boletim_bimestral_tab(tabs_inner.add('📊 Boletim Bimestral'))
        
        # Aba de Atividades
        self._aluno_atividades_tab(tabs_inner.add('Minhas Atividades'))
        
        # Aba de Segurança
        tab_seguranca = tabs_inner.add("Segurança")
        self._criar_aba_seguranca(tab_seguranca)
        
        self._criar_controles_inferiores(parent_tab)

    def _aluno_notas_tab(self, parent_tab):
        """Aba para visualização de notas do aluno"""
        ra_aluno = self.usuario_logado.get('ra')
        
        if not ra_aluno:
            customtkinter.CTkLabel(parent_tab, text="Erro: RA do aluno não encontrado.", 
                                 font=customtkinter.CTkFont(size=16)).pack(pady=50)
            return

        # Encontrar a turma do aluno
        turmas = carregar_json(TURMAS_FILE)
        turma_aluno = None
        for t in turmas:
            if ra_aluno in t.get('alunos', []):
                turma_aluno = t
                break
        
        if not turma_aluno:
            customtkinter.CTkLabel(parent_tab, text="Você ainda não foi matriculado em nenhuma turma.", 
                                 font=customtkinter.CTkFont(size=16)).pack(pady=50)
            return

        # Tabela de notas por matéria
        tree_notas = ttk.Treeview(parent_tab, columns=('materia', 'b1_np1', 'b1_np2', 'b1_media', 'b2_np1', 'b2_np2', 'b2_media', 'b3_np1', 'b3_np2', 'b3_media', 'b4_np1', 'b4_np2', 'b4_media', 'media_final'), show='headings')
        
        # Configurar cabeçalhos
        tree_notas.heading('materia', text='Matéria')
        tree_notas.column('materia', width=150)
        
        for bim in range(1, 5):
            tree_notas.heading(f'b{bim}_np1', text=f'{bim}ºB NP1')
            tree_notas.column(f'b{bim}_np1', width=70, anchor='center')
            tree_notas.heading(f'b{bim}_np2', text=f'{bim}ºB NP2')
            tree_notas.column(f'b{bim}_np2', width=70, anchor='center')
            tree_notas.heading(f'b{bim}_media', text=f'{bim}ºB Média')
            tree_notas.column(f'b{bim}_media', width=80, anchor='center')
        
        tree_notas.heading('media_final', text='Média Final')
        tree_notas.column('media_final', width=100, anchor='center')
        
        tree_notas.pack(fill='both', expand=True, padx=10, pady=10)

        # Carregar notas
        materias = carregar_json(MATERIAS_FILE)
        notas = carregar_json(NOTAS_FILE)
        
        # Filtrar matérias da turma do aluno pelo ID da turma
        turma_id = turma_aluno.get('id')
        materias_aluno = [m for m in materias if m.get('turma_id') == turma_id]
        
        for materia in materias_aluno:
            materia_id = materia['id']
            nome_materia = materia['nome']
            
            # Inicializar valores
            valores = [nome_materia]
            medias_bimestrais = []
            
            for bim in range(1, 5):
                bim_prefix = f"B{bim}"
                
                # Buscar notas NP1 e NP2
                nota_np1 = next((n for n in notas if n.get('aluno_ra') == ra_aluno and n.get('materia_id') == materia_id and n.get('tipo_nota') == f"{bim_prefix}_NP1"), None)
                nota_np2 = next((n for n in notas if n.get('aluno_ra') == ra_aluno and n.get('materia_id') == materia_id and n.get('tipo_nota') == f"{bim_prefix}_NP2"), None)
                
                val_np1 = nota_np1.get('valor') if nota_np1 else "N/L"
                val_np2 = nota_np2.get('valor') if nota_np2 else "N/L"
                
                # Calcular média bimestral
                if isinstance(val_np1, (int, float)) and isinstance(val_np2, (int, float)):
                    media_bim = (val_np1 + val_np2) / 2
                    media_bim_str = f"{media_bim:.2f}"
                    medias_bimestrais.append(media_bim)
                else:
                    media_bim_str = "N/L"
                
                valores.extend([val_np1, val_np2, media_bim_str])
            
            # Calcular média final
            if medias_bimestrais:
                media_final = sum(medias_bimestrais) / len(medias_bimestrais)
                media_final_str = f"{media_final:.2f}"
            else:
                media_final_str = "N/A"
            
            valores.append(media_final_str)
            tree_notas.insert('', 'end', values=valores)

    def _aluno_boletim_bimestral_tab(self, parent_tab):
        """Aba para visualização do boletim bimestral completo do aluno"""
        ra_aluno = self.usuario_logado.get('ra')
        
        if not ra_aluno:
            customtkinter.CTkLabel(parent_tab, text="Erro: RA do aluno não encontrado.", 
                                 font=customtkinter.CTkFont(size=16)).pack(pady=50)
            return

        # Encontrar a turma do aluno
        turmas = carregar_json(TURMAS_FILE)
        turma_aluno = None
        for t in turmas:
            if ra_aluno in t.get('alunos', []):
                turma_aluno = t
                break
        
        if not turma_aluno:
            customtkinter.CTkLabel(parent_tab, text="Você ainda não foi matriculado em nenhuma turma.", 
                                 font=customtkinter.CTkFont(size=16)).pack(pady=50)
            return

        # Frame principal com scroll
        main_frame = customtkinter.CTkScrollableFrame(parent_tab)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Cabeçalho do boletim
        header_frame = customtkinter.CTkFrame(main_frame)
        header_frame.pack(fill='x', pady=(0, 20))
        
        customtkinter.CTkLabel(header_frame, 
                              text="📊 BOLETIM ESCOLAR BIMESTRAL", 
                              font=customtkinter.CTkFont(size=20, weight="bold")).pack(pady=15)
        
        info_text = f"Aluno: {self.usuario_logado.get('nome', '')} | RA: {ra_aluno} | Turma: {turma_aluno.get('serie', '')} - {turma_aluno.get('turma', '')}"
        customtkinter.CTkLabel(header_frame, text=info_text, 
                              font=customtkinter.CTkFont(size=12)).pack(pady=(0, 15))

        # Carregar dados
        materias = carregar_json(MATERIAS_FILE)
        notas = carregar_json(NOTAS_FILE)
        
        # Filtrar matérias da turma do aluno pelo ID da turma
        turma_id = turma_aluno.get('id')
        materias_aluno = [m for m in materias if m.get('turma_id') == turma_id]
        
        if not materias_aluno:
            customtkinter.CTkLabel(main_frame, text="Nenhuma matéria encontrada para sua turma.", 
                                 font=customtkinter.CTkFont(size=16)).pack(pady=50)
            return

        # Criar boletim por bimestre
        medias_finais_por_materia = {}
        
        for bimestre in range(1, 5):
            bim_frame = customtkinter.CTkFrame(main_frame)
            bim_frame.pack(fill='x', pady=(0, 15))
            
            # Título do bimestre
            customtkinter.CTkLabel(bim_frame, 
                                  text=f"📚 {bimestre}º BIMESTRE", 
                                  font=customtkinter.CTkFont(size=16, weight="bold"),
                                  text_color=("#1f538d", "#3b8ed0")).pack(pady=15)
            
            # Tabela de notas do bimestre
            tree_bimestre = ttk.Treeview(bim_frame, 
                                       columns=('materia', 'np1', 'np2', 'media', 'situacao'), 
                                       show='headings', height=6)
            
            tree_bimestre.heading('materia', text='Matéria')
            tree_bimestre.column('materia', width=200)
            tree_bimestre.heading('np1', text='NP1')
            tree_bimestre.column('np1', width=80, anchor='center')
            tree_bimestre.heading('np2', text='NP2')
            tree_bimestre.column('np2', width=80, anchor='center')
            tree_bimestre.heading('media', text='Média')
            tree_bimestre.column('media', width=80, anchor='center')
            tree_bimestre.heading('situacao', text='Situação')
            tree_bimestre.column('situacao', width=100, anchor='center')
            
            tree_bimestre.pack(fill='x', padx=15, pady=(0, 10))
            
            # Carregar notas do bimestre
            medias_bimestre = []
            bim_prefix = f"B{bimestre}"
            
            for materia in materias_aluno:
                materia_id = materia['id']
                nome_materia = materia['nome']
                
                # Buscar notas NP1 e NP2 do bimestre
                nota_np1 = next((n for n in notas if 
                               n.get('aluno_ra') == ra_aluno and 
                               n.get('materia_id') == materia_id and 
                               n.get('tipo_nota') == f"{bim_prefix}_NP1"), None)
                
                nota_np2 = next((n for n in notas if 
                               n.get('aluno_ra') == ra_aluno and 
                               n.get('materia_id') == materia_id and 
                               n.get('tipo_nota') == f"{bim_prefix}_NP2"), None)
                
                val_np1 = nota_np1.get('valor') if nota_np1 else "N/L"
                val_np2 = nota_np2.get('valor') if nota_np2 else "N/L"
                
                # Calcular média do bimestre
                if isinstance(val_np1, (int, float)) and isinstance(val_np2, (int, float)):
                    media_bim = (val_np1 + val_np2) / 2
                    media_str = f"{media_bim:.2f}"
                    
                    # Armazenar para cálculo da média final
                    if nome_materia not in medias_finais_por_materia:
                        medias_finais_por_materia[nome_materia] = []
                    medias_finais_por_materia[nome_materia].append(media_bim)
                    medias_bimestre.append(media_bim)
                    
                    # Determinar situação
                    if media_bim >= 7.0:
                        situacao = "✅ Aprovado"
                        situacao_color = "green"
                    elif media_bim >= 5.0:
                        situacao = "⚠️ Recuperação"
                        situacao_color = "orange"
                    else:
                        situacao = "❌ Reprovado"
                        situacao_color = "red"
                else:
                    media_str = "N/L"
                    situacao = "⏳ Pendente"
                    situacao_color = "gray"
                
                # Inserir na tabela
                tree_bimestre.insert('', 'end', values=(nome_materia, val_np1, val_np2, media_str, situacao))
            
            # Média geral do bimestre
            if medias_bimestre:
                media_geral_bim = sum(medias_bimestre) / len(medias_bimestre)
                status_frame = customtkinter.CTkFrame(bim_frame, fg_color="transparent")
                status_frame.pack(fill='x', padx=15, pady=(5, 15))
                
                customtkinter.CTkLabel(status_frame, 
                                      text=f"📊 Média Geral do {bimestre}º Bimestre: {media_geral_bim:.2f}", 
                                      font=customtkinter.CTkFont(size=14, weight="bold"),
                                      text_color=("green" if media_geral_bim >= 7.0 else 
                                                 "orange" if media_geral_bim >= 5.0 else "red")).pack()

        # Resumo Final
        if medias_finais_por_materia:
            resumo_frame = customtkinter.CTkFrame(main_frame)
            resumo_frame.pack(fill='x', pady=(20, 0))
            
            customtkinter.CTkLabel(resumo_frame, 
                                  text="🎯 RESUMO FINAL DO ANO LETIVO", 
                                  font=customtkinter.CTkFont(size=18, weight="bold"),
                                  text_color=("#1f538d", "#3b8ed0")).pack(pady=15)
            
            # Tabela de médias finais por matéria
            tree_final = ttk.Treeview(resumo_frame, 
                                    columns=('materia', 'media_final', 'situacao_final'), 
                                    show='headings', height=8)
            
            tree_final.heading('materia', text='Matéria')
            tree_final.column('materia', width=200)
            tree_final.heading('media_final', text='Média Final')
            tree_final.column('media_final', width=120, anchor='center')
            tree_final.heading('situacao_final', text='Situação Final')
            tree_final.column('situacao_final', width=150, anchor='center')
            
            tree_final.pack(fill='x', padx=15, pady=(0, 10))
            
            medias_gerais = []
            for materia_nome, medias_bimestrais in medias_finais_por_materia.items():
                if medias_bimestrais:
                    media_final = sum(medias_bimestrais) / len(medias_bimestrais)
                    medias_gerais.append(media_final)
                    
                    # Situação final
                    if media_final >= 7.0:
                        situacao_final = "🎉 APROVADO"
                    elif media_final >= 5.0:
                        situacao_final = "📝 RECUPERAÇÃO FINAL"
                    else:
                        situacao_final = "🚫 REPROVADO"
                    
                    tree_final.insert('', 'end', values=(
                        materia_nome, 
                        f"{media_final:.2f}", 
                        situacao_final
                    ))
            
            # Média geral do aluno
            if medias_gerais:
                media_geral_aluno = sum(medias_gerais) / len(medias_gerais)
                
                resultado_frame = customtkinter.CTkFrame(resumo_frame)
                resultado_frame.pack(fill='x', padx=15, pady=15)
                
                customtkinter.CTkLabel(resultado_frame, 
                                      text=f"🏆 MÉDIA GERAL DO ALUNO: {media_geral_aluno:.2f}", 
                                      font=customtkinter.CTkFont(size=16, weight="bold"),
                                      text_color=("green" if media_geral_aluno >= 7.0 else 
                                                 "orange" if media_geral_aluno >= 5.0 else "red")).pack(pady=10)
                
                # Status final do aluno
                if media_geral_aluno >= 7.0:
                    status_texto = "🎊 PARABÉNS! Aluno APROVADO no ano letivo!"
                    status_cor = "green"
                elif media_geral_aluno >= 5.0:
                    status_texto = "📚 Aluno em RECUPERAÇÃO FINAL - Precisa melhorar o desempenho"
                    status_cor = "orange"
                else:
                    status_texto = "❗ Aluno REPROVADO - Necessária recuperação intensiva"
                    status_cor = "red"
                
                customtkinter.CTkLabel(resultado_frame, 
                                      text=status_texto, 
                                      font=customtkinter.CTkFont(size=14, weight="bold"),
                                      text_color=status_cor).pack(pady=(0, 10))

        # Botões de ação no final
        botoes_frame = customtkinter.CTkFrame(main_frame)
        botoes_frame.pack(fill='x', pady=20)
        
        customtkinter.CTkButton(botoes_frame, 
                              text="🖨️ Gerar Relatório Detalhado",
                              command=lambda: self._gerar_relatorio_boletim(ra_aluno),
                              fg_color="#28a745",
                              hover_color="#218838",
                              font=customtkinter.CTkFont(weight="bold")).pack(side='left', padx=5)
        
        customtkinter.CTkButton(botoes_frame, 
                              text="📊 Estatísticas Detalhadas",
                              command=lambda: self._mostrar_estatisticas_aluno(ra_aluno),
                              fg_color="#17a2b8",
                              hover_color="#138496",
                              font=customtkinter.CTkFont(weight="bold")).pack(side='left', padx=5)
        
        customtkinter.CTkButton(botoes_frame, 
                              text="🔄 Atualizar Boletim",
                              command=lambda: self._aluno_boletim_bimestral_tab(parent_tab),
                              fg_color="#ffc107",
                              hover_color="#e0a800",
                              font=customtkinter.CTkFont(weight="bold")).pack(side='right', padx=5)

    def _gerar_relatorio_boletim(self, ra_aluno):
        """Gera um relatório detalhado do boletim do aluno"""
        try:
            from datetime import datetime
            
            # Buscar dados do aluno
            usuarios = carregar_json(ALUNOS_FILE)
            aluno_info = next((u for u in usuarios if u.get('ra') == ra_aluno), None)
            
            if not aluno_info:
                messagebox.showerror("Erro", "Dados do aluno não encontrados.")
                return
            
            # Encontrar turma
            turmas = carregar_json(TURMAS_FILE)
            turma_aluno = None
            for t in turmas:
                if ra_aluno in t.get('alunos', []):
                    turma_aluno = t
                    break
            
            if not turma_aluno:
                messagebox.showerror("Erro", "Turma do aluno não encontrada.")
                return
            
            # Gerar relatório em texto
            relatorio = f"""
╔══════════════════════════════════════════════════════════════╗
║                    BOLETIM ESCOLAR COMPLETO                  ║
╠══════════════════════════════════════════════════════════════╣
║ Data de Emissão: {datetime.now().strftime('%d/%m/%Y às %H:%M')}                          ║
║                                                              ║
║ DADOS DO ALUNO:                                              ║
║ Nome: {aluno_info.get('nome', 'N/A'):<52} ║
║ RA: {ra_aluno:<58} ║
║ Turma: {turma_aluno.get('serie', 'N/A')} - {turma_aluno.get('turma', 'N/A'):<50} ║
╚══════════════════════════════════════════════════════════════╝

"""
            
            # Carregar dados para o relatório
            materias = carregar_json(MATERIAS_FILE)
            notas = carregar_json(NOTAS_FILE)
            turma_id = turma_aluno.get('id')
            materias_aluno = [m for m in materias if m.get('turma_id') == turma_id]
            
            if not materias_aluno:
                relatorio += "\n❌ Nenhuma matéria encontrada para esta turma.\n"
            else:
                relatorio += "\n📚 NOTAS POR BIMESTRE:\n" + "="*60 + "\n"
                
                # Processar cada bimestre
                medias_finais = {}
                
                for bimestre in range(1, 5):
                    relatorio += f"\n🔸 {bimestre}º BIMESTRE:\n" + "-" * 40 + "\n"
                    bim_prefix = f"B{bimestre}"
                    
                    for materia in materias_aluno:
                        materia_id = materia['id']
                        nome_materia = materia['nome']
                        
                        # Buscar notas
                        nota_np1 = next((n for n in notas if 
                                       n.get('aluno_ra') == ra_aluno and 
                                       n.get('materia_id') == materia_id and 
                                       n.get('tipo_nota') == f"{bim_prefix}_NP1"), None)
                        
                        nota_np2 = next((n for n in notas if 
                                       n.get('aluno_ra') == ra_aluno and 
                                       n.get('materia_id') == materia_id and 
                                       n.get('tipo_nota') == f"{bim_prefix}_NP2"), None)
                        
                        val_np1 = nota_np1.get('valor') if nota_np1 else "N/L"
                        val_np2 = nota_np2.get('valor') if nota_np2 else "N/L"
                        
                        if isinstance(val_np1, (int, float)) and isinstance(val_np2, (int, float)):
                            media_bim = (val_np1 + val_np2) / 2
                            if nome_materia not in medias_finais:
                                medias_finais[nome_materia] = []
                            medias_finais[nome_materia].append(media_bim)
                            status = "✅" if media_bim >= 7.0 else "⚠️" if media_bim >= 5.0 else "❌"
                            relatorio += f"  {nome_materia:<20} | NP1: {val_np1:>5} | NP2: {val_np2:>5} | Média: {media_bim:>5.2f} {status}\n"
                        else:
                            relatorio += f"  {nome_materia:<20} | NP1: {val_np1:>5} | NP2: {val_np2:>5} | Média: {'N/L':>5} ⏳\n"
                
                # Resumo final
                relatorio += "\n" + "="*60 + "\n📊 RESUMO FINAL:\n" + "="*60 + "\n"
                
                if medias_finais:
                    medias_gerais = []
                    for materia_nome, medias_bimestrais in medias_finais.items():
                        if medias_bimestrais:
                            media_final = sum(medias_bimestrais) / len(medias_bimestrais)
                            medias_gerais.append(media_final)
                            status_final = "🎉 APROVADO" if media_final >= 7.0 else "📝 RECUPERAÇÃO" if media_final >= 5.0 else "🚫 REPROVADO"
                            relatorio += f"{materia_nome:<25} | Média Final: {media_final:>6.2f} | {status_final}\n"
                    
                    if medias_gerais:
                        media_geral_aluno = sum(medias_gerais) / len(medias_gerais)
                        relatorio += "\n" + "="*60 + "\n"
                        relatorio += f"🏆 MÉDIA GERAL DO ALUNO: {media_geral_aluno:.2f}\n"
                        
                        if media_geral_aluno >= 7.0:
                            relatorio += "🎊 SITUAÇÃO: APROVADO NO ANO LETIVO!\n"
                        elif media_geral_aluno >= 5.0:
                            relatorio += "📚 SITUAÇÃO: RECUPERAÇÃO FINAL\n"
                        else:
                            relatorio += "❗ SITUAÇÃO: REPROVADO\n"
            
            relatorio += "\n" + "="*60 + "\n"
            relatorio += "📋 Relatório gerado automaticamente pelo Sistema Acadêmico\n"
            relatorio += f"⏰ {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}\n"
            
            # Mostrar relatório em nova janela
            janela_relatorio = customtkinter.CTkToplevel(self)
            janela_relatorio.title(f"📊 Relatório Completo - {aluno_info.get('nome', 'Aluno')}")
            janela_relatorio.geometry("800x600")
            janela_relatorio.transient(self)
            
            texto_relatorio = customtkinter.CTkTextbox(janela_relatorio, font=customtkinter.CTkFont(family="Courier", size=12))
            texto_relatorio.pack(fill='both', expand=True, padx=20, pady=20)
            texto_relatorio.insert("1.0", relatorio)
            texto_relatorio.configure(state="disabled")
            
            customtkinter.CTkButton(janela_relatorio, text="❌ Fechar", 
                                  command=janela_relatorio.destroy).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar relatório: {str(e)}")

    def _mostrar_estatisticas_aluno(self, ra_aluno):
        """Mostra estatísticas detalhadas do desempenho do aluno"""
        try:
            # Buscar dados
            usuarios = carregar_json(ALUNOS_FILE)
            aluno_info = next((u for u in usuarios if u.get('ra') == ra_aluno), None)
            
            if not aluno_info:
                messagebox.showerror("Erro", "Dados do aluno não encontrados.")
                return
            
            turmas = carregar_json(TURMAS_FILE)
            turma_aluno = None
            for t in turmas:
                if ra_aluno in t.get('alunos', []):
                    turma_aluno = t
                    break
            
            materias = carregar_json(MATERIAS_FILE)
            notas = carregar_json(NOTAS_FILE)
            turma_id = turma_aluno.get('id')
            materias_aluno = [m for m in materias if m.get('turma_id') == turma_id]
            
            # Calcular estatísticas
            todas_medias = []
            medias_por_bimestre = {1: [], 2: [], 3: [], 4: []}
            melhor_materia = {"nome": "", "media": 0}
            pior_materia = {"nome": "", "media": 10}
            
            for materia in materias_aluno:
                materia_id = materia['id']
                nome_materia = materia['nome']
                medias_materia = []
                
                for bimestre in range(1, 5):
                    bim_prefix = f"B{bimestre}"
                    
                    nota_np1 = next((n for n in notas if 
                                   n.get('aluno_ra') == ra_aluno and 
                                   n.get('materia_id') == materia_id and 
                                   n.get('tipo_nota') == f"{bim_prefix}_NP1"), None)
                    
                    nota_np2 = next((n for n in notas if 
                                   n.get('aluno_ra') == ra_aluno and 
                                   n.get('materia_id') == materia_id and 
                                   n.get('tipo_nota') == f"{bim_prefix}_NP2"), None)
                    
                    val_np1 = nota_np1.get('valor') if nota_np1 else None
                    val_np2 = nota_np2.get('valor') if nota_np2 else None
                    
                    if isinstance(val_np1, (int, float)) and isinstance(val_np2, (int, float)):
                        media_bim = (val_np1 + val_np2) / 2
                        medias_materia.append(media_bim)
                        medias_por_bimestre[bimestre].append(media_bim)
                        todas_medias.append(media_bim)
                
                if medias_materia:
                    media_final_materia = sum(medias_materia) / len(medias_materia)
                    if media_final_materia > melhor_materia["media"]:
                        melhor_materia = {"nome": nome_materia, "media": media_final_materia}
                    if media_final_materia < pior_materia["media"]:
                        pior_materia = {"nome": nome_materia, "media": media_final_materia}
            
            # Criar janela de estatísticas
            janela_stats = customtkinter.CTkToplevel(self)
            janela_stats.title(f"📈 Estatísticas - {aluno_info.get('nome', 'Aluno')}")
            janela_stats.geometry("600x500")
            janela_stats.transient(self)
            
            scroll_frame = customtkinter.CTkScrollableFrame(janela_stats)
            scroll_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            # Título
            customtkinter.CTkLabel(scroll_frame, text="📈 ANÁLISE ESTATÍSTICA DO DESEMPENHO", 
                                  font=customtkinter.CTkFont(size=16, weight="bold")).pack(pady=(0, 20))
            
            if todas_medias:
                media_geral = sum(todas_medias) / len(todas_medias)
                
                # Estatísticas gerais
                stats_frame = customtkinter.CTkFrame(scroll_frame)
                stats_frame.pack(fill='x', pady=(0, 15))
                
                customtkinter.CTkLabel(stats_frame, text="📊 Estatísticas Gerais", 
                                      font=customtkinter.CTkFont(size=14, weight="bold"),
                                      text_color=("#1f538d", "#3b8ed0")).pack(pady=10)
                
                stats_info = [
                    f"🎯 Média Geral: {media_geral:.2f}",
                    f"📈 Maior Nota: {max(todas_medias):.2f}",
                    f"📉 Menor Nota: {min(todas_medias):.2f}",
                    f"📝 Total de Avaliações: {len(todas_medias)}",
                    f"✅ Notas ≥ 7.0: {sum(1 for m in todas_medias if m >= 7.0)}",
                    f"⚠️ Notas 5.0-6.9: {sum(1 for m in todas_medias if 5.0 <= m < 7.0)}",
                    f"❌ Notas < 5.0: {sum(1 for m in todas_medias if m < 5.0)}"
                ]
                
                for info in stats_info:
                    customtkinter.CTkLabel(stats_frame, text=info).pack(anchor='w', padx=20, pady=2)
                
                # Desempenho por bimestre
                bim_frame = customtkinter.CTkFrame(scroll_frame)
                bim_frame.pack(fill='x', pady=(0, 15))
                
                customtkinter.CTkLabel(bim_frame, text="📅 Desempenho por Bimestre", 
                                      font=customtkinter.CTkFont(size=14, weight="bold"),
                                      text_color=("#1f538d", "#3b8ed0")).pack(pady=10)
                
                for bim, medias in medias_por_bimestre.items():
                    if medias:
                        media_bim = sum(medias) / len(medias)
                        customtkinter.CTkLabel(bim_frame, 
                                              text=f"{bim}º Bimestre: {media_bim:.2f} ({len(medias)} avaliações)").pack(anchor='w', padx=20, pady=2)
                
                # Melhores e piores matérias
                desempenho_frame = customtkinter.CTkFrame(scroll_frame)
                desempenho_frame.pack(fill='x', pady=(0, 15))
                
                customtkinter.CTkLabel(desempenho_frame, text="🏆 Análise por Matéria", 
                                      font=customtkinter.CTkFont(size=14, weight="bold"),
                                      text_color=("#1f538d", "#3b8ed0")).pack(pady=10)
                
                if melhor_materia["nome"]:
                    customtkinter.CTkLabel(desempenho_frame, 
                                          text=f"🥇 Melhor Matéria: {melhor_materia['nome']} ({melhor_materia['media']:.2f})",
                                          text_color="green").pack(anchor='w', padx=20, pady=2)
                
                if pior_materia["nome"] and pior_materia["media"] < 10:
                    customtkinter.CTkLabel(desempenho_frame, 
                                          text=f"📚 Matéria para Focar: {pior_materia['nome']} ({pior_materia['media']:.2f})",
                                          text_color="orange").pack(anchor='w', padx=20, pady=2)
            else:
                customtkinter.CTkLabel(scroll_frame, text="❌ Nenhuma nota encontrada para análise.", 
                                      font=customtkinter.CTkFont(size=14)).pack(pady=50)
            
            customtkinter.CTkButton(janela_stats, text="❌ Fechar", 
                                  command=janela_stats.destroy).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao calcular estatísticas: {str(e)}")

    def _aluno_atividades_tab(self, parent_tab):
        """Aba para visualização de atividades disponíveis para o aluno"""
        ra_aluno = self.usuario_logado.get('ra')
        
        if not ra_aluno:
            customtkinter.CTkLabel(parent_tab, text="Erro: RA do aluno não encontrado.", 
                                 font=customtkinter.CTkFont(size=16)).pack(pady=50)
            return

        # Encontrar a turma do aluno
        turmas = carregar_json(TURMAS_FILE)
        turma_aluno = None
        for t in turmas:
            if ra_aluno in t.get('alunos', []):
                turma_aluno = t
                break
        
        if not turma_aluno:
            customtkinter.CTkLabel(parent_tab, text="Você ainda não foi matriculado em nenhuma turma.", 
                                 font=customtkinter.CTkFont(size=16)).pack(pady=50)
            return

        # Removido: Frame de filtros (não mais necessário pois só mostra atividades liberadas)

        # Tabela de atividades
        tree_atividades = ttk.Treeview(parent_tab, columns=('materia', 'aula', 'atividade', 'tipo', 'data_entrega', 'pontuacao', 'status'), show='headings')
        
        # Configurar cabeçalhos
        tree_atividades.heading('materia', text='Matéria')
        tree_atividades.column('materia', width=120)
        tree_atividades.heading('aula', text='Aula')
        tree_atividades.column('aula', width=130)
        tree_atividades.heading('atividade', text='Atividade')
        tree_atividades.column('atividade', width=150)
        tree_atividades.heading('tipo', text='Tipo')
        tree_atividades.column('tipo', width=120, anchor='center')
        tree_atividades.heading('data_entrega', text='Data de Entrega')
        tree_atividades.column('data_entrega', width=120, anchor='center')
        tree_atividades.heading('pontuacao', text='Pontuação Máx.')
        tree_atividades.column('pontuacao', width=100, anchor='center')
        tree_atividades.heading('status', text='Status')
        tree_atividades.column('status', width=100, anchor='center')
        
        tree_atividades.pack(fill='both', expand=True, padx=10, pady=10)

        # Scrollbar para a tabela
        scrollbar = ttk.Scrollbar(parent_tab, orient='vertical', command=tree_atividades.yview)
        tree_atividades.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        def carregar_atividades():
            """Carrega atividades LIBERADAS e dentro do prazo para o aluno"""
            # Limpar tabela
            for item in tree_atividades.get_children():
                tree_atividades.delete(item)

            # Carregar dados necessários
            materias = carregar_json(MATERIAS_FILE)
            registros_aula = carregar_json(REGISTROS_AULA_FILE)
            
            # Filtrar matérias da turma do aluno
            materias_aluno = [m for m in materias if m.get('turma_id') == turma_aluno.get('id')]
            
            # Obter IDs das matérias do aluno
            ids_materias_aluno = [m['id'] for m in materias_aluno]
            
            # Processar registros de aula e suas atividades
            for registro in registros_aula:
                materia_id = registro.get('materia_id')
                
                # Verificar se é uma matéria da turma do aluno
                if materia_id not in ids_materias_aluno:
                    continue
                
                # Encontrar nome da matéria
                materia_nome = next((m['nome'] for m in materias_aluno if m['id'] == materia_id), 'Matéria Desconhecida')
                nome_aula = registro.get('nome_aula', '')
                
                # Processar atividades do registro
                atividades = registro.get('atividades', [])
                for atividade in atividades:
                    # Obter status da atividade para este aluno
                    status_atividade = obter_status_atividade_aluno(atividade, ra_aluno)
                    
                    # Só mostra atividades liberadas pelo professor
                    if atividade.get('status') != "Liberada":
                        continue
                    
                    # Status visual baseado no status real da atividade
                    data_entrega = atividade.get('data_entrega', '')
                    status_real = obter_status_atividade_aluno(atividade, ra_aluno)
                    
                    if status_real == 'Expirada':
                        status_visual = "⏰ Expirada"
                    elif status_real == 'Respondida':
                        status_visual = "✅ Respondida"
                    else:  # Disponível
                        status_visual = "📝 Disponível"
                    
                    # Inserir na tabela
                    valores = [
                        materia_nome,
                        nome_aula,
                        atividade.get('nome', ''),
                        atividade.get('tipo', 'Não especificado'),
                        data_entrega,
                        f"{atividade.get('pontuacao_maxima', 0):.1f}",
                        status_visual
                    ]
                    
                    tree_atividades.insert('', 'end', values=valores)

        # Frame de botões
        btn_frame = customtkinter.CTkFrame(parent_tab)
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        # Botão para responder atividade
        customtkinter.CTkButton(
            btn_frame, 
            text="📝 Responder Atividade", 
            command=lambda: self._responder_atividade_aluno(tree_atividades, turma_aluno, ra_aluno),
            fg_color="#28a745",
            hover_color="#218838",
            font=customtkinter.CTkFont(weight="bold")
        ).pack(side='left', padx=5)
        
        # Botão para visualizar detalhes da atividade
        customtkinter.CTkButton(
            btn_frame, 
            text="👁 Ver Detalhes", 
            command=lambda: self._ver_detalhes_atividade_aluno(tree_atividades),
            fg_color="#6c757d",
            hover_color="#545b62"
        ).pack(side='left', padx=5)
        
        # Botão para ver histórico de respostas
        customtkinter.CTkButton(
            btn_frame, 
            text="📋 Minhas Respostas", 
            command=lambda: self._ver_historico_respostas_aluno(ra_aluno),
            fg_color="#fd7e14",
            hover_color="#e36414"
        ).pack(side='right', padx=5)
        
        # Botão de Atualizar
        customtkinter.CTkButton(
            btn_frame, 
            text='🔄 Atualizar', 
            command=lambda: carregar_atividades(),
            fg_color="#17a2b8",
            hover_color="#138496",
            font=customtkinter.CTkFont(weight="bold")
        ).pack(side='right', padx=5)

        # Carregar atividades inicialmente
        carregar_atividades()

    def _ver_detalhes_atividade_aluno(self, tree_atividades):
        """Mostra detalhes da atividade selecionada"""
        selection = tree_atividades.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Por favor, selecione uma atividade para ver os detalhes.")
            return
        
        item = tree_atividades.item(selection[0])
        valores = item['values']
        
        if len(valores) < 7:
            messagebox.showerror("Erro", "Dados da atividade incompletos.")
            return
        
        materia_nome = valores[0]
        nome_aula = valores[1]
        nome_atividade = valores[2]
        tipo_atividade = valores[3]
        data_entrega = valores[4]
        pontuacao_max = valores[5]
        status = valores[6]
        
        # Buscar dados completos da atividade
        registros_aula = carregar_json(REGISTROS_AULA_FILE)
        atividade_completa = None
        
        for registro in registros_aula:
            if registro.get('nome_aula') == nome_aula:
                atividades = registro.get('atividades', [])
                for ativ in atividades:
                    if ativ.get('nome') == nome_atividade:
                        atividade_completa = ativ
                        break
                if atividade_completa:
                    break
        
        if not atividade_completa:
            messagebox.showerror("Erro", "Detalhes da atividade não encontrados.")
            return
        
        # Verificação de segurança: não permitir visualização de atividades não liberadas
        if atividade_completa.get('status', 'Não Liberada') != "Liberada":
            messagebox.showerror("Acesso Negado", "Esta atividade não está liberada para visualização.")
            return
        
        # Verificar prazo
        if not verificar_prazo_atividade(atividade_completa.get('data_entrega', '')):
            messagebox.showwarning("Prazo Expirado", "O prazo para esta atividade já expirou.")
            # Continua permitindo visualização, mas não permite resposta
        
        # Criar janela de detalhes
        janela_detalhes = customtkinter.CTkToplevel(self)
        janela_detalhes.title("Detalhes da Atividade")
        janela_detalhes.geometry("700x600")
        janela_detalhes.transient(self)
        janela_detalhes.grab_set()

        # Título
        customtkinter.CTkLabel(janela_detalhes, text=nome_atividade, 
                              font=customtkinter.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        # Informações da atividade
        info_frame = customtkinter.CTkFrame(janela_detalhes)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        infos = [
            ("Matéria:", materia_nome),
            ("Aula:", nome_aula),
            ("Tipo:", tipo_atividade),
            ("Data de Entrega:", data_entrega),
            ("Pontuação Máxima:", pontuacao_max),
            ("Status:", status)
        ]
        
        for i, (label, valor) in enumerate(infos):
            customtkinter.CTkLabel(info_frame, text=label, font=customtkinter.CTkFont(weight="bold")).grid(row=i, column=0, sticky='w', padx=10, pady=5)
            customtkinter.CTkLabel(info_frame, text=valor).grid(row=i, column=1, sticky='w', padx=10, pady=5)
        
        # Descrição
        customtkinter.CTkLabel(janela_detalhes, text="Descrição:", 
                              font=customtkinter.CTkFont(weight="bold")).pack(anchor='w', padx=20, pady=(20,5))
        
        desc_textbox = customtkinter.CTkTextbox(janela_detalhes, height=80)
        desc_textbox.pack(fill='x', padx=20, pady=(0,10))
        desc_textbox.insert("1.0", atividade_completa.get('descricao', 'Sem descrição'))
        desc_textbox.configure(state="disabled")
        
        # Mostrar perguntas baseado no tipo
        perguntas = atividade_completa.get('perguntas', [])
        if perguntas:
            customtkinter.CTkLabel(janela_detalhes, text="Perguntas:", 
                                  font=customtkinter.CTkFont(weight="bold")).pack(anchor='w', padx=20, pady=(20,5))
            
            perguntas_frame = customtkinter.CTkScrollableFrame(janela_detalhes, height=250)
            perguntas_frame.pack(fill='both', expand=True, padx=20, pady=(0,10))
            
            if tipo_atividade == "Múltipla Escolha":
                self._mostrar_perguntas_multipla_escolha(perguntas_frame, perguntas)
            elif tipo_atividade == "Dissertativa":
                self._mostrar_perguntas_dissertativas(perguntas_frame, perguntas)
        
        # Botão fechar
        customtkinter.CTkButton(janela_detalhes, text="Fechar", command=janela_detalhes.destroy).pack(pady=10)

    def _mostrar_perguntas_multipla_escolha(self, parent_frame, perguntas):
        """Mostra as perguntas de múltipla escolha"""
        for i, pergunta in enumerate(perguntas):
            pergunta_frame = customtkinter.CTkFrame(parent_frame)
            pergunta_frame.pack(fill='x', padx=5, pady=10)
            pergunta_frame.grid_columnconfigure(0, weight=1)
            
            # Título da pergunta
            customtkinter.CTkLabel(pergunta_frame, text=f"Pergunta {i+1}:", 
                                  font=customtkinter.CTkFont(weight="bold")).grid(row=0, column=0, sticky='w', padx=10, pady=5)
            
            # Texto da pergunta
            pergunta_text = customtkinter.CTkTextbox(pergunta_frame, height=60)
            pergunta_text.grid(row=1, column=0, sticky='ew', padx=10, pady=5)
            pergunta_text.insert("1.0", pergunta.get('pergunta', ''))
            pergunta_text.configure(state="disabled")
            
            # Alternativas
            alternativas = pergunta.get('alternativas', {})
            for j, (letra, texto) in enumerate(alternativas.items()):
                customtkinter.CTkLabel(pergunta_frame, text=f"{letra}) {texto}").grid(row=j+2, column=0, sticky='w', padx=20, pady=2)

    def _mostrar_perguntas_dissertativas(self, parent_frame, perguntas):
        """Mostra as perguntas dissertativas"""
        for i, pergunta in enumerate(perguntas):
            pergunta_frame = customtkinter.CTkFrame(parent_frame)
            pergunta_frame.pack(fill='x', padx=5, pady=10)
            pergunta_frame.grid_columnconfigure(0, weight=1)
            
            # Título da pergunta
            customtkinter.CTkLabel(pergunta_frame, text=f"Pergunta {i+1}:", 
                                  font=customtkinter.CTkFont(weight="bold")).grid(row=0, column=0, sticky='w', padx=10, pady=5)
            
            # Texto da pergunta
            pergunta_text = customtkinter.CTkTextbox(pergunta_frame, height=80)
            pergunta_text.grid(row=1, column=0, sticky='ew', padx=10, pady=5)
            pergunta_text.insert("1.0", pergunta.get('pergunta', ''))
            pergunta_text.configure(state="disabled")
            
            # Critérios de avaliação (se existirem)
            criterios = pergunta.get('criterios', '')
            if criterios:
                customtkinter.CTkLabel(pergunta_frame, text="Critérios de Avaliação:", 
                                      font=customtkinter.CTkFont(weight="bold")).grid(row=2, column=0, sticky='w', padx=10, pady=(10,5))
                
                criterios_text = customtkinter.CTkTextbox(pergunta_frame, height=60)
                criterios_text.grid(row=3, column=0, sticky='ew', padx=10, pady=5)
                criterios_text.insert("1.0", criterios)
                criterios_text.configure(state="disabled")

    def _responder_atividade_aluno(self, tree_atividades, turma_aluno, ra_aluno):
        """Permite ao aluno responder uma atividade selecionada"""
        selection = tree_atividades.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Por favor, selecione uma atividade para responder.")
            return
        
        item = tree_atividades.item(selection[0])
        valores = item['values']
        
        if len(valores) < 7:
            messagebox.showerror("Erro", "Dados da atividade incompletos.")
            return
        
        materia_nome = valores[0]
        nome_aula = valores[1]
        nome_atividade = valores[2]
        tipo_atividade = valores[3]
        data_entrega = valores[4]
        status = valores[6]
        
        # Verificar se a atividade ainda está no prazo
        if "Expirada" in status:
            messagebox.showerror("Prazo Expirado", "O prazo para responder esta atividade já expirou.")
            return
        
        # Verificar se já foi respondida
        if "Respondida" in status:
            messagebox.showinfo("Atividade Respondida", "Você já respondeu esta atividade.")
            return
        
        # Buscar dados completos da atividade
        registros_aula = carregar_json(REGISTROS_AULA_FILE)
        atividade_completa = None
        registro_pai = None
        
        for registro in registros_aula:
            if registro.get('nome_aula') == nome_aula:
                atividades = registro.get('atividades', [])
                for ativ in atividades:
                    if ativ.get('nome') == nome_atividade:
                        atividade_completa = ativ
                        registro_pai = registro
                        break
                if atividade_completa:
                    break
        
        if not atividade_completa:
            messagebox.showerror("Erro", "Detalhes da atividade não encontrados.")
            return
        
        # Verificação final de prazo
        if not verificar_prazo_atividade(atividade_completa.get('data_entrega', '')):
            messagebox.showerror("Prazo Expirado", "O prazo para responder esta atividade já expirou.")
            return
        
        # VERIFICAÇÃO CRÍTICA: Confirmar se já foi respondida antes de abrir o formulário
        ja_respondida, data_resposta = verificar_atividade_ja_respondida(atividade_completa.get('id'), ra_aluno)
        if ja_respondida:
            messagebox.showwarning("⚠️ Atividade Já Respondida", 
                                   f"Você já respondeu esta atividade em {data_resposta}.\n\n"
                                   f"🚫 REGRA: Cada aluno pode responder uma atividade apenas UMA VEZ.\n\n"
                                   f"✅ Suas respostas já foram registradas no sistema.\n"
                                   f"📋 Consulte seu professor para mais informações.")
            return
        
        # Criar janela de resposta
        janela_resposta = customtkinter.CTkToplevel(self)
        janela_resposta.title(f"Responder: {nome_atividade}")
        janela_resposta.geometry("800x700")
        janela_resposta.transient(self)
        janela_resposta.grab_set()

        # Cabeçalho com informações da atividade
        header_frame = customtkinter.CTkFrame(janela_resposta)
        header_frame.pack(fill='x', padx=20, pady=10)
        
        customtkinter.CTkLabel(header_frame, text=nome_atividade, 
                              font=customtkinter.CTkFont(size=18, weight="bold")).pack(pady=5)
        
        info_text = f"Matéria: {materia_nome} | Aula: {nome_aula} | Tipo: {tipo_atividade} | Entrega: {data_entrega}"
        customtkinter.CTkLabel(header_frame, text=info_text, 
                              font=customtkinter.CTkFont(size=12)).pack(pady=2)
        
        # Mostrar tempo restante
        tempo_restante = self._calcular_tempo_restante(data_entrega)
        customtkinter.CTkLabel(header_frame, text=f"⏰ Tempo restante: {tempo_restante}", 
                              font=customtkinter.CTkFont(size=12, weight="bold"),
                              text_color=("red" if "expirou" in tempo_restante.lower() else "orange")).pack(pady=2)
        
        # Descrição da atividade
        desc_frame = customtkinter.CTkFrame(janela_resposta)
        desc_frame.pack(fill='x', padx=20, pady=5)
        
        customtkinter.CTkLabel(desc_frame, text="Descrição:", 
                              font=customtkinter.CTkFont(weight="bold")).pack(anchor='w', padx=10, pady=5)
        
        desc_textbox = customtkinter.CTkTextbox(desc_frame, height=60)
        desc_textbox.pack(fill='x', padx=10, pady=(0,10))
        desc_textbox.insert("1.0", atividade_completa.get('descricao', 'Sem descrição'))
        desc_textbox.configure(state="disabled")
        
        # Frame scrollável para perguntas
        perguntas_scroll = customtkinter.CTkScrollableFrame(janela_resposta, height=350)
        perguntas_scroll.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Criar campos de resposta baseado no tipo
        perguntas = atividade_completa.get('perguntas', [])
        respostas_widgets = []
        
        if tipo_atividade == "Múltipla Escolha":
            respostas_widgets = self._criar_formulario_multipla_escolha(perguntas_scroll, perguntas)
        elif tipo_atividade == "Dissertativa":
            respostas_widgets = self._criar_formulario_dissertativo(perguntas_scroll, perguntas)
        
        # Botões de ação
        btn_frame = customtkinter.CTkFrame(janela_resposta)
        btn_frame.pack(fill='x', padx=20, pady=10)
        
        customtkinter.CTkButton(btn_frame, text="❌ Cancelar", 
                              fg_color="#dc3545", hover_color="#c82333",
                              command=janela_resposta.destroy).pack(side='left', padx=5)
        
        customtkinter.CTkButton(btn_frame, text="📤 Enviar Respostas", 
                              fg_color="#28a745", hover_color="#218838",
                              font=customtkinter.CTkFont(weight="bold"),
                              command=lambda: self._salvar_respostas_aluno(
                                  janela_resposta, atividade_completa, registro_pai, 
                                  respostas_widgets, ra_aluno, tipo_atividade
                              )).pack(side='right', padx=5)

    def _calcular_tempo_restante(self, data_entrega_str):
        """Calcula o tempo restante para entrega da atividade"""
        try:
            data_entrega = datetime.strptime(data_entrega_str, '%d/%m/%Y')
            data_limite = data_entrega.replace(hour=23, minute=59, second=59)
            data_atual = datetime.now()
            
            if data_atual > data_limite:
                return "❌ Prazo expirou"
            
            diferenca = data_limite - data_atual
            dias = diferenca.days
            horas, resto = divmod(diferenca.seconds, 3600)
            minutos, _ = divmod(resto, 60)
            
            if dias > 0:
                return f"{dias} dia(s), {horas} hora(s)"
            elif horas > 0:
                return f"{horas} hora(s), {minutos} minuto(s)"
            else:
                return f"{minutos} minuto(s)"
        except:
            return "Não disponível"

    def _criar_formulario_multipla_escolha(self, parent_frame, perguntas):
        """Cria formulário de resposta para múltipla escolha"""
        respostas_widgets = []
        
        for i, pergunta in enumerate(perguntas):
            pergunta_frame = customtkinter.CTkFrame(parent_frame)
            pergunta_frame.pack(fill='x', padx=5, pady=10)
            pergunta_frame.grid_columnconfigure(0, weight=1)
            
            # Título da pergunta
            customtkinter.CTkLabel(pergunta_frame, text=f"Pergunta {i+1}:", 
                                  font=customtkinter.CTkFont(weight="bold")).grid(row=0, column=0, sticky='w', padx=10, pady=5)
            
            # Texto da pergunta
            pergunta_text = customtkinter.CTkTextbox(pergunta_frame, height=60)
            pergunta_text.grid(row=1, column=0, sticky='ew', padx=10, pady=5)
            pergunta_text.insert("1.0", pergunta.get('pergunta', ''))
            pergunta_text.configure(state="disabled")
            
            # Alternativas com radio buttons
            alternativas = pergunta.get('alternativas', {})
            resposta_var = tk.StringVar()
            respostas_widgets.append(resposta_var)
            
            customtkinter.CTkLabel(pergunta_frame, text="Escolha sua resposta:", 
                                  font=customtkinter.CTkFont(weight="bold")).grid(row=2, column=0, sticky='w', padx=10, pady=(10,5))
            
            for j, (letra, texto) in enumerate(alternativas.items()):
                radio = customtkinter.CTkRadioButton(pergunta_frame, text=f"{letra}) {texto}", 
                                                   variable=resposta_var, value=letra)
                radio.grid(row=j+3, column=0, sticky='w', padx=20, pady=2)
        
        return respostas_widgets

    def _criar_formulario_dissertativo(self, parent_frame, perguntas):
        """Cria formulário de resposta para perguntas dissertativas"""
        respostas_widgets = []
        
        for i, pergunta in enumerate(perguntas):
            pergunta_frame = customtkinter.CTkFrame(parent_frame)
            pergunta_frame.pack(fill='x', padx=5, pady=10)
            pergunta_frame.grid_columnconfigure(0, weight=1)
            
            # Título da pergunta
            customtkinter.CTkLabel(pergunta_frame, text=f"Pergunta {i+1}:", 
                                  font=customtkinter.CTkFont(weight="bold")).grid(row=0, column=0, sticky='w', padx=10, pady=5)
            
            # Texto da pergunta
            pergunta_text = customtkinter.CTkTextbox(pergunta_frame, height=80)
            pergunta_text.grid(row=1, column=0, sticky='ew', padx=10, pady=5)
            pergunta_text.insert("1.0", pergunta.get('pergunta', ''))
            pergunta_text.configure(state="disabled")
            
            # Critérios de avaliação (se existirem)
            criterios = pergunta.get('criterios', '')
            if criterios:
                customtkinter.CTkLabel(pergunta_frame, text="Critérios de Avaliação:", 
                                      font=customtkinter.CTkFont(weight="bold")).grid(row=2, column=0, sticky='w', padx=10, pady=(10,5))
                
                criterios_text = customtkinter.CTkTextbox(pergunta_frame, height=60)
                criterios_text.grid(row=3, column=0, sticky='ew', padx=10, pady=5)
                criterios_text.insert("1.0", criterios)
                criterios_text.configure(state="disabled")
            
            # Campo de resposta
            customtkinter.CTkLabel(pergunta_frame, text="Sua resposta:", 
                                  font=customtkinter.CTkFont(weight="bold")).grid(row=4, column=0, sticky='w', padx=10, pady=(10,5))
            
            resposta_textbox = customtkinter.CTkTextbox(pergunta_frame, height=120)
            resposta_textbox.grid(row=5, column=0, sticky='ew', padx=10, pady=(0,10))
            resposta_textbox.insert("1.0", "Digite sua resposta aqui...")
            
            respostas_widgets.append(resposta_textbox)
        
        return respostas_widgets

    def _salvar_respostas_aluno(self, janela, atividade, registro_pai, respostas_widgets, ra_aluno, tipo_atividade):
        """Salva as respostas do aluno"""
        # VERIFICAÇÃO 1: Verificar prazo novamente antes de salvar
        if not verificar_prazo_atividade(atividade.get('data_entrega', '')):
            messagebox.showerror("Prazo Expirado", "O prazo para esta atividade expirou enquanto você respondia.")
            return
        
        # VERIFICAÇÃO 2: Verificar se já foi respondida (verificação crítica antes de salvar)
        ja_respondida, data_resposta = verificar_atividade_ja_respondida(atividade.get('id'), ra_aluno)
        if ja_respondida:
            messagebox.showerror("❌ Erro Crítico", 
                               f"ATENÇÃO: Esta atividade já foi respondida por você em {data_resposta}!\n\n"
                               f"🚫 SISTEMA DE SEGURANÇA: Não é possível responder a mesma atividade duas vezes.\n\n"
                               f"Fechando o formulário para proteger a integridade dos dados.")
            janela.destroy()
            return
        
        # Coletar respostas
        respostas = []
        
        if tipo_atividade == "Múltipla Escolha":
            for i, resposta_var in enumerate(respostas_widgets):
                resposta = resposta_var.get()
                if not resposta:
                    messagebox.showwarning("Resposta Incompleta", f"Por favor, responda a pergunta {i+1}.")
                    return
                respostas.append(resposta)
        
        elif tipo_atividade == "Dissertativa":
            for i, resposta_textbox in enumerate(respostas_widgets):
                resposta = resposta_textbox.get("1.0", "end-1c").strip()
                if not resposta or resposta == "Digite sua resposta aqui...":
                    messagebox.showwarning("Resposta Incompleta", f"Por favor, responda a pergunta {i+1}.")
                    return
                respostas.append(resposta)
        
        # VERIFICAÇÃO 3: Confirmar envio com aviso sobre única tentativa
        confirmacao = messagebox.askyesno("⚠️ Confirmar Envio - ÚLTIMA CHANCE", 
                                         f"🔔 ATENÇÃO: Você está prestes a enviar suas respostas!\n\n"
                                         f"❗ IMPORTANTE:\n"
                                         f"• Você só pode responder esta atividade UMA VEZ\n"
                                         f"• Após enviar, NÃO será possível alterar as respostas\n"
                                         f"• Esta ação é IRREVERSÍVEL\n\n"
                                         f"✅ Tem certeza que deseja enviar agora?")
        if not confirmacao:
            return
        
        # Criar estrutura da resposta
        resposta_aluno = {
            "ra_aluno": ra_aluno,
            "nome_aluno": self.usuario_logado.get('nome', ''),
            "atividade_id": atividade.get('id'),
            "atividade_nome": atividade.get('nome'),
            "materia_id": registro_pai.get('materia_id'),
            "registro_aula": registro_pai.get('nome_aula'),
            "data_resposta": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "tipo_atividade": tipo_atividade,
            "respostas": respostas,
            "status": "Respondida"
        }
        
        # VERIFICAÇÃO 4: Última verificação antes de salvar no arquivo
        RESPOSTAS_FILE = os.path.join(DATA_DIR, 'respostas_alunos.json')
        respostas_existentes = carregar_json(RESPOSTAS_FILE)
        
        # Verificação final para garantir que não há duplicata
        for resp in respostas_existentes:
            if (str(resp.get('ra_aluno')) == str(ra_aluno) and 
                str(resp.get('atividade_id')) == str(atividade.get('id'))):
                messagebox.showerror("🚨 ERRO DE SEGURANÇA", 
                                   f"CRÍTICO: Detectada tentativa de resposta duplicada!\n\n"
                                   f"• Aluno: {ra_aluno}\n"
                                   f"• Atividade ID: {atividade.get('id')}\n"
                                   f"• Resposta já existe desde: {resp.get('data_resposta', 'N/A')}\n\n"
                                   f"🛡️ O sistema bloqueou esta operação por segurança.")
                janela.destroy()
                return
        
        # Salvar nova resposta (garantido que não é duplicata)
        respostas_existentes.append(resposta_aluno)
        salvar_json(RESPOSTAS_FILE, respostas_existentes)
        
        messagebox.showinfo("✅ Sucesso", 
                           f"Suas respostas foram enviadas com sucesso!\n\n"
                           f"📝 Atividade: {atividade.get('nome')}\n"
                           f"⏰ Data/Hora: {resposta_aluno['data_resposta']}\n"
                           f"🔒 Status: Resposta registrada permanentemente\n\n"
                           f"💡 Lembre-se: Você não poderá responder esta atividade novamente.")
        janela.destroy()

    def _ver_historico_respostas_aluno(self, ra_aluno):
        """Mostra o histórico de respostas do aluno"""
        RESPOSTAS_FILE = os.path.join(DATA_DIR, 'respostas_alunos.json')
        respostas = carregar_json(RESPOSTAS_FILE)
        
        # Filtrar respostas do aluno
        respostas_aluno = [r for r in respostas if str(r.get('ra_aluno')) == str(ra_aluno)]
        
        if not respostas_aluno:
            messagebox.showinfo("Histórico de Respostas", "Você ainda não respondeu nenhuma atividade.")
            return
        
        # Criar janela de histórico
        janela_historico = customtkinter.CTkToplevel(self)
        janela_historico.title("📋 Meu Histórico de Respostas")
        janela_historico.geometry("900x600")
        janela_historico.transient(self)
        janela_historico.grab_set()
        
        # Cabeçalho
        header_frame = customtkinter.CTkFrame(janela_historico)
        header_frame.pack(fill='x', padx=20, pady=10)
        
        customtkinter.CTkLabel(header_frame, 
                              text="📋 Histórico de Atividades Respondidas", 
                              font=customtkinter.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        customtkinter.CTkLabel(header_frame, 
                              text=f"👤 Aluno: {self.usuario_logado.get('nome', '')} | 🆔 RA: {ra_aluno} | 📊 Total de respostas: {len(respostas_aluno)}", 
                              font=customtkinter.CTkFont(size=12)).pack(pady=5)
        
        # Tabela de histórico
        tree_historico = ttk.Treeview(janela_historico, 
                                     columns=('atividade', 'materia', 'tipo', 'data_resposta', 'status'), 
                                     show='headings')
        
        # Configurar cabeçalhos
        tree_historico.heading('atividade', text='Atividade')
        tree_historico.column('atividade', width=200)
        tree_historico.heading('materia', text='Matéria')
        tree_historico.column('materia', width=150)
        tree_historico.heading('tipo', text='Tipo')
        tree_historico.column('tipo', width=120, anchor='center')
        tree_historico.heading('data_resposta', text='Data/Hora Resposta')
        tree_historico.column('data_resposta', width=140, anchor='center')
        tree_historico.heading('status', text='Status')
        tree_historico.column('status', width=100, anchor='center')
        
        tree_historico.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Carregar dados das matérias para mostrar nomes
        materias = carregar_json(MATERIAS_FILE)
        mapa_materias = {m['id']: m['nome'] for m in materias}
        
        # Preencher tabela
        for resposta in sorted(respostas_aluno, key=lambda x: x.get('data_resposta', ''), reverse=True):
            materia_nome = mapa_materias.get(resposta.get('materia_id'), 'Matéria Desconhecida')
            
            valores = [
                resposta.get('atividade_nome', 'N/A'),
                materia_nome,
                resposta.get('tipo_atividade', 'N/A'),
                resposta.get('data_resposta', 'N/A'),
                '✅ ' + resposta.get('status', 'N/A')
            ]
            
            tree_historico.insert('', 'end', values=valores)
        
        # Frame de botões
        btn_frame = customtkinter.CTkFrame(janela_historico)
        btn_frame.pack(fill='x', padx=20, pady=10)
        
        customtkinter.CTkButton(btn_frame, text="👁 Ver Detalhes da Resposta", 
                              command=lambda: self._ver_detalhes_resposta_aluno(tree_historico, respostas_aluno),
                              fg_color="#6c757d", hover_color="#545b62").pack(side='left', padx=5)
        
        customtkinter.CTkButton(btn_frame, text="❌ Fechar", 
                              command=janela_historico.destroy).pack(side='right', padx=5)

    def _ver_detalhes_resposta_aluno(self, tree_historico, respostas_aluno):
        """Mostra detalhes de uma resposta específica"""
        selection = tree_historico.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Por favor, selecione uma resposta para ver os detalhes.")
            return
        
        item = tree_historico.item(selection[0])
        valores = item['values']
        nome_atividade = valores[0]
        
        # Encontrar a resposta completa
        resposta_completa = next((r for r in respostas_aluno if r.get('atividade_nome') == nome_atividade), None)
        
        if not resposta_completa:
            messagebox.showerror("Erro", "Detalhes da resposta não encontrados.")
            return
        
        # Criar janela de detalhes
        janela_detalhes = customtkinter.CTkToplevel(self)
        janela_detalhes.title(f"🔍 Detalhes da Resposta: {nome_atividade}")
        janela_detalhes.geometry("700x500")
        janela_detalhes.transient(self)
        janela_detalhes.grab_set()
        
        # Frame de informações
        info_frame = customtkinter.CTkFrame(janela_detalhes)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        customtkinter.CTkLabel(info_frame, text=f"📝 {nome_atividade}", 
                              font=customtkinter.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        info_text = f"📚 Matéria: {valores[1]} | 🎯 Tipo: {valores[2]} | ⏰ Respondida em: {valores[3]}"
        customtkinter.CTkLabel(info_frame, text=info_text, 
                              font=customtkinter.CTkFont(size=11)).pack(pady=2)
        
        # Frame de respostas
        customtkinter.CTkLabel(janela_detalhes, text="📋 Suas Respostas:", 
                              font=customtkinter.CTkFont(size=14, weight="bold")).pack(anchor='w', padx=20, pady=(20,5))
        
        respostas_scroll = customtkinter.CTkScrollableFrame(janela_detalhes, height=300)
        respostas_scroll.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Mostrar respostas
        respostas_data = resposta_completa.get('respostas', [])
        
        for i, resposta in enumerate(respostas_data):
            resp_frame = customtkinter.CTkFrame(respostas_scroll)
            resp_frame.pack(fill='x', padx=5, pady=5)
            
            customtkinter.CTkLabel(resp_frame, text=f"Pergunta {i+1}:", 
                                  font=customtkinter.CTkFont(weight="bold")).pack(anchor='w', padx=10, pady=5)
            
            resposta_text = customtkinter.CTkTextbox(resp_frame, height=60)
            resposta_text.pack(fill='x', padx=10, pady=(0,10))
            resposta_text.insert("1.0", str(resposta))
            resposta_text.configure(state="disabled")
        
        # Aviso
        aviso_frame = customtkinter.CTkFrame(janela_detalhes)
        aviso_frame.pack(fill='x', padx=20, pady=10)
        
        customtkinter.CTkLabel(aviso_frame, 
                              text="🔒 IMPORTANTE: Estas respostas são definitivas e não podem ser alteradas.", 
                              font=customtkinter.CTkFont(size=11, weight="bold"),
                              text_color="orange").pack(pady=5)
        
        # Botão fechar
        customtkinter.CTkButton(janela_detalhes, text="❌ Fechar", 
                              command=janela_detalhes.destroy).pack(pady=10)

    def _criar_aba_seguranca(self, parent_tab):
        """Cria aba de segurança (alterar senha)"""
        customtkinter.CTkLabel(parent_tab, text="Configurações de Segurança", 
                              font=customtkinter.CTkFont(size=16, weight="bold")).pack(pady=(20, 10))
        
        # Frame para alterar senha
        senha_frame = customtkinter.CTkFrame(parent_tab)
        senha_frame.pack(fill='x', padx=20, pady=10)
        
        customtkinter.CTkLabel(senha_frame, text="Alterar Senha", 
                              font=customtkinter.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        customtkinter.CTkButton(senha_frame, text="Alterar Minha Senha", 
                              command=self._alterar_propria_senha,
                              height=40).pack(pady=10)
        
        # Informações de segurança
        info_frame = customtkinter.CTkFrame(parent_tab)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        customtkinter.CTkLabel(info_frame, text="Dicas de Segurança", 
                              font=customtkinter.CTkFont(size=14, weight="bold")).pack(pady=(10,5))
        
        dicas_text = """• Use uma senha forte com pelo menos 6 caracteres
• Inclua letras, números e símbolos especiais
• Não compartilhe sua senha com outras pessoas
• Altere sua senha regularmente
• Faça logout quando terminar de usar o sistema"""
        
        customtkinter.CTkLabel(info_frame, text=dicas_text, 
                              justify='left').pack(pady=10, padx=20)

    # ================= ADMIN =================
    def _tab_admin(self, parent_tab):
        # Adiciona um título para garantir que a aba Admin aparece
        customtkinter.CTkLabel(parent_tab, text="Painel Administrativo", font=customtkinter.CTkFont(size=18, weight="bold")).pack(pady=(10, 5), padx=10, anchor='w')

        tabs_inner = customtkinter.CTkTabview(parent_tab)
        tabs_inner.pack(expand=True, fill='both')

        # Ordem das abas alterada conforme solicitado
        self._admin_alunos_tab(tabs_inner.add('Alunos'))
        self._admin_usuarios_tab(tabs_inner.add('Usuários'))
        self._admin_turmas_tab(tabs_inner.add('Turmas'))
        self._admin_materias_tab(tabs_inner.add('Matérias'))
        self._admin_pedidos_tab(tabs_inner.add('Pedidos'))
        
        self._criar_controles_inferiores(parent_tab)

    # --------- USUÁRIOS ---------
    def _admin_usuarios_tab(self, parent_tab):
        # --- Frame de Filtros ---
        frm_filtros = customtkinter.CTkFrame(parent_tab)
        frm_filtros.pack(fill='x', padx=10, pady=10)

        customtkinter.CTkLabel(frm_filtros, text="Pesquisar (Usuário ou Nome):").pack(side='left', padx=5)
        e_pesquisa = customtkinter.CTkEntry(frm_filtros)
        e_pesquisa.pack(side='left', fill='x', expand=True, padx=5)

        customtkinter.CTkLabel(frm_filtros, text="Tipo:").pack(side='left', padx=(10, 2))
        e_tipo_filtro = customtkinter.CTkComboBox(frm_filtros, values=["Todos", "admin", "professor"], width=120)
        e_tipo_filtro.pack(side='left', padx=(0, 5))
        e_tipo_filtro.set("Todos")

        def aplicar_filtros():
            refresh(e_pesquisa.get().lower().strip(), e_tipo_filtro.get())

        customtkinter.CTkButton(frm_filtros, text="Pesquisar", command=aplicar_filtros).pack(side='left', padx=5)
        
        def limpar_filtros():
            e_pesquisa.delete(0, 'end')
            e_tipo_filtro.set("Todos")
            refresh()
        customtkinter.CTkButton(frm_filtros, text="Limpar", command=limpar_filtros).pack(side='left', padx=5)

        tree = ttk.Treeview(parent_tab, columns=('usuario', 'tipo', 'nome', 'data_nascimento'), show='headings', height=8)
        tree.heading('usuario', text='Usuário')
        tree.column('usuario', width=120)
        tree.heading('tipo', text='Tipo')
        tree.column('tipo', width=80)
        tree.heading('nome', text='Nome')
        tree.column('nome', width=250)
        tree.heading('data_nascimento', text='Data de Nascimento')
        tree.column('data_nascimento', width=150)
        tree.pack(fill='both', expand=True, padx=10, pady=10)

        def refresh(termo_pesquisa=None, tipo_filtro="Todos"):
            for i in tree.get_children():
                tree.delete(i)
            
            usuarios = carregar_todos_usuarios()
            # Filtrar apenas admin e professor (excluir alunos)
            usuarios_filtrados = [u for u in usuarios if u.get('tipo') in ['admin', 'professor']]

            if termo_pesquisa:
                usuarios_filtrados = [
                    u for u in usuarios_filtrados if
                    termo_pesquisa in u['usuario'].lower() or
                    termo_pesquisa in u.get('nome', '').lower()
                ]
            
            if tipo_filtro != "Todos":
                usuarios_filtrados = [u for u in usuarios_filtrados if u['tipo'] == tipo_filtro]

            for u in usuarios_filtrados:
                tree.insert('', 'end', values=(u['usuario'], u['tipo'], u.get('nome', ''), u.get('data_nascimento', 'N/A')))
        refresh()

        frm = customtkinter.CTkFrame(parent_tab)
        frm.pack(fill='x', pady=8, padx=10)
        customtkinter.CTkButton(frm, text='Adicionar', command=lambda: self._usuario_form(refresh)).pack(side='left', padx=5)
        customtkinter.CTkButton(frm, text='Alterar', command=lambda: self._usuario_form(refresh, edit=True, tree=tree)).pack(side='left', padx=5)
        customtkinter.CTkButton(frm, text='Remover', command=lambda: self._remover_usuario(tree, refresh)).pack(side='left', padx=5)
        
        # Botão de Atualizar com ícone e destaque visual
        customtkinter.CTkButton(
            frm, 
            text='🔄 Atualizar', 
            command=lambda: refresh(),
            fg_color="#17a2b8",
            hover_color="#138496",
            font=customtkinter.CTkFont(weight="bold")
        ).pack(side='right', padx=5)
        
    def _usuario_form(self, refresh, edit=False, tree=None):
        top = customtkinter.CTkToplevel(self)
        top.title('Adicionar Usuário' if not edit else 'Alterar Usuário')
        top.geometry('500x600')
        top.resizable(False, False)
        todos_usuarios = carregar_todos_usuarios()
        u = None
        usuario_original = None
        tipo_original = None

        if edit and tree:
            sel = tree.selection()
            if not sel:
                messagebox.showwarning('Erro', 'Selecione um usuário.')
                top.destroy()
                return
            values = tree.item(sel[0])['values']
            usuario_original = values[0]  # Primeira coluna é o nome de usuário
            tipo_original = values[1]     # Segunda coluna é o tipo
            

            
            # Buscar usuário no arquivo específico do tipo (apenas admin e professor)
            if tipo_original == 'professor':
                professores = carregar_json(PROFESSORES_FILE)
                u = next((x for x in professores if x.get('usuario') == usuario_original), None)
            elif tipo_original == 'admin':
                admins = carregar_json(ADMIN_FILE)
                u = next((x for x in admins if x.get('usuario') == usuario_original), None)
            else:
                messagebox.showerror('Erro', f'Tipo de usuário "{tipo_original}" não é permitido nesta seção.')
                top.destroy()
                return
            
            if not u:
                messagebox.showerror('Erro', f'Usuário "{usuario_original}" do tipo "{tipo_original}" não encontrado.')
                top.destroy()
                return
            
            # Adicionar tipo ao objeto para garantir consistência
            u['tipo'] = tipo_original


        # Frame principal com scroll
        main_frame = customtkinter.CTkScrollableFrame(top)
        main_frame.pack(fill='both', expand=True, padx=20, pady=(20, 10))

        # Título do formulário
        title_label = customtkinter.CTkLabel(
            main_frame, 
            text='📝 Dados do Usuário' if not edit else '✏️ Editar Usuário',
            font=customtkinter.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # Campo Usuário
        customtkinter.CTkLabel(main_frame, text='Usuário:*', font=customtkinter.CTkFont(size=14, weight="bold")).pack(anchor='w', pady=(10, 5), padx=20)
        e_user = customtkinter.CTkEntry(main_frame, height=40, font=customtkinter.CTkFont(size=13))
        e_user.pack(fill='x', padx=20, pady=(0, 15))
        e_user.insert(0, u['usuario'] if u else '')
        if edit:
            e_user.configure(state='disabled')  # Desabilita a edição do nome de usuário

        # Campo Senha
        senha_label_text = 'Nova Senha:' if edit else 'Senha:*'
        customtkinter.CTkLabel(main_frame, text=senha_label_text, font=customtkinter.CTkFont(size=14, weight="bold")).pack(anchor='w', pady=(10, 5), padx=20)
        
        # Label informativa para edição
        if edit:
            customtkinter.CTkLabel(main_frame, text='💡 Deixe vazio para manter a senha atual', 
                                  font=customtkinter.CTkFont(size=11), 
                                  text_color="gray").pack(anchor='w', padx=20, pady=(0, 5))
        
        pass_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        pass_frame.pack(fill='x', padx=20, pady=(0, 15))
        e_pass = customtkinter.CTkEntry(pass_frame, show='*', height=40, font=customtkinter.CTkFont(size=13))
        e_pass.pack(side='left', fill='x', expand=True)
        # Se está editando, deixar campo vazio para permitir nova senha (não mostrar hash)
        if edit:
            e_pass.configure(placeholder_text="Digite nova senha ou deixe vazio para manter")
        else:
            e_pass.insert(0, u['senha'] if u else '')
        
        show_pass_btn = customtkinter.CTkButton(pass_frame, text="👁️", width=50, height=40, font=customtkinter.CTkFont(size=16))
        show_pass_btn.pack(side='left', padx=(10,0))

        def toggle_user_pass():
            if e_pass.cget('show') == '*':
                e_pass.configure(show='')
                show_pass_btn.configure(text="🔒")
            else:
                e_pass.configure(show='*')
                show_pass_btn.configure(text="👁️")
        show_pass_btn.configure(command=toggle_user_pass)

        # Campo Tipo
        customtkinter.CTkLabel(main_frame, text='Tipo de Usuário:*', font=customtkinter.CTkFont(size=14, weight="bold")).pack(anchor='w', pady=(10, 5), padx=20)
        e_tipo = customtkinter.CTkComboBox(main_frame, values=['admin', 'professor'], height=40, font=customtkinter.CTkFont(size=13))
        e_tipo.pack(fill='x', padx=20, pady=(0, 15))
        e_tipo.set(u['tipo'] if u else 'professor')
        
        # Campo Nome
        customtkinter.CTkLabel(main_frame, text='Nome Completo:*', font=customtkinter.CTkFont(size=14, weight="bold")).pack(anchor='w', pady=(10, 5), padx=20)
        e_nome = customtkinter.CTkEntry(main_frame, height=40, font=customtkinter.CTkFont(size=13))
        e_nome.pack(fill='x', padx=20, pady=(0, 15))
        e_nome.insert(0, u.get('nome', '') if u else '')

        # Campo Data de Nascimento
        customtkinter.CTkLabel(main_frame, text='Data de Nascimento (DD/MM/AAAA):*', font=customtkinter.CTkFont(size=14, weight="bold")).pack(anchor='w', pady=(10, 5), padx=20)
        e_data_nascimento = customtkinter.CTkEntry(main_frame, height=40, font=customtkinter.CTkFont(size=13), placeholder_text="Ex: 15/03/1990")
        e_data_nascimento.pack(fill='x', padx=20, pady=(0, 20))
        if edit:
            e_data_nascimento.insert(0, u.get('data_nascimento', ''))

        def salvar():
            novo_usuario = e_user.get().strip()
            nova_senha = e_pass.get().strip()
            novo_tipo = e_tipo.get()
            novo_nome = e_nome.get().strip()
            nova_data_nascimento = e_data_nascimento.get().strip()

            if not novo_usuario:
                messagebox.showerror('Erro', 'O campo Usuário é obrigatório.', parent=top)
                return

            if not novo_nome:
                messagebox.showerror('Erro', 'O campo Nome é obrigatório.', parent=top)
                return

            if not nova_data_nascimento:
                messagebox.showerror('Erro', 'O campo Data de Nascimento é obrigatório.', parent=top)
                return

            # Validar formato da data
            valida_data, msg_data = validar_data(nova_data_nascimento)
            if not valida_data:
                messagebox.showerror('Erro', msg_data, parent=top)
                return

            # Validar idade mínima de 18 anos
            valida_idade, msg_idade = validar_idade_minima(nova_data_nascimento, 18)
            if not valida_idade:
                messagebox.showerror('Erro', msg_idade, parent=top)
                return

            # Se a senha for alterada, ela deve ser validada e criptografada
            if nova_senha:
                valida, msg = self._validar_senha(nova_senha)
                if not valida:
                    messagebox.showerror('Senha Inválida', msg, parent=top)
                    return
                senha_para_salvar = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            elif not edit: # Se for um novo usuário, a senha é obrigatória
                messagebox.showerror('Erro', 'O campo Senha é obrigatório para novos usuários.', parent=top)
                return
            else: # Editando sem alterar a senha
                senha_para_salvar = None

            # Verificar se o usuário já existe em qualquer arquivo
            todos_usuarios_atualizado = carregar_todos_usuarios()
            if not edit and any(x['usuario'] == novo_usuario for x in todos_usuarios_atualizado):
                messagebox.showerror('Erro', f'O usuário "{novo_usuario}" já existe.', parent=top)
                return

            # Criar/atualizar usuário
            usuario_data = {
                'usuario': novo_usuario, 
                'tipo': novo_tipo, 
                'nome': novo_nome,
                'data_nascimento': nova_data_nascimento
            }

            if edit and u:
                # Manter a senha original se não foi alterada
                if senha_para_salvar:
                    usuario_data['senha'] = senha_para_salvar
                else:
                    usuario_data['senha'] = u['senha']
                
                # Se o tipo mudou, remover do arquivo antigo e salvar no novo
                if u['tipo'] != novo_tipo:
                    # Remover do arquivo antigo
                    remover_usuario_por_tipo(usuario_original, u['tipo'])
                
                # Salvar no arquivo correto do novo tipo
                salvar_usuario_por_tipo(usuario_data)
                messagebox.showinfo('Sucesso', f'Usuário "{novo_nome}" foi atualizado com sucesso!')
            else:
                # Novo usuário
                usuario_data['senha'] = senha_para_salvar
                salvar_usuario_por_tipo(usuario_data)
                messagebox.showinfo('Sucesso', f'Usuário "{novo_nome}" foi criado com sucesso!')
            
            # atualizar mapa local de professores
            self.mapa_professores = gerar_mapa_professores()
            refresh()
            top.destroy()
    
        # Frame de botões fixo na parte inferior
        botoes_frame = customtkinter.CTkFrame(top, fg_color="transparent")
        botoes_frame.pack(fill='x', padx=20, pady=(0, 20))

        # Separador visual
        separator = customtkinter.CTkFrame(botoes_frame, height=2, fg_color="gray40")
        separator.pack(fill='x', pady=(0, 15))

        # Container para os botões
        btn_container = customtkinter.CTkFrame(botoes_frame, fg_color="transparent")
        btn_container.pack(fill='x')

        # Botão Cancelar
        btn_cancelar = customtkinter.CTkButton(
            btn_container, 
            text='✖ Cancelar', 
            command=top.destroy, 
            height=45, 
            width=200,
            font=customtkinter.CTkFont(size=14, weight="bold"),
            fg_color="#dc3545",
            hover_color="#c82333",
            corner_radius=8
        )
        btn_cancelar.pack(side='left', expand=True, padx=(0, 10))

        # Botão Salvar
        btn_salvar = customtkinter.CTkButton(
            btn_container, 
            text='✓ Salvar', 
            command=salvar, 
            height=45, 
            width=200,
            font=customtkinter.CTkFont(size=14, weight="bold"),
            fg_color="#28a745",
            hover_color="#218838",
            corner_radius=8
        )
        btn_salvar.pack(side='right', expand=True, padx=(10, 0))

    def _remover_usuario(self, tree, refresh):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning('Erro', 'Selecione um usuário.')
            return
        
        # Confirmar exclusão
        values = tree.item(sel[0])['values']
        usuario_nome = values[0]  # Nome de usuário na primeira coluna
        tipo_usuario = values[1]  # Tipo de usuário na segunda coluna
        
        if not messagebox.askyesno('Confirmar', f'Confirma a exclusão do usuário "{usuario_nome}" ({tipo_usuario})?'):
            return
            
        # Remover do arquivo correspondente ao tipo
        remover_usuario_por_tipo(usuario_nome, tipo_usuario)
        
        # atualizar mapa local de professores
        self.mapa_professores = gerar_mapa_professores()
        refresh()

    # --------- TURMAS ---------
    def _admin_turmas_tab(self, parent_tab):
        # Frame principal que divide a aba em duas seções
        main_frame = customtkinter.CTkFrame(parent_tab, fg_color="transparent")
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # --- Lado Esquerdo: Lista de Turmas ---
        left_frame = customtkinter.CTkFrame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        customtkinter.CTkLabel(left_frame, text="Turmas", font=customtkinter.CTkFont(weight="bold")).grid(row=0, column=0, pady=5, padx=10, sticky="w")
        
        tree_turmas = ttk.Treeview(left_frame, columns=('id', 'serie', 'turma', 'alunos', 'materias'), show='headings', height=6)
        tree_turmas.heading('id', text='ID')
        tree_turmas.column('id', width=40)
        tree_turmas.heading('serie', text='Série')
        tree_turmas.column('serie', width=120)
        tree_turmas.heading('turma', text='Turma')
        tree_turmas.column('turma', width=100)
        tree_turmas.heading('alunos', text='Alunos (Qtd/Limite)')
        tree_turmas.column('alunos', width=120, anchor='center')
        tree_turmas.heading('materias', text='Matérias (Qtd)')
        tree_turmas.column('materias', width=100, anchor='center')
        tree_turmas.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))

        # --- Lado Direito: Gerenciador de Alunos ---
        right_frame = customtkinter.CTkFrame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_columnconfigure(1, weight=1)
        right_frame.grid_columnconfigure(2, weight=1)
        right_frame.grid_rowconfigure(2, weight=1)

        lbl_turma_selecionada = customtkinter.CTkLabel(right_frame, text="Selecione uma turma à esquerda", font=customtkinter.CTkFont(weight="bold"))
        lbl_turma_selecionada.grid(row=0, column=0, columnspan=3, pady=5, padx=10, sticky="w")

        customtkinter.CTkLabel(right_frame, text="Alunos na Turma").grid(row=1, column=0, padx=10, sticky="w")
        tree_alunos_na_turma = ttk.Treeview(right_frame, columns=('ra', 'nome'), show='headings', selectmode='extended')
        tree_alunos_na_turma.heading('ra', text='RA')
        tree_alunos_na_turma.column('ra', width=80)
        tree_alunos_na_turma.heading('nome', text='Nome')
        tree_alunos_na_turma.grid(row=2, column=0, sticky='nsew', padx=(10,5))

        # Botões de Ação (Adicionar/Remover)
        action_frame = customtkinter.CTkFrame(right_frame, fg_color="transparent")
        action_frame.grid(row=2, column=1, sticky="ew", padx=5)
        # Botões renomeados e ordem trocada para clareza
        btn_adicionar_aluno = customtkinter.CTkButton(action_frame, text="<", width=40)
        btn_adicionar_aluno.pack(pady=10)
        btn_remover_aluno = customtkinter.CTkButton(action_frame, text=">", width=40)
        btn_remover_aluno.pack(pady=10)

        customtkinter.CTkLabel(right_frame, text="Alunos Disponíveis").grid(row=1, column=2, padx=10, sticky="w")
        tree_alunos_disponiveis = ttk.Treeview(right_frame, columns=('ra', 'nome'), show='headings', selectmode='extended')
        tree_alunos_disponiveis.heading('ra', text='RA')
        tree_alunos_disponiveis.column('ra', width=80)
        tree_alunos_disponiveis.heading('nome', text='Nome')
        tree_alunos_disponiveis.grid(row=2, column=2, sticky='nsew', padx=(5,10))

        def refresh_turmas():
            materias = carregar_json(MATERIAS_FILE)
            for i in tree_turmas.get_children():
                tree_turmas.delete(i)
            for t in carregar_json(TURMAS_FILE):
                num_alunos = len(t.get('alunos', []))
                limite_alunos = t.get('limite_alunos', 'N/A')
                info_alunos = f"{num_alunos}/{limite_alunos}"
                
                qtd_materias = len([m for m in materias if m.get('turma_id') == t.get('id')])

                tree_turmas.insert('', 'end', iid=t['id'], values=(t['id'], t.get('serie', ''), t.get('turma', ''), info_alunos, qtd_materias))

        def on_turma_select(event=None):
            sel = tree_turmas.selection()
            if not sel:
                lbl_turma_selecionada.configure(text="Selecione uma turma à esquerda")
                btn_adicionar_aluno.configure(state="disabled")
                btn_remover_aluno.configure(state="disabled")
                # Limpar listas se nada estiver selecionado
                for i in tree_alunos_na_turma.get_children(): tree_alunos_na_turma.delete(i)
                for i in tree_alunos_disponiveis.get_children(): tree_alunos_disponiveis.delete(i)
                return
            
            turma_id = int(sel[0])
            turmas = carregar_json(TURMAS_FILE)
            turma_selecionada = next((t for t in turmas if t['id'] == turma_id), None)
            
            if not turma_selecionada: return

            lbl_turma_selecionada.configure(text=f"Gerenciando: {turma_selecionada.get('serie')} - {turma_selecionada.get('turma')}")
            btn_adicionar_aluno.configure(state="normal")
            btn_remover_aluno.configure(state="normal")

            # Limpar listas de alunos
            for i in tree_alunos_na_turma.get_children(): tree_alunos_na_turma.delete(i)
            for i in tree_alunos_disponiveis.get_children(): tree_alunos_disponiveis.delete(i)

            # Carregar todos os alunos e turmas
            todos_usuarios = carregar_json(ALUNOS_FILE)  # Agora apenas alunos
            alunos = {u['ra']: u for u in todos_usuarios}  # Todos já são alunos
            
            ras_em_outras_turmas = set()
            for t in turmas:
                if t['id'] != turma_id:
                    ras_em_outras_turmas.update(t.get('alunos', []))

            # Popular lista de alunos na turma
            for ra_aluno in turma_selecionada.get('alunos', []):
                if ra_aluno in alunos:
                    tree_alunos_na_turma.insert('', 'end', iid=ra_aluno, values=(ra_aluno, alunos[ra_aluno].get('nome', '')))
            
            # Popular lista de alunos disponíveis
            for ra, aluno_data in alunos.items():
                if ra not in turma_selecionada.get('alunos', []) and ra not in ras_em_outras_turmas:
                    tree_alunos_disponiveis.insert('', 'end', iid=ra, values=(ra, aluno_data.get('nome', '')))

        def mover_aluno(adicionar=True):
            sel_turma = tree_turmas.selection()
            if not sel_turma:
                messagebox.showwarning("Aviso", "Nenhuma turma selecionada.")
                return
            turma_id = int(sel_turma[0])

            if adicionar:
                sel_alunos = tree_alunos_disponiveis.selection()
                if not sel_alunos:
                    messagebox.showwarning("Aviso", "Selecione um ou mais alunos disponíveis para adicionar.")
                    return
            else: # Remover
                sel_alunos = tree_alunos_na_turma.selection()
                if not sel_alunos:
                    messagebox.showwarning("Aviso", "Selecione um ou mais alunos da turma para remover.")
                    return

            turmas = carregar_json(TURMAS_FILE)
            turma_alvo = next((t for t in turmas if t['id'] == turma_id), None)
            
            if turma_alvo:
                alunos_na_turma = turma_alvo.setdefault('alunos', [])
                if adicionar:
                    try:
                        limite_alunos = int(turma_alvo.get('limite_alunos', 0))
                        if len(alunos_na_turma) + len(sel_alunos) > limite_alunos:
                            return
                    except (ValueError, TypeError):
                        messagebox.showerror("Erro de Configuração", "O limite de alunos para esta turma não é um número válido.")
                        return
                    
                    for ra_aluno in sel_alunos:
                        if ra_aluno not in alunos_na_turma:
                            alunos_na_turma.append(ra_aluno)

                elif not adicionar:
                    for ra_aluno in sel_alunos:
                        if ra_aluno in alunos_na_turma:
                            alunos_na_turma.remove(ra_aluno)
                
                salvar_json(TURMAS_FILE, turmas)
                refresh_turmas() # Atualiza a lista de turmas para mostrar a nova contagem
                on_turma_select() # Refresh as listas de alunos

        # CORREÇÃO: Lógica dos botões invertida para o correto
        btn_adicionar_aluno.configure(command=lambda: mover_aluno(adicionar=True))  # Botão > (adicionar)
        btn_remover_aluno.configure(command=lambda: mover_aluno(adicionar=False)) # Botão < (remover)

        tree_turmas.bind('<<TreeviewSelect>>', on_turma_select)
        
        # Botões de CRUD para Turmas
        frm_botoes_turma = customtkinter.CTkFrame(left_frame)
        frm_botoes_turma.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        # Função de callback para atualizar a lista de turmas e a seleção
        def refresh_e_seleciona():
            refresh_turmas()
            on_turma_select()

        customtkinter.CTkButton(frm_botoes_turma, text='Criar', command=lambda: self._turma_form(refresh_e_seleciona)).pack(side='left', padx=5)
        customtkinter.CTkButton(frm_botoes_turma, text='Alterar', command=lambda: self._turma_form(refresh_e_seleciona, edit=True, tree=tree_turmas)).pack(side='left', padx=5)
        customtkinter.CTkButton(frm_botoes_turma, text='Remover', command=lambda: self._remover_turma(tree_turmas, refresh_e_seleciona)).pack(side='left', padx=5)
        
        # Botão de Atualizar com ícone e destaque visual
        customtkinter.CTkButton(
            frm_botoes_turma, 
            text='🔄 Atualizar', 
            command=lambda: refresh_e_seleciona(),
            fg_color="#17a2b8",
            hover_color="#138496",
            font=customtkinter.CTkFont(weight="bold")
        ).pack(side='right', padx=5)

        # Carrega os dados iniciais
        refresh_turmas()
        on_turma_select()

    def _turma_form(self, refresh, edit=False, tree=None):
        top = customtkinter.CTkToplevel(self)
        top.title('Turma')
        top.geometry('400x450')
        top.resizable(False, False)

        data = carregar_json(TURMAS_FILE)
        t = None
        if edit and tree:
            sel = tree.selection()
            if not sel:
                messagebox.showwarning('Erro', 'Selecione uma turma.')
                top.destroy()
                return
            values = tree.item(sel[0])['values']
            t = next((x for x in data if x['id'] == values[0]), None)

        customtkinter.CTkLabel(top, text='Série:').pack(anchor='w', pady=(10, 0), padx=20)
        e_serie = customtkinter.CTkComboBox(top, values=self.series_disponiveis)
        e_serie.pack(fill='x', padx=20, pady=5)
        e_serie.set(t.get('serie', '') if t else '')

        customtkinter.CTkLabel(top, text='Turma:').pack(anchor='w', pady=(5, 0), padx=20)
        e_turma = customtkinter.CTkComboBox(top, values=self.turmas_disponiveis)
        e_turma.pack(fill='x', padx=20, pady=5)
        e_turma.set(t.get('turma', '') if t else '')

        customtkinter.CTkLabel(top, text='Tempo de curso:').pack(anchor='w', pady=(5, 0), padx=20)
        e_tempo = customtkinter.CTkEntry(top)
        e_tempo.pack(fill='x', padx=20, pady=5)
        e_tempo.insert(0, t.get('tempo_curso', '') if t else '')

        customtkinter.CTkLabel(top, text='Limite de alunos:').pack(anchor='w', pady=(5, 0), padx=20)
        e_limite = customtkinter.CTkEntry(top)
        e_limite.pack(fill='x', padx=20, pady=5)
        e_limite.insert(0, t.get('limite_alunos', '') if t else '')

        customtkinter.CTkLabel(top, text='Professor responsável:').pack(anchor='w', pady=(5, 0), padx=20)
        professores = carregar_json(PROFESSORES_FILE)
        professores_nomes = [u.get('nome', u['usuario']) for u in professores]
        e_prof = customtkinter.CTkComboBox(top, values=professores_nomes)
        e_prof.pack(fill='x', padx=20, pady=(0, 5))
        if t and t.get('professor') in professores_nomes:
            e_prof.set(t.get('professor'))
        else:
            e_prof.set('')

        def salvar():
            serie = e_serie.get()
            turma_letra = e_turma.get()
            tempo_curso = e_tempo.get()
            limite_alunos = e_limite.get()
            professor_responsavel = e_prof.get()

            if not serie or not turma_letra or not tempo_curso or not limite_alunos or not professor_responsavel:
                messagebox.showerror('Erro', 'Todos os campos são obrigatórios.', parent=top)
                return

            if edit and t:
                t['serie'] = serie
                t['turma'] = turma_letra
                t['tempo_curso'] = tempo_curso
                t['limite_alunos'] = limite_alunos
                t['professor'] = professor_responsavel
            else:
                novo_id = max([x.get('id', 0) for x in data], default=0) + 1
                data.append({'id': novo_id, 'serie': serie, 'turma': turma_letra, 'tempo_curso': tempo_curso, 'limite_alunos': limite_alunos, 'professor': professor_responsavel, 'alunos': []})
            
            salvar_json(TURMAS_FILE, data)
            refresh()
            top.destroy()

        customtkinter.CTkButton(top, text='Salvar', command=salvar).pack(pady=20)

    def _remover_turma(self, tree, refresh):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning('Erro', 'Selecione uma turma.')
            return
        # confirmar exclusão
        if not messagebox.askyesno('Confirmar', 'Confirma a exclusão da turma selecionada?'):
            return

        turmas = carregar_json(TURMAS_FILE)
        turma_id = int(tree.item(sel[0])['values'][0]) # Garantir que o ID é int
        turmas = [x for x in turmas if x['id'] != turma_id]
        salvar_json(TURMAS_FILE, turmas)
        refresh()

    # --------- ALUNOS (atribuição) ---------
    def _admin_alunos_tab(self, parent_tab):
        # --- Frame de Filtros ---
        frm_filtros = customtkinter.CTkFrame(parent_tab)
        frm_filtros.pack(fill='x', padx=10, pady=10)

        customtkinter.CTkLabel(frm_filtros, text="Pesquisar (Nome/Usuário):").pack(side='left', padx=5)
        e_pesquisa = customtkinter.CTkEntry(frm_filtros)
        e_pesquisa.pack(side='left', fill='x', expand=True, padx=5)

        customtkinter.CTkLabel(frm_filtros, text="Série:").pack(side='left', padx=(10, 2))
        e_serie_filtro = customtkinter.CTkComboBox(frm_filtros, values=[""] + self.series_disponiveis, width=120)
        e_serie_filtro.pack(side='left', padx=(0, 5))
        e_serie_filtro.set("")

        customtkinter.CTkLabel(frm_filtros, text="Turma:").pack(side='left', padx=(10, 2))
        e_turma_filtro = customtkinter.CTkComboBox(frm_filtros, values=[""] + self.turmas_disponiveis, width=90)
        e_turma_filtro.pack(side='left', padx=(0, 5))
        e_turma_filtro.set("")

        def aplicar_filtros():
            refresh_alunos_list(
                termo_pesquisa=e_pesquisa.get().lower().strip(),
                serie_filtro=e_serie_filtro.get(),
                turma_filtro=e_turma_filtro.get()
            )

        def limpar_filtros():
            e_pesquisa.delete(0, 'end')
            e_serie_filtro.set("")
            e_turma_filtro.set("")
            refresh_alunos_list()

        customtkinter.CTkButton(frm_filtros, text="Pesquisar", command=aplicar_filtros).pack(side='left', padx=5)
        customtkinter.CTkButton(frm_filtros, text="Limpar", command=limpar_filtros).pack(side='left', padx=5)

        tree = ttk.Treeview(parent_tab, columns=('nome', 'ra', 'usuario', 'data_nascimento', 'turma'), show='headings', height=8)
        tree.heading('nome', text='Nome do Aluno')
        tree.column('nome', width=200)
        tree.heading('ra', text='RA')
        tree.column('ra', width=100)
        tree.heading('usuario', text='Usuário (Login)')
        tree.column('usuario', width=120)
        tree.heading('data_nascimento', text='Data de Nascimento')
        tree.column('data_nascimento', width=130)
        tree.heading('turma', text='Turma')
        tree.column('turma', width=150)
        tree.pack(fill='both', expand=True, padx=10, pady=10)

        def refresh_alunos_list(termo_pesquisa=None, serie_filtro=None, turma_filtro=None):
            for i in tree.get_children():
                tree.delete(i)
            
            usuarios = carregar_json(ALUNOS_FILE)  # Agora busca diretamente no arquivo de alunos
            turmas = carregar_json(TURMAS_FILE)
            
            # Mapeia cada aluno (RA) à sua turma para consulta rápida
            mapa_aluno_turma = {}
            for t in turmas:
                nome_turma = f"{t.get('serie', '')} - {t.get('turma', '')}"
                for aluno_ra in t.get('alunos', []):
                    # Garantir que o RA seja tratado como string
                    ra_string = str(aluno_ra).strip()
                    mapa_aluno_turma[ra_string] = nome_turma

            # Filtra apenas os usuários que são alunos (todos do arquivo já são alunos)
            alunos = usuarios

            # Aplica filtro de pesquisa por texto
            if termo_pesquisa:
                alunos = [
                    u for u in alunos if
                    termo_pesquisa in u.get('nome', '').lower() or
                    termo_pesquisa in u.get('usuario', '').lower() or
                    termo_pesquisa in str(u.get('ra', '')).lower()
                ]

            # Aplica filtros de série e turma
            if serie_filtro or turma_filtro:
                alunos_filtrados_turma = []
                for aluno in alunos:
                    ra_aluno = aluno.get('ra')
                    turma_aluno = mapa_aluno_turma.get(ra_aluno, "Sem turma")
                    
                    match_serie = not serie_filtro or serie_filtro in turma_aluno
                    match_turma = not turma_filtro or turma_filtro in turma_aluno
                    
                    if match_serie and match_turma:
                        alunos_filtrados_turma.append(aluno)
                alunos = alunos_filtrados_turma

            for aluno in sorted(alunos, key=lambda x: x.get('nome', '')):
                nome = aluno.get('nome', '')
                ra = str(aluno.get('ra', '')).strip()  # Garantir que seja string
                usuario = aluno.get('usuario', '')
                data_nascimento = aluno.get('data_nascimento', 'N/A')
                turma_aluno = mapa_aluno_turma.get(ra, "Sem turma")
                
                # Debug para verificar os dados sendo inseridos
                tree.insert('', 'end', values=(nome, ra, usuario, data_nascimento, turma_aluno))
        
        refresh_alunos_list()

        frm_botoes_aluno = customtkinter.CTkFrame(parent_tab)
        frm_botoes_aluno.pack(fill='x', padx=10, pady=5)
        customtkinter.CTkButton(frm_botoes_aluno, text='Criar Aluno', command=lambda: self._aluno_form(refresh_callback=refresh_alunos_list)).pack(side='left', padx=5)
        customtkinter.CTkButton(frm_botoes_aluno, text='Alterar Aluno', command=lambda: self._aluno_form(refresh_callback=refresh_alunos_list, edit=True, tree=tree)).pack(side='left', padx=5)
        customtkinter.CTkButton(frm_botoes_aluno, text='Excluir Aluno', command=lambda: self._remover_aluno(tree, refresh_alunos_list)).pack(side='left', padx=5)
        
        # Botão de Atualizar com ícone e destaque visual
        customtkinter.CTkButton(
            frm_botoes_aluno, 
            text='🔄 Atualizar', 
            command=lambda: refresh_alunos_list(),
            fg_color="#17a2b8",
            hover_color="#138496",
            font=customtkinter.CTkFont(weight="bold")
        ).pack(side='right', padx=5)

    def _aluno_form(self, refresh_callback=None, edit=False, prefill_data=None, tree=None):
        """Formulário completo para criação/edição de alunos com interface moderna"""
        top = customtkinter.CTkToplevel(self)
        top.geometry('750x900')
        top.resizable(True, True)
        top.grab_set()
        
        # Configurar título baseado no modo
        usuarios = carregar_json(ALUNOS_FILE)  # Buscar apenas no arquivo de alunos
        aluno_selecionado = None
        ra_original = None
        
        if edit:
            if not tree or not tree.selection():
                messagebox.showerror("Erro", "Selecione um aluno para alterar.", parent=top)
                top.destroy()
                return
            
            # Obter valores do item selecionado
            item_values = tree.item(tree.selection()[0])['values']
            # Estrutura: (nome, ra, usuario, turma)
            ra_original = str(item_values[1]).strip()  # RA está na segunda coluna
            

            
            # Buscar aluno pelo RA - comparação mais robusta
            aluno_selecionado = None
            for u in usuarios:
                ra_usuario = str(u.get('ra', '')).strip()

                if ra_usuario == ra_original:
                    aluno_selecionado = u
                    break
            
            if not aluno_selecionado:

                messagebox.showerror("Erro", f"Aluno com RA '{ra_original}' não encontrado no sistema.\n\nVerifique se o aluno existe na base de dados.", parent=top)
                top.destroy()
                return
            

            top.title(f"✏️ Alterar Dados - {aluno_selecionado.get('nome', 'Aluno')}")
        elif prefill_data:
            top.title("📝 Finalizar Matrícula de Novo Aluno")
        else:
            top.title("👨‍🎓 Cadastrar Novo Aluno")

        # === HEADER COM INFORMAÇÕES ===
        header_frame = customtkinter.CTkFrame(top, height=80)
        header_frame.pack(fill='x', padx=20, pady=(20, 10))
        header_frame.pack_propagate(False)

        if edit and aluno_selecionado:
            # Buscar informações da turma do aluno
            turmas = carregar_json(TURMAS_FILE)
            turma_aluno = None
            for t in turmas:
                if ra_original in t.get('alunos', []):
                    turma_aluno = t
                    break
            
            info_turma = f"Turma: {turma_aluno.get('serie', 'N/A')} - {turma_aluno.get('turma', 'N/A')}" if turma_aluno else "Turma: Não matriculado"
            
            customtkinter.CTkLabel(
                header_frame, 
                text=f"👤 {aluno_selecionado.get('nome', '')}\n🎓 RA: {ra_original} | {info_turma}",
                font=customtkinter.CTkFont(size=16, weight="bold"),
                justify='center'
            ).pack(expand=True)
        elif prefill_data:
            nome_solicitante = prefill_data.get('Nome', 'Solicitante')
            customtkinter.CTkLabel(
                header_frame,
                text=f"📋 Completando matrícula de: {nome_solicitante}\n✨ Dados preenchidos automaticamente - Verifique e ajuste se necessário",
                font=customtkinter.CTkFont(size=14, weight="bold"),
                justify='center',
                text_color=("#2d5016", "#4a8c2a")
            ).pack(expand=True)
        else:
            customtkinter.CTkLabel(
                header_frame,
                text="📋 Preencha os dados do aluno abaixo\n✨ Campos marcados com * são obrigatórios",
                font=customtkinter.CTkFont(size=14),
                justify='center'
            ).pack(expand=True)

        # === FRAME PRINCIPAL COM SCROLL ===
        main_scroll = customtkinter.CTkScrollableFrame(top)
        main_scroll.pack(fill='both', expand=True, padx=20, pady=10)

        # === SEÇÃO 1: IDENTIFICAÇÃO ===
        id_frame = customtkinter.CTkFrame(main_scroll)
        id_frame.pack(fill='x', pady=(0, 15))
        
        customtkinter.CTkLabel(
            id_frame, 
            text='🎓 IDENTIFICAÇÃO ACADÊMICA', 
            font=customtkinter.CTkFont(size=18, weight="bold"),
            text_color=("#1f538d", "#3b8ed0")
        ).pack(pady=15)

        # RA (somente leitura)
        ra_container = customtkinter.CTkFrame(id_frame, fg_color="transparent")
        ra_container.pack(fill='x', padx=20, pady=5)
        
        customtkinter.CTkLabel(ra_container, text='📄 RA (Registro Acadêmico):').pack(anchor='w')
        ra_display = ra_original if edit else (prefill_data.get('novo_ra', '') if prefill_data else 'Será gerado automaticamente')
        e_ra = customtkinter.CTkEntry(
            ra_container, 
            placeholder_text="RA do aluno",
            height=40,
            font=customtkinter.CTkFont(size=12, weight="bold")
        )
        e_ra.pack(fill='x', pady=(5, 10))
        e_ra.insert(0, ra_display)
        e_ra.configure(state='disabled')

        # === SEÇÃO 2: DADOS PESSOAIS ===
        pessoais_frame = customtkinter.CTkFrame(main_scroll)
        pessoais_frame.pack(fill='x', pady=(0, 15))
        
        customtkinter.CTkLabel(
            pessoais_frame, 
            text='👤 DADOS PESSOAIS', 
            font=customtkinter.CTkFont(size=18, weight="bold"),
            text_color=("#1f538d", "#3b8ed0")
        ).pack(pady=15)

        # Grid para organizar campos pessoais
        grid_pessoais = customtkinter.CTkFrame(pessoais_frame, fg_color="transparent")
        grid_pessoais.pack(fill='x', padx=20, pady=10)
        grid_pessoais.grid_columnconfigure(0, weight=1)
        grid_pessoais.grid_columnconfigure(1, weight=1)

        # Nome completo
        nome_frame = customtkinter.CTkFrame(grid_pessoais, fg_color="transparent")
        nome_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=5)
        customtkinter.CTkLabel(nome_frame, text='📝 Nome Completo: *', font=customtkinter.CTkFont(weight="bold")).pack(anchor='w')
        e_nome = customtkinter.CTkEntry(nome_frame, placeholder_text="Digite o nome completo do aluno", height=40)
        e_nome.pack(fill='x', pady=(5, 0))

        # Data de nascimento
        data_frame = customtkinter.CTkFrame(grid_pessoais, fg_color="transparent")
        data_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=5)
        customtkinter.CTkLabel(data_frame, text='📅 Data de Nascimento: *', font=customtkinter.CTkFont(weight="bold")).pack(anchor='w')
        e_data_nascimento = customtkinter.CTkEntry(data_frame, placeholder_text="DD/MM/AAAA", height=40)
        e_data_nascimento.pack(fill='x', pady=(5, 0))

        # === Remover SEÇÕES 3, 4 e 5 (CONTATO, ENDEREÇO e RESPONSÁVEL) ===
        # Criar variáveis vazias para manter compatibilidade com o código de salvamento
        e_cpf = None
        e_nome_mae = None
        e_telefone = None
        e_email = None
        e_endereco_logradouro = None
        e_endereco_numero = None
        e_endereco_bairro = None
        e_endereco_cidade = None
        e_endereco_cep = None
        e_endereco_estado = None
        e_responsavel_nome = None
        e_responsavel_cpf = None
        e_responsavel_relacao = None
        e_responsavel_telefone = None
        e_responsavel_email = None

        # === SEÇÃO 3: ACESSO AO SISTEMA ===
        sistema_frame = customtkinter.CTkFrame(main_scroll)
        sistema_frame.pack(fill='x', pady=(0, 15))
        
        customtkinter.CTkLabel(
            sistema_frame, 
            text='🔐 ACESSO AO SISTEMA', 
            font=customtkinter.CTkFont(size=18, weight="bold"),
            text_color=("#1f538d", "#3b8ed0")
        ).pack(pady=15)

        # Grid para sistema
        grid_sistema = customtkinter.CTkFrame(sistema_frame, fg_color="transparent")
        grid_sistema.pack(fill='x', padx=20, pady=10)
        grid_sistema.grid_columnconfigure(0, weight=2)
        grid_sistema.grid_columnconfigure(1, weight=1)

        # Usuário
        user_frame = customtkinter.CTkFrame(grid_sistema, fg_color="transparent")
        user_frame.grid(row=0, column=0, sticky='ew', padx=(0, 10), pady=5)
        customtkinter.CTkLabel(user_frame, text='👤 Usuário (Login): *', font=customtkinter.CTkFont(weight="bold")).pack(anchor='w')
        e_user = customtkinter.CTkEntry(user_frame, placeholder_text="Nome de usuário para login", height=40)
        e_user.pack(fill='x', pady=(5, 0))

        # Status
        status_frame = customtkinter.CTkFrame(grid_sistema, fg_color="transparent")
        status_frame.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=5)
        customtkinter.CTkLabel(status_frame, text='📊 Status:', font=customtkinter.CTkFont(weight="bold")).pack(anchor='w')
        e_status = customtkinter.CTkComboBox(status_frame, values=["Ativo", "Inativo", "Suspenso", "Transferido"], height=40)
        e_status.set("Ativo")
        e_status.pack(fill='x', pady=(5, 0))

        # Senha
        senha_container = customtkinter.CTkFrame(grid_sistema, fg_color="transparent")
        senha_container.grid(row=1, column=0, columnspan=2, sticky='ew', pady=5)
        
        senha_label_text = '🔑 Nova Senha:' if edit else '🔑 Senha: *'
        customtkinter.CTkLabel(senha_container, text=senha_label_text, font=customtkinter.CTkFont(weight="bold")).pack(anchor='w')
        
        senha_input_frame = customtkinter.CTkFrame(senha_container, fg_color="transparent")
        senha_input_frame.pack(fill='x', pady=(5, 0))
        senha_input_frame.grid_columnconfigure(0, weight=1)
        
        placeholder_senha = "Deixe vazio para manter atual" if edit else "Digite uma senha segura"
        e_pass = customtkinter.CTkEntry(senha_input_frame, show='*', placeholder_text=placeholder_senha, height=40)
        e_pass.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        
        show_pass_btn = customtkinter.CTkButton(
            senha_input_frame, 
            text="👁", 
            width=50, 
            height=40,
            fg_color=("#3b8ed0", "#1e6091"),
            hover_color=("#2e6da4", "#17537a")
        )
        show_pass_btn.grid(row=0, column=1)

        def toggle_password():
            if e_pass.cget('show') == '*':
                e_pass.configure(show='')
                show_pass_btn.configure(text="🙈")
            else:
                e_pass.configure(show='*')
                show_pass_btn.configure(text="👁")
        show_pass_btn.configure(command=toggle_password)

        # === SEÇÃO 7: OBSERVAÇÕES ===
        obs_frame = customtkinter.CTkFrame(main_scroll)
        obs_frame.pack(fill='x', pady=(0, 15))
        
        customtkinter.CTkLabel(
            obs_frame, 
            text='📝 OBSERVAÇÕES ADICIONAIS', 
            font=customtkinter.CTkFont(size=18, weight="bold"),
            text_color=("#1f538d", "#3b8ed0")
        ).pack(pady=15)

        obs_container = customtkinter.CTkFrame(obs_frame, fg_color="transparent")
        obs_container.pack(fill='x', padx=20, pady=10)
        
        customtkinter.CTkLabel(obs_container, text='💭 Observações:', font=customtkinter.CTkFont(weight="bold")).pack(anchor='w')
        e_observacoes = customtkinter.CTkTextbox(obs_container, height=80)
        e_observacoes.pack(fill='x', pady=(5, 0))

        # === PREENCHIMENTO DOS CAMPOS ===
        if edit and aluno_selecionado:
            e_nome.insert(0, aluno_selecionado.get('nome', ''))
            e_data_nascimento.insert(0, aluno_selecionado.get('data_nascimento', ''))
            e_user.insert(0, aluno_selecionado.get('usuario', ''))
            e_user.configure(state='disabled')  # Não permitir alterar login em edição
            e_status.set(aluno_selecionado.get('status', 'Ativo'))
            if aluno_selecionado.get('observacoes'):
                e_observacoes.insert("1.0", aluno_selecionado.get('observacoes', ''))
        elif prefill_data:
            # Preencher com dados do pedido de matrícula - apenas nome e data

            
            # Preencher campos básicos
            if 'Nome' in prefill_data and prefill_data['Nome']:
                e_nome.insert(0, prefill_data['Nome'])
            
            if 'Data de Nascimento' in prefill_data and prefill_data['Data de Nascimento']:
                e_data_nascimento.insert(0, prefill_data['Data de Nascimento'])
            
            # Gerar usuário automaticamente baseado no nome
            if 'Nome' in prefill_data and prefill_data['Nome']:
                nome_completo = prefill_data['Nome'].strip()
                palavras_nome = nome_completo.split()
                if len(palavras_nome) >= 2:
                    usuario_sugerido = f"{palavras_nome[0]}.{palavras_nome[-1]}"
                else:
                    usuario_sugerido = palavras_nome[0] if palavras_nome else ""
                
                usuario_sugerido = normalizar_texto(usuario_sugerido)
                
                # Verificar disponibilidade
                todos_usuarios = carregar_todos_usuarios()
                contador = 1
                usuario_final = usuario_sugerido
                while any(u['usuario'] == usuario_final for u in todos_usuarios):
                    usuario_final = f"{usuario_sugerido}{contador}"
                    contador += 1
                
                e_user.insert(0, usuario_final)
            
            # Gerar senha mais segura baseada no nome e data
            senha_padrao = "Temp123@"  # Senha temporária mais segura
            if 'Nome' in prefill_data and prefill_data['Nome']:
                # Usar primeira letra do nome + "temp123@"
                primeira_letra = prefill_data['Nome'][0].upper()
                senha_padrao = f"{primeira_letra}temp123@"
            e_pass.insert(0, senha_padrao)
            


        # === FUNÇÃO DE SALVAMENTO ===
        def salvar_dados_aluno():
            # Coletar dados simplificados
            nome = e_nome.get().strip()
            data_nascimento = e_data_nascimento.get().strip()
            
            # Dados do sistema
            usuario = e_user.get().strip()
            senha = e_pass.get().strip()
            status = e_status.get()
            observacoes = e_observacoes.get("1.0", "end-1c").strip()

            # Validações
            if not nome:
                messagebox.showerror('Erro', 'O nome completo é obrigatório.', parent=top)
                e_nome.focus()
                return
            
            if not data_nascimento:
                messagebox.showerror('Erro', 'A data de nascimento é obrigatória.', parent=top)
                e_data_nascimento.focus()
                return

            if not usuario:
                messagebox.showerror('Erro', 'O usuário de login é obrigatório.', parent=top)
                e_user.focus()
                return

            # Validar formato da data
            valida_data, msg_data = validar_data(data_nascimento)
            if not valida_data:
                messagebox.showerror('Erro', msg_data, parent=top)
                e_data_nascimento.focus()
                return

            # Validar idade mínima de 18 anos
            valida_idade, msg_idade = validar_idade_minima(data_nascimento, 18)
            if not valida_idade:
                messagebox.showerror('Erro', msg_idade, parent=top)
                e_data_nascimento.focus()
                return

            # Validar e preparar senha
            senha_para_salvar = None
            if senha:
                valida, msg = self._validar_senha(senha)
                if not valida:
                    messagebox.showerror('Senha Inválida', msg, parent=top)
                    e_pass.focus()
                    return
                senha_para_salvar = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Carregar dados
            data = carregar_json(ALUNOS_FILE)  # Usar arquivo específico de alunos

            if edit:
                # Editar aluno existente
                aluno_encontrado = False
                for usuario_data in data:
                    ra_atual = str(usuario_data.get('ra', '')).strip()
                    ra_procurado = str(ra_original).strip()
                    
                    if ra_atual == ra_procurado:
                        # Atualizar dados
                        usuario_data.update({
                            'nome': nome,
                            'data_nascimento': data_nascimento,
                            'status': status,
                            'observacoes': observacoes
                        })
                        
                        if senha_para_salvar:
                            usuario_data['senha'] = senha_para_salvar
                        
                        aluno_encontrado = True

                        break
                
                if not aluno_encontrado:
                    messagebox.showerror('Erro', f'Aluno com RA {ra_original} não encontrado para alteração.', parent=top)
                    return
                    
                messagebox.showinfo('✅ Sucesso', f'Dados do aluno "{nome}" foram atualizados com sucesso!', parent=top)
            else:
                # Criar novo aluno
                # Verificar se usuário já existe (verificar todos os tipos de usuário)
                todos_usuarios = carregar_todos_usuarios()
                if any(u['usuario'] == usuario for u in todos_usuarios):
                    messagebox.showerror('Erro', f'O usuário "{usuario}" já existe.', parent=top)
                    e_user.focus()
                    return
                
                if not senha_para_salvar:
                    messagebox.showerror('Erro', 'A senha é obrigatória para novos alunos.', parent=top)
                    e_pass.focus()
                    return

                # Gerar novo RA - 8 dígitos começando com 1 (10000000)
                ras_existentes = []
                for u in data:
                    if u.get('ra'):
                        try:
                            ra_num = int(str(u.get('ra', '')).strip())
                            # Apenas considerar RAs no formato correto (8 dígitos começando com 1)
                            if 10000000 <= ra_num <= 19999999:
                                ras_existentes.append(ra_num)
                        except (ValueError, TypeError):
                            continue
                
                # Definir o próximo RA: começar em 10000000 ou incrementar o maior existente
                if ras_existentes:
                    proximo_ra = max(ras_existentes) + 1
                else:
                    proximo_ra = 10000000  # Primeiro RA no novo formato
                
                novo_ra = str(proximo_ra)  # RA já tem 8 dígitos

                # === CONFIRMAÇÃO DE CADASTRO ===
                confirmacao_texto = f"""🎓 CONFIRMAR CADASTRO DE NOVO ALUNO

📝 Nome: {nome}
🆔 RA: {novo_ra}  
👤 Usuário: {usuario}
📅 Data Nasc.: {data_nascimento}

⚠️ Tem certeza que deseja cadastrar este aluno?
Os dados serão salvos permanentemente no sistema."""

                if not messagebox.askyesno(
                    "🎓 Confirmar Cadastro", 
                    confirmacao_texto,
                    parent=top
                ):
                    return  # Usuário cancelou

                # Criar estrutura do aluno com dados simplificados
                novo_aluno = {
                    'tipo': 'aluno',  # Identificação do tipo
                    'usuario': usuario,
                    'senha': senha_para_salvar,
                    'nome': nome,
                    'ra': novo_ra,
                    'data_nascimento': data_nascimento,
                    'status': status,
                    'observacoes': observacoes,
                    'data_cadastro': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                }
                
                # Adicionar à lista
                data.append(novo_aluno)
                
                # Mensagem de sucesso
                messagebox.showinfo(
                    '✅ Cadastro Realizado!', 
                    f'🎉 Aluno cadastrado com sucesso!\n\n'
                    f'📝 Nome: {nome}\n'
                    f'🎓 RA: {novo_ra}\n'
                    f'👤 Usuário: {usuario}\n'
                    f'📅 Data do Cadastro: {datetime.now().strftime("%d/%m/%Y às %H:%M")}\n\n'
                    f'O aluno já pode fazer login no sistema!', 
                    parent=top
                )

            # Salvar arquivo
            salvar_json(ALUNOS_FILE, data)
            
            if refresh_callback:
                refresh_callback()
            
            top.destroy()

        # === RODAPÉ COM BOTÕES ===
        footer_frame = customtkinter.CTkFrame(top, height=80)
        footer_frame.pack(fill='x', padx=20, pady=(10, 20))
        footer_frame.pack_propagate(False)

        button_container = customtkinter.CTkFrame(footer_frame, fg_color="transparent")
        button_container.pack(expand=True, fill='both', padx=20, pady=15)
        button_container.grid_columnconfigure(0, weight=1)
        button_container.grid_columnconfigure(1, weight=1)

        # Botão Cancelar
        btn_cancelar = customtkinter.CTkButton(
            button_container,
            text='❌ Cancelar',
            command=top.destroy,
            font=customtkinter.CTkFont(size=14, weight="bold"),
            height=50,
            fg_color=("#dc3545", "#c82333"),
            hover_color=("#c82333", "#a71e2a")
        )
        btn_cancelar.grid(row=0, column=0, sticky='ew', padx=(0, 10))

        # Botão Salvar
        texto_salvar = "💾 Atualizar Dados" if edit else "💾 Cadastrar Aluno"
        btn_salvar = customtkinter.CTkButton(
            button_container,
            text=texto_salvar,
            command=salvar_dados_aluno,
            font=customtkinter.CTkFont(size=14, weight="bold"),
            height=50,
            fg_color=("#28a745", "#218838"),
            hover_color=("#218838", "#1e7e34")
        )
        btn_salvar.grid(row=0, column=1, sticky='ew', padx=(10, 0))

        # Dica sobre campos obrigatórios
        dica_frame = customtkinter.CTkFrame(main_scroll, fg_color="transparent")
        dica_frame.pack(fill='x', pady=10)
        customtkinter.CTkLabel(
            dica_frame, 
            text='💡 Dica: Campos marcados com * são obrigatórios',
            font=customtkinter.CTkFont(size=11),
            text_color="gray"
        ).pack()

    def _remover_aluno(self, tree, refresh_callback):
        if not tree.selection():
            messagebox.showerror("Erro", "Selecione um aluno para excluir.")
            return
        
        item_selecionado = tree.item(tree.selection()[0])
        nome_aluno = item_selecionado['values'][0]
        ra_aluno = str(item_selecionado['values'][1]).strip()  # Garantir que seja string e remover espaços

        if not messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o aluno '{nome_aluno}' (RA: {ra_aluno})?\n\nEsta ação não pode ser desfeita."):
            return

        # Remover dos usuários - buscar apenas alunos
        usuarios = carregar_json(ALUNOS_FILE)  # Agora busca apenas no arquivo de alunos
        usuarios_filtrados = []
        aluno_removido = False
        
        for u in usuarios:
            ra_atual = str(u.get('ra', '')).strip()
            if ra_atual == ra_aluno:

                aluno_removido = True
                continue  # Pula este usuário (remove da lista)
            usuarios_filtrados.append(u)
        
        if not aluno_removido:
            messagebox.showerror("Erro", f"Aluno com RA {ra_aluno} não foi encontrado para exclusão.")
            return
        
        # Remover das turmas
        turmas = carregar_json(TURMAS_FILE)
        for turma in turmas:
            alunos_turma = turma.get('alunos', [])
            # Remover o RA da lista de alunos da turma
            turma['alunos'] = [ra for ra in alunos_turma if str(ra).strip() != ra_aluno]

        # Salvar alterações
        salvar_json(ALUNOS_FILE, usuarios_filtrados)
        salvar_json(TURMAS_FILE, turmas)

        messagebox.showinfo("Sucesso", f"Aluno '{nome_aluno}' foi excluído com sucesso.")
        refresh_callback()

    def _gerenciar_alunos_turma(self, tree, refresh):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning('Erro', 'Selecione uma turma.')
            return
        turma_values = tree.item(sel[0])['values']
        turma_id = turma_values[0]
        turmas = carregar_json(TURMAS_FILE)
        t = next((x for x in turmas if x['id'] == turma_id), None)
        if not t:
            return

        top = customtkinter.CTkToplevel(self)
        top.title(f"Gerenciar Alunos - Turma {t.get('serie')} {t.get('turma')}")
        top.geometry('600x400')
        top.resizable(False, False)
        top.resizable(False, False)

        tree_alunos = ttk.Treeview(top, columns=('ra', 'nome'), show='headings')
        tree_alunos.heading('ra', text='RA')
        tree_alunos.column('ra', width=150)
        tree_alunos.heading('nome', text='Nome do Aluno')
        tree_alunos.column('nome', width=400)
        tree_alunos.pack(fill='both', expand=True, padx=10, pady=10)

        # Botões de ação
        frm_botoes = customtkinter.CTkFrame(top)
       
        frm_botoes.pack(fill='x', padx=10, pady=5)
        
        def refresh_alunos_na_turma():
            for i in tree_alunos.get_children():
                tree_alunos.delete(i)
            
            # Recarrega os dados da turma específica
            turma_atualizada = next((x for x in carregar_json(TURMAS_FILE) if x['id'] == turma_id), None)
            if turma_atualizada:
                alunos_na_turma_ra = turma_atualizada.get('alunos', [])
                todos_usuarios = carregar_json(ALUNOS_FILE)  # Buscar apenas alunos
                
                for ra_aluno in alunos_na_turma_ra:
                    # Encontra o aluno pelo RA
                    aluno_info = next((u for u in todos_usuarios if u.get('ra') == ra_aluno), None)
                    if aluno_info:
                        tree_alunos.insert('', 'end', values=(aluno_info.get('ra', ''), aluno_info.get('nome', ''), aluno_info.get('usuario', '')))

        customtkinter.CTkButton(frm_botoes, text='Adicionar Aluno', command=lambda: self._adicionar_aluno_turma_form(turma_id, refresh_alunos_na_turma)).pack(side='left', padx=5)
        customtkinter.CTkButton(frm_botoes, text='Remover Aluno', command=lambda: self._remover_aluno_turma(tree_alunos, turma_id, refresh_alunos_na_turma)).pack(side='left', padx=5)

        refresh_alunos_na_turma()

    def _adicionar_aluno_turma_form(self, turma_id, refresh_func):
        top = customtkinter.CTkToplevel(self)
        top.title('Adicionar Aluno à Turma')
        top.geometry('500x400')
        top.resizable(False, False)

        # --- Frame de Pesquisa ---
        frm_pesquisa = customtkinter.CTkFrame(top)
        frm_pesquisa.pack(fill='x', padx=10, pady=10)

        customtkinter.CTkLabel(frm_pesquisa, text="Pesquisar (Nome ou RA):").pack(side='left', padx=5)
        e_pesquisa = customtkinter.CTkEntry(frm_pesquisa)
        e_pesquisa.pack(side='left', fill='x', expand=True, padx=5)
        
        # --- Treeview de Resultados ---
        tree_resultados = ttk.Treeview(top, columns=('ra', 'nome'), show='headings', height=8)
        tree_resultados.heading('ra', text='RA')
        tree_resultados.column('ra', width=100)
        tree_resultados.heading('nome', text='Nome do Aluno')
        tree_resultados.column('nome', width=350)
        tree_resultados.pack(fill='both', expand=True, padx=10, pady=5)

        def pesquisar_alunos():
            termo = e_pesquisa.get().lower().strip()
            for i in tree_resultados.get_children():
                tree_resultados.delete(i)

            todos_usuarios = carregar_json(ALUNOS_FILE)  # Buscar apenas alunos
            turmas = carregar_json(TURMAS_FILE)
            
            # Obter RAs de todos os alunos já matriculados em qualquer turma
            ras_matriculados = set()
            for t in turmas:
                ras_matriculados.update(t.get('alunos', []))

            # Filtrar alunos que não estão em nenhuma turma
            alunos_disponiveis = [u for u in todos_usuarios if u.get('ra') not in ras_matriculados]

            # Filtrar por termo de pesquisa
            if termo:
                resultados = [
                    u for u in alunos_disponiveis 
                    if termo in u.get('nome', '').lower() or termo in u.get('ra', '').lower()
                ]
            else:
                # Mostrar todos os disponíveis se a pesquisa estiver vazia
                resultados = alunos_disponiveis

            for aluno in sorted(resultados, key=lambda x: x.get('nome', '')):
                tree_resultados.insert('', 'end', values=(aluno.get('ra', ''), aluno.get('nome', '')))

        btn_pesquisar = customtkinter.CTkButton(frm_pesquisa, text="Pesquisar", width=80, command=pesquisar_alunos)
        btn_pesquisar.pack(side='left', padx=5)

        def adicionar_aluno_selecionado():
            sel = tree_resultados.selection()
            if not sel:
                messagebox.showerror('Erro', 'Selecione um aluno da lista para adicionar.', parent=top)
                return
            
            ra_aluno = tree_resultados.item(sel[0])['values'][0]
            
            turmas = carregar_json(TURMAS_FILE)
            turma_alvo = next((t for t in turmas if t['id'] == turma_id), None)

            if turma_alvo:
                # Verificação dupla para garantir que o aluno não foi adicionado enquanto a janela estava aberta
                if ra_aluno in turma_alvo.get('alunos', []):
                    messagebox.showwarning('Aviso', 'Este aluno já está na turma.', parent=top)
                    return
                
                # Verifica se o aluno já está em outra turma
                for t in turmas:

                    if ra_aluno in t.get('alunos', []):
                         messagebox.showwarning('Aviso', f"Este aluno já está matriculado na turma {t.get('serie')} - {t.get('turma')}.", parent=top)
                         return

                turma_alvo.setdefault('alunos', []).append(ra_aluno)
                salvar_json(TURMAS_FILE, turmas)
                messagebox.showinfo('Sucesso', 'Aluno adicionado à turma com sucesso.', parent=top)
                refresh_func() # Atualiza a lista de alunos na janela de gerenciamento
                pesquisar_alunos() # Atualiza a lista de pesquisa para remover o aluno adicionado
            else:
                messagebox.showerror('Erro', 'Turma não encontrada. A operação foi cancelada.', parent=top)
                top.destroy()

        # --- Botão de Adicionar ---
        customtkinter.CTkButton(top, text='Adicionar Aluno Selecionado', command=adicionar_aluno_selecionado).pack(pady=10)

        # Carregar alunos disponíveis inicialmente
        pesquisar_alunos()

    def _remover_aluno_turma(self, tree, turma_id, refresh_func):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning('Erro', 'Selecione um aluno.')
            return
        
        aluno_ra = tree.item(sel[0])['values'][0]
        turmas = carregar_json(TURMAS_FILE)
        
        for t in turmas:
            if t['id'] == turma_id:
                if aluno_ra in t.get('alunos', []):
                    t['alunos'].remove(aluno_ra)
                    salvar_json(TURMAS_FILE, turmas)
                    messagebox.showinfo('Sucesso', 'Aluno removido da turma com sucesso.')
                else:
                    messagebox.showwarning('Aviso', 'Aluno não encontrado nesta turma.')
                break
        
        refresh_func()

    # --------- MATÉRIAS ---------
    def _admin_materias_tab(self, parent_tab):
        # --- Frame de Filtros ---
        frm_filtros = customtkinter.CTkFrame(parent_tab)
        frm_filtros.pack(fill='x', padx=10, pady=10)

        customtkinter.CTkLabel(frm_filtros, text="Filtrar por Série:").pack(side='left', padx=(10,5))
        e_serie_filtro = customtkinter.CTkComboBox(frm_filtros, values=[""]+self.series_disponiveis)
        e_serie_filtro.pack(side='left', fill='x', expand=True, padx=5)
        e_serie_filtro.set('')

        customtkinter.CTkLabel(frm_filtros, text="Filtrar por Turma:").pack(side='left', padx=5)
        e_turma_filtro = customtkinter.CTkComboBox(frm_filtros, values=[""]+self.turmas_disponiveis)
        e_turma_filtro.pack(side='left', fill='x', expand=True, padx=5)
        e_turma_filtro.set('')

        customtkinter.CTkLabel(frm_filtros, text="Filtrar por Professor:").pack(side='left', padx=5)
        # Usar nomes dos professores para o filtro
        professores_nomes = list(self.mapa_professores.values())
        e_prof_filtro = customtkinter.CTkComboBox(frm_filtros, values=[""] + sorted(professores_nomes))
        e_prof_filtro.pack(side='left', fill='x', expand=True, padx=5)
        e_prof_filtro.set('')

        def aplicar_filtros():
            serie_sel = e_serie_filtro.get()
            turma_sel = e_turma_filtro.get()
            prof_sel = e_prof_filtro.get()

            # Criar um mapa reverso de Nome -> login para busca
            mapa_nome_prof = {v: k for k, v in self.mapa_professores.items()}
            prof_login_sel = mapa_nome_prof.get(prof_sel)

            for i in tree.get_children():
                tree.delete(i)

            materias = carregar_json(MATERIAS_FILE)
            turmas = carregar_json(TURMAS_FILE)

            for m in materias:
                # Buscar informações da turma pelo ID
                turma_info = next((t for t in turmas if t.get('id') == m.get('turma_id')), None)
                
                if turma_info:
                    serie_materia = turma_info.get('serie', '')
                    turma_materia = turma_info.get('turma', '')
                else:
                    # Compatibilidade com formato antigo
                    serie_materia = m.get('serie', '')
                    turma_materia = m.get('turma', '')

                # Lógica de filtro
                match_serie = not serie_sel or serie_materia == serie_sel
                match_turma = not turma_sel or turma_materia == turma_sel
                match_prof = not prof_sel or m.get('professor') == prof_login_sel

                if match_serie and match_turma and match_prof:
                    # Usar o mapa para obter o nome do professor a partir do login
                    nome_professor = self.mapa_professores.get(m.get('professor'), 'N/A')
                    tree.insert('', 'end', values=(m['id'], m['nome'], serie_materia, turma_materia, nome_professor))

        customtkinter.CTkButton(frm_filtros, text="Aplicar Filtros", command=aplicar_filtros).pack(side='right', padx=5)
        customtkinter.CTkButton(frm_filtros, text="Limpar", command=lambda: (e_serie_filtro.set(''), e_turma_filtro.set(''), e_prof_filtro.set(''), refresh())).pack(side='right', padx=5)


        # --- Treeview de Matérias ---
        tree = ttk.Treeview(parent_tab, columns=('id','nome','serie','turma','professor'), show='headings')
        tree.heading('id', text='ID')
        tree.column('id', width=50)
        tree.heading('nome', text='Nome')
        tree.column('nome', width=200)
        tree.heading('serie', text='Série')
        tree.column('serie', width=120)
        tree.heading('turma', text='Turma')
        tree.column('turma', width=80)
        tree.heading('professor', text='Professor')
        tree.column('professor', width=180)
        tree.pack(expand=True, fill='both', pady=5, padx=5)

        def refresh():
            # Limpa os filtros ao atualizar a lista
            e_serie_filtro.set('')
            e_turma_filtro.set('')
            e_prof_filtro.set('')
            for i in tree.get_children():
                tree.delete(i)
            
            materias = carregar_json(MATERIAS_FILE)
            turmas = carregar_json(TURMAS_FILE)
            
            for m in materias:
                # Buscar informações da turma pelo ID
                turma_info = next((t for t in turmas if t.get('id') == m.get('turma_id')), None)
                
                if turma_info:
                    serie = turma_info.get('serie', 'N/A')
                    turma = turma_info.get('turma', 'N/A')
                else:
                    # Compatibilidade com formato antigo
                    serie = m.get('serie', 'N/A')
                    turma = m.get('turma', 'N/A')
                
                # Usar o mapa para obter o nome do professor a partir do login
                nome_professor = self.mapa_professores.get(m.get('professor'), 'N/A')
                tree.insert('', 'end', values=(m['id'], m['nome'], serie, turma, nome_professor))

        refresh()

        frm = customtkinter.CTkFrame(parent_tab)
        frm.pack(fill='x', pady=8, padx=10)
        customtkinter.CTkButton(frm, text='Adicionar', command=lambda: self._materia_form(refresh)).pack(side='left', padx=5)
        customtkinter.CTkButton(frm, text='Alterar', command=lambda: self._materia_form(refresh, edit=True, tree=tree)).pack(side='left', padx=5)
        customtkinter.CTkButton(frm, text='Remover', command=lambda: self._remover_materia(tree, refresh)).pack(side='left', padx=5)
        
        # Botão de Atualizar com ícone e destaque visual
        customtkinter.CTkButton(
            frm, 
            text='🔄 Atualizar', 
            command=lambda: refresh(),
            fg_color="#17a2b8",
            hover_color="#138496",
            font=customtkinter.CTkFont(weight="bold")
        ).pack(side='right', padx=5)
        
    def _materia_form(self, refresh, edit=False, tree=None):
        top = customtkinter.CTkToplevel(self)
        top.title('Matéria')
        top.geometry('400x400')
        top.resizable(False, False)
        data = carregar_json(MATERIAS_FILE)
        m = None

        if edit and tree:
            sel = tree.selection()
            if not sel:
                messagebox.showwarning('Erro', 'Selecione uma matéria.')
                top.destroy()
                return
            values = tree.item(sel[0])['values']
            m = next((x for x in data if x['id'] == values[0]), None)

        customtkinter.CTkLabel(top, text='Nome:').pack(anchor='w', pady=(10, 0), padx=20)
        e_nome = customtkinter.CTkEntry(top)
        e_nome.pack(fill='x', padx=20, pady=5)
        if m:
            e_nome.insert(0, m['nome'])

        customtkinter.CTkLabel(top, text='Turma:').pack(anchor='w', pady=(10, 0), padx=20)
        # Carregar turmas disponíveis
        turmas_data = carregar_json(TURMAS_FILE)
        turmas_options = [f"{t.get('serie', '')} - {t.get('turma', '')} (ID: {t.get('id', '')})" for t in turmas_data]
        
        e_turma = customtkinter.CTkComboBox(top, values=turmas_options if turmas_options else ["Nenhuma turma disponível"])
        e_turma.pack(fill='x', padx=20, pady=5)
        
        # Se editando, encontrar a turma atual
        if m and m.get('turma_id'):
            turma_atual = next((t for t in turmas_data if t.get('id') == m.get('turma_id')), None)
            if turma_atual:
                turma_display = f"{turma_atual.get('serie', '')} - {turma_atual.get('turma', '')} (ID: {turma_atual.get('id', '')})"
                if turma_display in turmas_options:
                    e_turma.set(turma_display)

        customtkinter.CTkLabel(top, text='Professor:').pack(anchor='w', pady=(5, 0), padx=20)
        # Usar o mapa reverso para preencher o combobox com Nomes, mas salvar o login
        mapa_nome_prof = {v: k for k, v in self.mapa_professores.items()}
        professores_nomes = sorted(list(self.mapa_professores.values()))
        e_prof = customtkinter.CTkComboBox(top, values=professores_nomes)
        e_prof.pack(fill='x', padx=20, pady=(0, 5))
        if m and m.get('professor'):
            # Encontrar o nome do professor a partir do login salvo
            nome_prof_salvo = self.mapa_professores.get(m.get('professor'))
            if nome_prof_salvo:
                e_prof.set(nome_prof_salvo)

        def salvar():
            nome = e_nome.get().strip()
            turma_selecionada = e_turma.get()
            nome_prof_selecionado = e_prof.get()

            if not nome or not turma_selecionada or not nome_prof_selecionado or turma_selecionada == "Nenhuma turma disponível":
                messagebox.showerror('Erro', 'Todos os campos são obrigatórios.', parent=top)
                return

            # Extrair ID da turma da string selecionada
            try:
                # Formato: "Serie - Turma (ID: X)"
                turma_id = int(turma_selecionada.split("(ID: ")[1].split(")")[0])
            except (IndexError, ValueError):
                messagebox.showerror('Erro', 'Formato da turma inválido.', parent=top)
                return

            # Obter o login do professor a partir do nome selecionado
            login_prof = mapa_nome_prof.get(nome_prof_selecionado)
            if not login_prof:
                messagebox.showerror('Erro', 'Professor selecionado não é válido.', parent=top)
                return

            if edit and m:
                m['nome'] = nome
                m['turma_id'] = turma_id
                m['professor'] = login_prof
            else:
                novo_id = max([x.get('id', 0) for x in data], default=0) + 1
                data.append({'id': novo_id, 'nome': nome, 'turma_id': turma_id, 'professor': login_prof})
            
            salvar_json(MATERIAS_FILE, data)
            refresh()
            top.destroy()

        customtkinter.CTkButton(top, text='Salvar', command=salvar).pack(pady=20)

    def _remover_materia(self, tree, refresh):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning('Erro', 'Selecione uma matéria')
            return
        
        # confirmar exclusão
        if not messagebox.askyesno('Confirmar', 'Confirma a exclusão da matéria selecionada?'):
            return

        data = carregar_json(MATERIAS_FILE)
        mid = tree.item(sel[0])['values'][0]
        data = [x for x in data if x['id'] != mid]
        salvar_json(MATERIAS_FILE, data)
        refresh()

    def _admin_pedidos_tab(self, parent_tab):
        main_frame = customtkinter.CTkFrame(parent_tab, fg_color="transparent")
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # --- Filtros ---
        filter_frame = customtkinter.CTkFrame(main_frame)
        filter_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        customtkinter.CTkLabel(filter_frame, text="Filtrar por Status:").pack(side='left', padx=10)
        combo_status = customtkinter.CTkComboBox(filter_frame, values=["Todos", "Pendente", "Aprovado", "Recusado"])
        combo_status.pack(side='left', padx=5)
        combo_status.set("Pendente")

        # --- Lista de Pedidos ---
        list_frame = customtkinter.CTkFrame(main_frame)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        tree_pedidos = ttk.Treeview(list_frame, columns=('id', 'data', 'tipo', 'status', 'solicitante'), show='headings')
        tree_pedidos.heading('id', text='ID')
        tree_pedidos.column('id', width=40)
        tree_pedidos.heading('data', text='Data')
        tree_pedidos.column('data', width=120)
        tree_pedidos.heading('tipo', text='Tipo')
        tree_pedidos.column('tipo', width=80)
        tree_pedidos.heading('status', text='Status')
        tree_pedidos.column('status', width=80)
        tree_pedidos.heading('solicitante', text='Solicitante')
        tree_pedidos.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # --- Detalhes e Ações ---
        details_frame = customtkinter.CTkFrame(main_frame)
        details_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        details_frame.grid_rowconfigure(1, weight=1)
        details_frame.grid_columnconfigure(0, weight=1)

        lbl_detalhes = customtkinter.CTkLabel(details_frame, text="Detalhes do Pedido", font=customtkinter.CTkFont(weight="bold"))
        lbl_detalhes.grid(row=0, column=0, pady=5, padx=10, sticky="w")
        txt_descricao = customtkinter.CTkTextbox(details_frame, state="disabled", wrap="word")
        txt_descricao.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))

        action_frame = customtkinter.CTkFrame(details_frame, fg_color="transparent")
        action_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        btn_aprovar = customtkinter.CTkButton(action_frame, text="Aprovar Matrícula", state="disabled", command=lambda: aprovar_matricula())
        btn_aprovar.pack(side='right', padx=5)
        btn_recusar = customtkinter.CTkButton(action_frame, text="Recusar Pedido", state="disabled", fg_color="#dc3545", hover_color="#c82333", command=lambda: recusar_pedido())
        btn_recusar.pack(side='right', padx=5)

        def refresh_pedidos():
            status_filtro = combo_status.get()
            for i in tree_pedidos.get_children():
                tree_pedidos.delete(i)
            
            pedidos = carregar_json(PEDIDOS_FILE)
            for p in sorted(pedidos, key=lambda x: x.get('data', ''), reverse=True):
                if status_filtro == "Todos" or p.get('status') == status_filtro:
                    tree_pedidos.insert('', 'end', iid=p['id'], values=(
                        p['id'], p.get('data', ''), p.get('tipo', ''), p.get('status', ''), p.get('solicitante_nome', '')
                    ))
            on_pedido_select() # Limpar detalhes

        def on_pedido_select(event=None):
            sel = tree_pedidos.selection()
            txt_descricao.configure(state="normal")
            txt_descricao.delete("1.0", "end")
            
            if not sel:
                lbl_detalhes.configure(text="Detalhes do Pedido")
                btn_aprovar.configure(state="disabled")
                btn_recusar.configure(state="disabled")
                txt_descricao.configure(state="disabled")
                return

            pedido_id = int(sel[0])
            pedidos = carregar_json(PEDIDOS_FILE)
            pedido = next((p for p in pedidos if p['id'] == pedido_id), None)

            if pedido:
                lbl_detalhes.configure(text=f"Detalhes do Pedido #{pedido_id} - {pedido.get('tipo')}")
                
                # Formatação melhorada dos detalhes do pedido
                detalhes_formatados = self._formatar_detalhes_pedido(pedido)
                txt_descricao.insert("1.0", detalhes_formatados)
                
                if pedido.get('status') == 'Pendente':
                    btn_recusar.configure(state="normal")
                    if pedido.get('tipo') == 'Matrícula':
                        btn_aprovar.configure(state="normal")
                    else:
                        btn_aprovar.configure(state="disabled")
                else:
                    btn_aprovar.configure(state="disabled")
                    btn_recusar.configure(state="disabled")
            txt_descricao.configure(state="disabled")

        def aprovar_matricula():
            sel = tree_pedidos.selection()
            if not sel: return
            pedido_id = int(sel[0])
            pedidos = carregar_json(PEDIDOS_FILE)
            pedido = next((p for p in pedidos if p['id'] == pedido_id), None)
            if not pedido: return


            
            # Verificar se o pedido tem dados estruturados (novo formato)
            if 'dados_aluno' in pedido and 'dados_responsavel' in pedido:
                # Novo formato - usar dados estruturados
                endereco_info = pedido.get('endereco', {})
                dados_aluno = {
                    'Nome': pedido['dados_aluno'].get('nome', ''),
                    'Data de Nascimento': pedido['dados_aluno'].get('data_nascimento', ''),
                    'CPF do Aluno': pedido['dados_aluno'].get('cpf', ''),
                    'Nome da Mãe': pedido['dados_aluno'].get('nome_mae', ''),
                    'Nome do Responsável': pedido['dados_responsavel'].get('nome', ''),
                    'CPF do Responsável': pedido['dados_responsavel'].get('cpf', ''),
                    'Relação': pedido['dados_responsavel'].get('relacao', ''),
                    'Telefone': pedido['dados_responsavel'].get('telefone', ''),
                    'Email': pedido['dados_responsavel'].get('email', ''),
                    # Dados de Endereço
                    'Logradouro': endereco_info.get('logradouro', ''),
                    'Número': endereco_info.get('numero', ''),
                    'Bairro': endereco_info.get('bairro', ''),
                    'Cidade': endereco_info.get('cidade', ''),
                    'CEP': endereco_info.get('cep', ''),
                    'Estado': endereco_info.get('estado', ''),
                    # Outros dados
                    'Série Desejada': pedido.get('serie_desejada', ''),
                    'Informações Adicionais': pedido.get('informacoes_adicionais', ''),
                    'novo_ra': f"ALU{pedido_id:06d}"  # Gerar RA baseado no ID do pedido
                }
            else:
                # Formato antigo - extrair dados da descrição
                descricao = pedido.get('descricao', '')

                
                # Usar regex para extrair pares chave-valor da descrição
                dados_aluno = {}
                linhas = descricao.split('\n')
                
                for linha in linhas:
                    if ':' in linha and not linha.strip().startswith('Informações Adicionais'):
                        partes = linha.split(':', 1)
                        if len(partes) == 2:
                            chave = partes[0].strip()
                            valor = partes[1].strip()
                            if valor:  # Só adicionar se o valor não estiver vazio
                                dados_aluno[chave] = valor
                
                # Capturar informações adicionais separadamente
                if 'Informações Adicionais:' in descricao:
                    inicio_info = descricao.find('Informações Adicionais:')
                    info_adicional = descricao[inicio_info + len('Informações Adicionais:'):].strip()
                    if info_adicional:
                        dados_aluno['Informações Adicionais'] = info_adicional
                
                # Gerar RA para formato antigo também
                dados_aluno['novo_ra'] = f"ALU{pedido_id:06d}"
            

            
            # Chamar o formulário de aluno, passando os dados pré-preenchidos
            self._aluno_form(
                refresh_callback=lambda: (
                    atualizar_status_pedido(pedido_id, "Aprovado"),
                    refresh_pedidos()
                ),
                prefill_data=dados_aluno
            )

        def recusar_pedido():
            sel = tree_pedidos.selection()
            if not sel: return
            pedido_id = int(sel[0])
            if messagebox.askyesno("Confirmar", "Tem certeza que deseja recusar este pedido?"):
                atualizar_status_pedido(pedido_id, "Recusado")
                refresh_pedidos()

        def atualizar_status_pedido(pedido_id, novo_status, ra_aluno=None):
            pedidos = carregar_json(PEDIDOS_FILE)
            for p in pedidos:
                if p['id'] == pedido_id:
                    p['status'] = novo_status
                    if ra_aluno:
                        p['aluno_ra'] = ra_aluno
                    break
            salvar_json(PEDIDOS_FILE, pedidos)

        combo_status.configure(command=lambda choice: refresh_pedidos())
        tree_pedidos.bind("<<TreeviewSelect>>", on_pedido_select)
        
        # Adicionar botão de atualizar na área de filtros
        customtkinter.CTkButton(
            filter_frame, 
            text='🔄 Atualizar', 
            command=lambda: refresh_pedidos(),
            fg_color="#17a2b8",
            hover_color="#138496",
            font=customtkinter.CTkFont(weight="bold"),
            width=120
        ).pack(side='right', padx=10)
        
        refresh_pedidos()

    # SISTEMA DE NOTÍCIAS REMOVIDO
    # As funções _admin_noticias_tab, _noticia_form e _remover_noticia foram removidas

    # --------- PROFESSOR ---------
    def _tab_prof(self, parent_tab):
        user_login = self.usuario_logado['usuario']
        nome_professor = self.mapa_professores.get(user_login, user_login)

        # Buscar turmas onde o professor é responsável (por nome ou login)
        turmas = carregar_json(TURMAS_FILE)
        turmas_professor = [t for t in turmas if t.get('professor', '') == nome_professor or t.get('professor_login', '') == user_login]
        
        # Buscar matérias do professor
        materias = carregar_json(MATERIAS_FILE)
        materias_do_prof = [m for m in materias if m.get('professor') == user_login]

        # --- Frame principal para organizar o layout ---
        main_prof_frame = customtkinter.CTkFrame(parent_tab, fg_color="transparent")
        main_prof_frame.pack(fill='both', expand=True)
        main_prof_frame.grid_rowconfigure(0, weight=1)
        main_prof_frame.grid_columnconfigure(0, weight=1)

        tabs_prof = customtkinter.CTkTabview(main_prof_frame)
        tabs_prof.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        # ================= MINHAS TURMAS =================
        tab_minhas_turmas = tabs_prof.add('Minhas Turmas')
        self._criar_aba_minhas_turmas(tab_minhas_turmas, turmas_professor, nome_professor)
        
        # ================= MINHAS MATÉRIAS =================
        tab_minhas_materias = tabs_prof.add('Minhas Matérias')
        self._criar_aba_minhas_materias(tab_minhas_materias, materias_do_prof, user_login)
        
        # ================= LANÇAMENTO DE NOTAS =================
        tab_notas = tabs_prof.add('Lançar Notas')
        self._criar_aba_lancamento_notas(tab_notas, materias_do_prof, user_login)
        
        # ================= REGISTROS DE AULA =================
        tab_registros = tabs_prof.add('Registros de Aula')
        self._criar_aba_registros_aula(tab_registros, materias_do_prof, user_login)
        
        # Aba de Segurança
        tab_seguranca = tabs_prof.add("Segurança")
        self._criar_aba_seguranca(tab_seguranca)
        
        self._criar_controles_inferiores(parent_tab)

    def _criar_aba_minhas_turmas(self, parent_tab, turmas_professor, nome_professor):
        """Cria a aba de visualização das turmas do professor"""
        if not turmas_professor:
            customtkinter.CTkLabel(parent_tab, text="Você não é responsável por nenhuma turma.", 
                                  font=customtkinter.CTkFont(size=16)).pack(pady=50)
            return

        tree_turmas = ttk.Treeview(parent_tab, columns=('serie', 'turma', 'alunos', 'tempo_curso'), show='headings')
        tree_turmas.heading('serie', text='Série')
        tree_turmas.column('serie', width=150)
        tree_turmas.heading('turma', text='Turma')
        tree_turmas.column('turma', width=100)
        tree_turmas.heading('alunos', text='Qtd Alunos')
        tree_turmas.column('alunos', width=100, anchor='center')
        tree_turmas.heading('tempo_curso', text='Tempo de Curso')
        tree_turmas.column('tempo_curso', width=150)
        tree_turmas.pack(fill='both', expand=True, padx=10, pady=10)

        for turma in turmas_professor:
            qtd_alunos = len(turma.get('alunos', []))
            tree_turmas.insert('', 'end', values=(
                turma.get('serie', ''),
                turma.get('turma', ''),
                qtd_alunos,
                turma.get('tempo_curso', '')
            ))

    def _criar_aba_minhas_materias(self, parent_tab, materias_prof, user_login):
        """Cria a aba de visualização das matérias do professor"""
        if not materias_prof:
            customtkinter.CTkLabel(parent_tab, text="Você não possui matérias atribuídas.", 
                                  font=customtkinter.CTkFont(size=16)).pack(pady=50)
            return

        tree_materias = ttk.Treeview(parent_tab, columns=('nome', 'serie', 'turma'), show='headings')
        tree_materias.heading('nome', text='Nome da Matéria')
        tree_materias.column('nome', width=200)
        tree_materias.heading('serie', text='Série')
        tree_materias.column('serie', width=150)
        tree_materias.heading('turma', text='Turma')
        tree_materias.column('turma', width=100)
        tree_materias.pack(fill='both', expand=True, padx=10, pady=10)

        # Obter informações das turmas para exibição
        turmas = carregar_json(TURMAS_FILE)
        turma_info = {t['id']: f"{t.get('serie', '')} - {t.get('turma', '')}" for t in turmas}
        
        for materia in materias_prof:
            turma_display = turma_info.get(materia.get('turma_id'), 'N/A')
            serie_turma_split = turma_display.split(' - ') if ' - ' in turma_display else ['N/A', 'N/A']
            tree_materias.insert('', 'end', values=(
                materia['nome'],
                serie_turma_split[0],
                serie_turma_split[1]
            ))

        # Botão para visualizar alunos da matéria selecionada
        btn_frame = customtkinter.CTkFrame(parent_tab)
        btn_frame.pack(fill='x', padx=10, pady=5)
        customtkinter.CTkButton(btn_frame, text='Ver Alunos e Notas', 
                               command=lambda: self._visualizar_alunos_materia(tree_materias)).pack(side='left', padx=5)

    def _criar_aba_registros_aula(self, parent_tab, materias_prof, user_login):
        """Cria a aba para registros de aula"""
        if not materias_prof:
            customtkinter.CTkLabel(parent_tab, text="Você não possui matérias para registrar aulas.", 
                                  font=customtkinter.CTkFont(size=16)).pack(pady=50)
            return

        # --- Frame Superior para Formulário ---
        top_frame = customtkinter.CTkFrame(parent_tab)
        top_frame.pack(fill='x', padx=10, pady=10)
        top_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(top_frame, text="Matéria:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        # Obter informações das turmas para mostrar série e turma
        turmas = carregar_json(TURMAS_FILE)
        turma_info = {t['id']: f"{t.get('serie', '')} - {t.get('turma', '')}" for t in turmas}
        mapa_materias_prof = {f"{m['nome']} ({turma_info.get(m.get('turma_id'), 'N/A')})": m['id'] for m in materias_prof}
        combo_materias = customtkinter.CTkComboBox(top_frame, values=["Selecione uma matéria"] + list(mapa_materias_prof.keys()))
        combo_materias.grid(row=0, column=1, padx=10, pady=10, sticky='ew')
        combo_materias.set("Selecione uma matéria")

        customtkinter.CTkLabel(top_frame, text="Data (DD/MM/AAAA):").grid(row=1, column=0, padx=10, pady=5, sticky='w')
        entry_data = customtkinter.CTkEntry(top_frame, placeholder_text="Ex: 15/03/2024")
        entry_data.grid(row=1, column=1, padx=10, pady=5, sticky='ew')

        customtkinter.CTkLabel(top_frame, text="Nome da Aula:").grid(row=2, column=0, padx=10, pady=5, sticky='w')
        entry_nome_aula = customtkinter.CTkEntry(top_frame, placeholder_text="Ex: Introdução à Matemática")
        entry_nome_aula.grid(row=2, column=1, padx=10, pady=5, sticky='ew')

        customtkinter.CTkLabel(top_frame, text="Descrição:").grid(row=3, column=0, padx=10, pady=5, sticky='nw')
        entry_descricao = customtkinter.CTkTextbox(top_frame, height=60)
        entry_descricao.grid(row=3, column=1, padx=10, pady=5, sticky='ew')

        # --- Frame Inferior para Lista de Registros ---
        bottom_frame = customtkinter.CTkFrame(parent_tab)
        bottom_frame.pack(fill='both', expand=True, padx=10, pady=(0,10))

        # --- Frame do cabeçalho com botão de atividade ---
        header_frame = customtkinter.CTkFrame(bottom_frame)
        header_frame.pack(fill='x', padx=5, pady=5)
        
        customtkinter.CTkLabel(header_frame, text="Registros Anteriores", font=customtkinter.CTkFont(weight="bold")).pack(side='left', pady=5)
        
        btn_gerenciar_atividades = customtkinter.CTkButton(header_frame, text="Gerenciar Atividades", state="disabled", 
                                                          command=lambda: self._gerenciar_atividades_registro(user_login))
        btn_gerenciar_atividades.pack(side='right', pady=5, padx=5)
        
        btn_criar_atividade = customtkinter.CTkButton(header_frame, text="Criar Atividade", state="disabled", 
                                                      command=lambda: self._abrir_janela_criar_atividade(user_login))
        btn_criar_atividade.pack(side='right', pady=5, padx=5)

        tree_registros = ttk.Treeview(bottom_frame, columns=('data', 'nome_aula', 'descricao', 'atividades'), show='headings')
        tree_registros.heading('data', text='Data')
        tree_registros.column('data', width=100)
        tree_registros.heading('nome_aula', text='Nome da Aula')
        tree_registros.column('nome_aula', width=180)
        tree_registros.heading('descricao', text='Descrição')
        tree_registros.column('descricao', width=250)
        tree_registros.heading('atividades', text='Atividades')
        tree_registros.column('atividades', width=100)
        tree_registros.pack(fill='both', expand=True, padx=5, pady=5)

        def refresh_registros(materia_id=None):
            for i in tree_registros.get_children():
                tree_registros.delete(i)
            
            if materia_id:
                registros = carregar_json(REGISTROS_AULA_FILE)
                registros_materia = [r for r in registros if r.get('materia_id') == materia_id and r.get('professor_login') == user_login]
                for registro in sorted(registros_materia, key=lambda x: x.get('data', ''), reverse=True):
                    # Contar atividades deste registro
                    atividades_count = len(registro.get('atividades', []))
                    atividades_text = f"{atividades_count} atividade(s)" if atividades_count > 0 else "Nenhuma"
                    
                    tree_registros.insert('', 'end', values=(
                        registro.get('data', ''),
                        registro.get('nome_aula', ''),
                        registro.get('descricao', '')[:40] + '...' if len(registro.get('descricao', '')) > 40 else registro.get('descricao', ''),
                        atividades_text
                    ), tags=(f"registro_{registros.index(registro)}",))

        # Variável global para armazenar o registro selecionado
        self.registro_selecionado = None
        self.materia_selecionada_id = None

        def on_tree_select(event):
            selection = tree_registros.selection()
            if selection:
                item = tree_registros.item(selection[0])
                tags = item.get('tags', [])
                if tags:
                    # Extrair índice do registro das tags
                    tag = tags[0]
                    if tag.startswith('registro_'):
                        registro_index = int(tag.split('_')[1])
                        registros = carregar_json(REGISTROS_AULA_FILE)
                        if registro_index < len(registros):
                            self.registro_selecionado = registros[registro_index]
                            btn_criar_atividade.configure(state="normal")
                            btn_gerenciar_atividades.configure(state="normal")
                            return
            
            self.registro_selecionado = None
            btn_criar_atividade.configure(state="disabled")
            btn_gerenciar_atividades.configure(state="disabled")

        tree_registros.bind('<<TreeviewSelect>>', on_tree_select)

        def on_materia_select(choice=None):
            materia_selecionada_str = combo_materias.get()
            materia_id = mapa_materias_prof.get(materia_selecionada_str)
            if materia_id:
                self.materia_selecionada_id = materia_id
                refresh_registros(materia_id)
            else:
                self.materia_selecionada_id = None
                refresh_registros()
            
            # Resetar seleção ao trocar de matéria
            self.registro_selecionado = None
            btn_criar_atividade.configure(state="disabled")
            btn_gerenciar_atividades.configure(state="disabled")

        combo_materias.configure(command=on_materia_select)

        def salvar_registro():
            materia_selecionada_str = combo_materias.get()
            materia_id = mapa_materias_prof.get(materia_selecionada_str)
            data = entry_data.get().strip()
            nome_aula = entry_nome_aula.get().strip()
            descricao = entry_descricao.get("1.0", "end-1c").strip()

            if not materia_id or materia_selecionada_str == "Selecione uma matéria":
                messagebox.showerror("Erro", "Por favor, selecione uma matéria.")
                return
            if not all([data, nome_aula, descricao]):
                messagebox.showerror("Erro", "Todos os campos (Data, Nome da Aula, Descrição) são obrigatórios.")
                return

            # Validar formato da data
            try:
                data_aula_obj = datetime.strptime(data, '%d/%m/%Y')
            except ValueError:
                messagebox.showerror("Erro", "Data deve estar no formato DD/MM/AAAA e conter apenas números válidos.")
                return

            # Validar se a data não é futura demais (não pode ser mais de 1 ano no futuro)
            data_atual = datetime.now()
            limite_futuro = data_atual.replace(year=data_atual.year + 1)
            if data_aula_obj > limite_futuro:
                messagebox.showerror("Erro", "A data da aula não pode ser mais de 1 ano no futuro.")
                return

            novo_registro = {
                "materia_id": materia_id,
                "professor_login": user_login,
                "data": data,
                "nome_aula": nome_aula,
                "descricao": descricao,
                "atividades": []  # Inicializar lista de atividades vazia
            }

            registros = carregar_json(REGISTROS_AULA_FILE)
            registros.append(novo_registro)
            salvar_json(REGISTROS_AULA_FILE, registros)

            messagebox.showinfo("Sucesso", "Registro de aula salvo com sucesso.")
            # Limpar campos e atualizar a lista
            entry_data.delete(0, 'end')
            entry_nome_aula.delete(0, 'end')
            entry_descricao.delete("1.0", "end")
            refresh_registros(materia_id)

        btn_salvar = customtkinter.CTkButton(top_frame, text="Salvar Registro", command=salvar_registro)
        btn_salvar.grid(row=4, column=1, padx=10, pady=10, sticky='e')

    def _abrir_janela_criar_atividade(self, professor_login):
        """Abre dashboard completa para criar atividade para o registro de aula selecionado"""
        if not hasattr(self, 'registro_selecionado') or not self.registro_selecionado:
            messagebox.showerror("Erro", "Por favor, selecione um registro de aula primeiro.")
            return

        # Criar nova janela maximizada (dashboard completa)
        dashboard_atividade = customtkinter.CTkToplevel(self)
        dashboard_atividade.title("🎯 Dashboard - Criar Atividade")
        dashboard_atividade.state('zoomed')  # Maximizar janela
        dashboard_atividade.transient(self)
        
        # === CABEÇALHO PRINCIPAL ===
        header_main = customtkinter.CTkFrame(dashboard_atividade, height=100)
        header_main.pack(fill='x', padx=20, pady=20)
        header_main.pack_propagate(False)
        
        # Título principal
        customtkinter.CTkLabel(
            header_main, 
            text="🎯 CRIADOR DE ATIVIDADES", 
            font=customtkinter.CTkFont(size=28, weight="bold"),
            text_color=("#1f538d", "#3b8ed0")
        ).pack(pady=10)
        
        # Informações do registro
        info_text = f"📚 Aula: {self.registro_selecionado.get('nome_aula', '')} | 📅 Data: {self.registro_selecionado.get('data', '')}"
        customtkinter.CTkLabel(
            header_main, 
            text=info_text,
            font=customtkinter.CTkFont(size=14),
            text_color="gray"
        ).pack()

        # === FRAME PRINCIPAL COM SCROLL ===
        main_scroll = customtkinter.CTkScrollableFrame(dashboard_atividade)
        main_scroll.pack(fill='both', expand=True, padx=20, pady=(0, 10))

        # === SEÇÃO 1: CONFIGURAÇÕES BÁSICAS ===
        config_basicas_frame = customtkinter.CTkFrame(main_scroll)
        config_basicas_frame.pack(fill='x', pady=(0, 20))
        
        customtkinter.CTkLabel(
            config_basicas_frame, 
            text='⚙️ CONFIGURAÇÕES BÁSICAS DA ATIVIDADE', 
            font=customtkinter.CTkFont(size=18, weight="bold"),
            text_color=("#1f538d", "#3b8ed0")
        ).pack(pady=15)

        # Grid para configurações básicas
        grid_basicas = customtkinter.CTkFrame(config_basicas_frame, fg_color="transparent")
        grid_basicas.pack(fill='x', padx=20, pady=10)
        grid_basicas.grid_columnconfigure(1, weight=1)
        grid_basicas.grid_columnconfigure(3, weight=1)

        # Nome da atividade
        customtkinter.CTkLabel(grid_basicas, text="📝 Nome da Atividade: *", 
                              font=customtkinter.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky='w')
        entry_nome_atividade = customtkinter.CTkEntry(grid_basicas, placeholder_text="Ex: Exercício sobre Matemática Básica", height=40)
        entry_nome_atividade.grid(row=0, column=1, padx=10, pady=10, sticky='ew')

        # Tipo de atividade
        customtkinter.CTkLabel(grid_basicas, text="📋 Tipo de Atividade: *", 
                              font=customtkinter.CTkFont(weight="bold")).grid(row=0, column=2, padx=10, pady=10, sticky='w')
        tipo_var = customtkinter.StringVar(value="Múltipla Escolha")
        tipo_combo = customtkinter.CTkComboBox(grid_basicas, values=["Múltipla Escolha", "Dissertativa"], 
                                              variable=tipo_var, height=40)
        tipo_combo.grid(row=0, column=3, padx=10, pady=10, sticky='ew')

        # Data de entrega
        customtkinter.CTkLabel(grid_basicas, text="📅 Data de Entrega: *", 
                              font=customtkinter.CTkFont(weight="bold")).grid(row=1, column=0, padx=10, pady=10, sticky='w')
        entry_data_entrega = customtkinter.CTkEntry(grid_basicas, placeholder_text="DD/MM/AAAA", height=40)
        entry_data_entrega.grid(row=1, column=1, padx=10, pady=10, sticky='ew')

        # Pontuação máxima
        customtkinter.CTkLabel(grid_basicas, text="🏆 Pontuação Máxima: *", 
                              font=customtkinter.CTkFont(weight="bold")).grid(row=1, column=2, padx=10, pady=10, sticky='w')
        entry_pontuacao = customtkinter.CTkEntry(grid_basicas, placeholder_text="Ex: 10.0", height=40)
        entry_pontuacao.grid(row=1, column=3, padx=10, pady=10, sticky='ew')

        # Descrição (linha completa)
        customtkinter.CTkLabel(grid_basicas, text="📄 Descrição da Atividade: *", 
                              font=customtkinter.CTkFont(weight="bold")).grid(row=2, column=0, padx=10, pady=(20,5), sticky='nw')
        entry_descricao_atividade = customtkinter.CTkTextbox(grid_basicas, height=100)
        entry_descricao_atividade.grid(row=2, column=1, columnspan=3, padx=10, pady=(20,10), sticky='ew')
        entry_descricao_atividade.insert("1.0", "Descreva detalhadamente os objetivos e instruções desta atividade...")

        # Status da atividade
        status_frame = customtkinter.CTkFrame(grid_basicas, fg_color="transparent")
        status_frame.grid(row=3, column=0, columnspan=4, padx=10, pady=20, sticky='ew')
        
        customtkinter.CTkLabel(status_frame, text="🔓 Status da Atividade:", 
                              font=customtkinter.CTkFont(weight="bold")).pack(side='left', padx=(0, 20))
        status_var = customtkinter.StringVar(value="Não Liberada")
        status_switch = customtkinter.CTkSwitch(status_frame, text="✅ Liberar imediatamente para os alunos", 
                                               variable=status_var, onvalue="Liberada", offvalue="Não Liberada",
                                               font=customtkinter.CTkFont(size=14))
        status_switch.pack(side='left')

        # === SEÇÃO 2: CONFIGURAÇÃO DE QUESTÕES ===
        questoes_frame = customtkinter.CTkFrame(main_scroll)
        questoes_frame.pack(fill='x', pady=(0, 20))
        
        customtkinter.CTkLabel(
            questoes_frame, 
            text='❓ CONFIGURAÇÃO DE QUESTÕES', 
            font=customtkinter.CTkFont(size=18, weight="bold"),
            text_color=("#1f538d", "#3b8ed0")
        ).pack(pady=15)

        # Controles de quantidade de questões
        controles_frame = customtkinter.CTkFrame(questoes_frame, fg_color="transparent")
        controles_frame.pack(fill='x', padx=20, pady=10)

        customtkinter.CTkLabel(controles_frame, text="🔢 Quantidade de Questões:", 
                              font=customtkinter.CTkFont(size=14, weight="bold")).pack(side='left', padx=(0, 10))
        
        entry_num_questoes = customtkinter.CTkEntry(controles_frame, placeholder_text="Ex: 5", width=100, height=40)
        entry_num_questoes.pack(side='left', padx=(0, 20))
        
        # Label para mostrar quantidade atual
        lbl_quantidade_atual = customtkinter.CTkLabel(controles_frame, text="📊 Questões criadas: 0", 
                                                     font=customtkinter.CTkFont(size=12), text_color="gray")
        lbl_quantidade_atual.pack(side='left', padx=(20, 0))

        # Widgets que serão criados dinamicamente
        self._config_widgets = {
            'questoes_widgets': [],
            'scroll_questoes': None,
            'lbl_quantidade': lbl_quantidade_atual
        }

        # Frame para as questões com scroll
        scroll_questoes = customtkinter.CTkScrollableFrame(questoes_frame, height=400)
        scroll_questoes.pack(fill='both', expand=True, padx=20, pady=10)
        scroll_questoes.grid_columnconfigure(0, weight=1)
        self._config_widgets['scroll_questoes'] = scroll_questoes

        # Instruções iniciais
        instrucoes_label = customtkinter.CTkLabel(
            scroll_questoes, 
            text="👆 Digite a quantidade de questões acima e clique em 'Gerar Questões' para começar",
            font=customtkinter.CTkFont(size=14),
            text_color="gray"
        )
        instrucoes_label.grid(row=0, column=0, pady=50)
        self._config_widgets['instrucoes'] = instrucoes_label

        def gerar_questoes():
            """Gera os campos para as questões baseado no tipo e quantidade"""
            try:
                num_questoes = int(entry_num_questoes.get().strip())
                if num_questoes <= 0:
                    messagebox.showerror("❌ Erro", "Número de questões deve ser maior que zero.")
                    return
                
                tipo_atividade = tipo_var.get()
                limite_max = 50 if tipo_atividade == "Múltipla Escolha" else 20
                
                if num_questoes > limite_max:
                    messagebox.showerror("❌ Erro", f"Máximo de {limite_max} questões para {tipo_atividade}.")
                    return
                    
            except ValueError:
                messagebox.showerror("❌ Erro", "Digite um número válido de questões.")
                return

            # Limpar questões anteriores
            self._limpar_questoes_anteriores()
            
            # Gerar novas questões
            if tipo_atividade == "Múltipla Escolha":
                self._criar_questoes_multipla_escolha(num_questoes, scroll_questoes)
            else:  # Dissertativa
                self._criar_questoes_dissertativa(num_questoes, scroll_questoes)
            
            # Atualizar contador
            lbl_quantidade_atual.configure(text=f"📊 Questões criadas: {num_questoes}")
            
            messagebox.showinfo("✅ Sucesso", f"{num_questoes} questões do tipo '{tipo_atividade}' foram geradas com sucesso!")

        # Botão para gerar questões
        btn_gerar_questoes = customtkinter.CTkButton(
            controles_frame, 
            text="🚀 Gerar Questões",
            command=gerar_questoes,
            height=40,
            font=customtkinter.CTkFont(size=14, weight="bold"),
            fg_color=("#28a745", "#218838"),
            hover_color=("#218838", "#1e7e34")
        )
        btn_gerar_questoes.pack(side='right', padx=10)

        # Callback para mudança de tipo
        def on_tipo_change(choice):
            # Limpar questões ao mudar tipo
            if self._config_widgets['questoes_widgets']:
                if messagebox.askyesno("⚠️ Confirmar", "Trocar o tipo da atividade irá apagar todas as questões criadas. Deseja continuar?"):
                    self._limpar_questoes_anteriores()
                    entry_num_questoes.delete(0, 'end')
                    lbl_quantidade_atual.configure(text="📊 Questões criadas: 0")
                else:
                    # Reverter a seleção
                    tipo_combo.set("Múltipla Escolha" if choice == "Dissertativa" else "Dissertativa")
        
        tipo_combo.configure(command=on_tipo_change)

        # === RODAPÉ COM BOTÕES DE AÇÃO ===
        footer_frame = customtkinter.CTkFrame(dashboard_atividade, height=80)
        footer_frame.pack(fill='x', padx=20, pady=(0, 20))
        footer_frame.pack_propagate(False)

        # Container dos botões
        botoes_container = customtkinter.CTkFrame(footer_frame, fg_color="transparent")
        botoes_container.pack(expand=True, fill='both', padx=20, pady=15)
        botoes_container.grid_columnconfigure(0, weight=1)
        botoes_container.grid_columnconfigure(1, weight=1)
        botoes_container.grid_columnconfigure(2, weight=1)

        # Botão Voltar
        btn_voltar = customtkinter.CTkButton(
            botoes_container,
            text="⬅️ Voltar ao Painel",
            command=dashboard_atividade.destroy,
            height=50,
            font=customtkinter.CTkFont(size=14, weight="bold"),
            fg_color=("#6c757d", "#5a6268"),
            hover_color=("#5a6268", "#495057")
        )
        btn_voltar.grid(row=0, column=0, sticky='ew', padx=(0, 10))

        # Botão Cancelar
        btn_cancelar = customtkinter.CTkButton(
            botoes_container,
            text="❌ Cancelar",
            command=lambda: self._confirmar_cancelamento(dashboard_atividade),
            height=50,
            font=customtkinter.CTkFont(size=14, weight="bold"),
            fg_color=("#dc3545", "#c82333"),
            hover_color=("#c82333", "#a71e2a")
        )
        btn_cancelar.grid(row=0, column=1, sticky='ew', padx=5)

        # Botão Salvar Atividade
        btn_salvar = customtkinter.CTkButton(
            botoes_container,
            text="💾 Salvar Atividade",
            command=lambda: self._salvar_atividade_completa(
                entry_nome_atividade, entry_descricao_atividade, tipo_var, 
                entry_data_entrega, entry_pontuacao, status_var, 
                professor_login, dashboard_atividade
            ),
            height=50,
            font=customtkinter.CTkFont(size=14, weight="bold"),
            fg_color=("#28a745", "#218838"),
            hover_color=("#218838", "#1e7e34")
        )
        btn_salvar.grid(row=0, column=2, sticky='ew', padx=(10, 0))

    def _limpar_questoes_anteriores(self):
        """Limpa todas as questões anteriormente criadas"""
        if hasattr(self, '_config_widgets') and self._config_widgets.get('questoes_widgets'):
            # Destruir todos os widgets das questões
            for questao_data in self._config_widgets['questoes_widgets']:
                if 'frame' in questao_data and questao_data['frame'].winfo_exists():
                    questao_data['frame'].destroy()
            
            # Limpar lista
            self._config_widgets['questoes_widgets'].clear()
            
            # Remover instruções se existirem
            if 'instrucoes' in self._config_widgets and self._config_widgets['instrucoes'].winfo_exists():
                self._config_widgets['instrucoes'].destroy()

    def _criar_questoes_multipla_escolha(self, num_questoes, parent_scroll):
        """Cria interface para questões de múltipla escolha"""
        for i in range(num_questoes):
            # Frame principal da questão
            questao_frame = customtkinter.CTkFrame(parent_scroll)
            questao_frame.grid(row=i, column=0, padx=10, pady=15, sticky='ew')
            questao_frame.grid_columnconfigure(1, weight=1)
            
            # Cabeçalho da questão
            header_questao = customtkinter.CTkFrame(questao_frame)
            header_questao.grid(row=0, column=0, columnspan=2, sticky='ew', padx=10, pady=10)
            
            customtkinter.CTkLabel(
                header_questao, 
                text=f"❓ QUESTÃO {i+1}",
                font=customtkinter.CTkFont(size=16, weight="bold"),
                text_color=("#1f538d", "#3b8ed0")
            ).pack(pady=10)
            
            # Enunciado da questão
            customtkinter.CTkLabel(questao_frame, text="📝 Enunciado da Questão: *", 
                                  font=customtkinter.CTkFont(weight="bold")).grid(row=1, column=0, padx=10, pady=(10,5), sticky='nw')
            entry_questao = customtkinter.CTkTextbox(questao_frame, height=80)
            entry_questao.grid(row=1, column=1, padx=10, pady=(10,5), sticky='ew')
            entry_questao.insert("1.0", f"Digite aqui o enunciado da questão {i+1}...")
            
            # Frame para alternativas
            alt_frame = customtkinter.CTkFrame(questao_frame, fg_color="transparent")
            alt_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky='ew')
            alt_frame.grid_columnconfigure(1, weight=1)
            alt_frame.grid_columnconfigure(3, weight=1)
            
            customtkinter.CTkLabel(alt_frame, text="🔤 Alternativas: *", 
                                  font=customtkinter.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=4, pady=(0,10), sticky='w')
            
            # Criar 4 alternativas (A, B, C, D)
            alternativas_widgets = []
            for j in range(4):
                letra = chr(ord('A') + j)
                row_alt = (j // 2) + 1
                col_alt = (j % 2) * 2
                
                customtkinter.CTkLabel(alt_frame, text=f"{letra})", 
                                      font=customtkinter.CTkFont(weight="bold")).grid(row=row_alt, column=col_alt, padx=(0,5), pady=5, sticky='w')
                entry_alt = customtkinter.CTkEntry(alt_frame, placeholder_text=f"Alternativa {letra}")
                entry_alt.grid(row=row_alt, column=col_alt+1, padx=(0,20), pady=5, sticky='ew')
                alternativas_widgets.append(entry_alt)
            
            # Resposta correta
            resp_frame = customtkinter.CTkFrame(questao_frame, fg_color="transparent")
            resp_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky='ew')
            
            customtkinter.CTkLabel(resp_frame, text="✅ Resposta Correta: *", 
                                  font=customtkinter.CTkFont(weight="bold")).pack(side='left', padx=(0, 10))
            combo_resposta = customtkinter.CTkComboBox(resp_frame, values=["A", "B", "C", "D"], width=100, height=35)
            combo_resposta.pack(side='left')
            combo_resposta.set("A")
            
            # Validação visual
            status_frame = customtkinter.CTkFrame(questao_frame, fg_color="transparent")
            status_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=(0,10), sticky='ew')
            
            lbl_status = customtkinter.CTkLabel(status_frame, text="⏳ Aguardando preenchimento...", 
                                              font=customtkinter.CTkFont(size=11), text_color="orange")
            lbl_status.pack(side='left')
            
            # Salvar referências dos widgets
            questao_data = {
                'frame': questao_frame,
                'questao': entry_questao,
                'alternativas': alternativas_widgets,
                'resposta_correta': combo_resposta,
                'status_label': lbl_status,
                'numero': i + 1
            }
            
            self._config_widgets['questoes_widgets'].append(questao_data)
            
            # Configurar validação em tempo real
            self._configurar_validacao_multipla_escolha(questao_data)

    def _criar_questoes_dissertativa(self, num_questoes, parent_scroll):
        """Cria interface para questões dissertativas"""
        for i in range(num_questoes):
            # Frame principal da questão
            questao_frame = customtkinter.CTkFrame(parent_scroll)
            questao_frame.grid(row=i, column=0, padx=10, pady=15, sticky='ew')
            questao_frame.grid_columnconfigure(1, weight=1)
            
            # Cabeçalho da questão
            header_questao = customtkinter.CTkFrame(questao_frame)
            header_questao.grid(row=0, column=0, columnspan=2, sticky='ew', padx=10, pady=10)
            
            customtkinter.CTkLabel(
                header_questao, 
                text=f"📝 QUESTÃO DISSERTATIVA {i+1}",
                font=customtkinter.CTkFont(size=16, weight="bold"),
                text_color=("#1f538d", "#3b8ed0")
            ).pack(pady=10)
            
            # Enunciado da questão
            customtkinter.CTkLabel(questao_frame, text="❓ Enunciado da Questão: *", 
                                  font=customtkinter.CTkFont(weight="bold")).grid(row=1, column=0, padx=10, pady=(10,5), sticky='nw')
            entry_questao = customtkinter.CTkTextbox(questao_frame, height=100)
            entry_questao.grid(row=1, column=1, padx=10, pady=(10,5), sticky='ew')
            entry_questao.insert("1.0", f"Digite aqui o enunciado da questão dissertativa {i+1}...")
            
            # Critérios de avaliação
            customtkinter.CTkLabel(questao_frame, text="📋 Critérios de Avaliação:", 
                                  font=customtkinter.CTkFont(weight="bold")).grid(row=2, column=0, padx=10, pady=(15,5), sticky='nw')
            entry_criterios = customtkinter.CTkTextbox(questao_frame, height=80)
            entry_criterios.grid(row=2, column=1, padx=10, pady=(15,5), sticky='ew')
            entry_criterios.insert("1.0", "• Clareza e organização das ideias\n• Uso correto da linguagem\n• Fundamentação e argumentação\n• Criatividade e originalidade")
            
            # Peso da questão (para dissertativas)
            peso_frame = customtkinter.CTkFrame(questao_frame, fg_color="transparent")
            peso_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky='ew')
            
            customtkinter.CTkLabel(peso_frame, text="⚖️ Peso da Questão:", 
                                  font=customtkinter.CTkFont(weight="bold")).pack(side='left', padx=(0, 10))
            entry_peso = customtkinter.CTkEntry(peso_frame, placeholder_text="Ex: 2.0", width=100)
            entry_peso.pack(side='left', padx=(0, 20))
            entry_peso.insert(0, "1.0")
            
            # Validação visual
            status_frame = customtkinter.CTkFrame(questao_frame, fg_color="transparent")
            status_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=(0,10), sticky='ew')
            
            lbl_status = customtkinter.CTkLabel(status_frame, text="⏳ Aguardando preenchimento...", 
                                              font=customtkinter.CTkFont(size=11), text_color="orange")
            lbl_status.pack(side='left')
            
            # Salvar referências dos widgets
            questao_data = {
                'frame': questao_frame,
                'questao': entry_questao,
                'criterios': entry_criterios,
                'peso': entry_peso,
                'status_label': lbl_status,
                'numero': i + 1
            }
            
            self._config_widgets['questoes_widgets'].append(questao_data)
            
            # Configurar validação em tempo real
            self._configurar_validacao_dissertativa(questao_data)

    def _configurar_validacao_multipla_escolha(self, questao_data):
        """Configura validação em tempo real para questão de múltipla escolha"""
        def validar_questao():
            questao_texto = questao_data['questao'].get("1.0", "end-1c").strip()
            alternativas_preenchidas = all(alt.get().strip() for alt in questao_data['alternativas'])
            
            if questao_texto and alternativas_preenchidas:
                questao_data['status_label'].configure(
                    text="✅ Questão válida", 
                    text_color="green"
                )
                return True
            else:
                questao_data['status_label'].configure(
                    text="⚠️ Preencha todos os campos", 
                    text_color="orange"
                )
                return False
        
        # Bind para validação automática
        questao_data['questao'].bind('<KeyRelease>', lambda e: validar_questao())
        for alt_widget in questao_data['alternativas']:
            alt_widget.bind('<KeyRelease>', lambda e: validar_questao())

    def _configurar_validacao_dissertativa(self, questao_data):
        """Configura validação em tempo real para questão dissertativa"""
        def validar_questao():
            questao_texto = questao_data['questao'].get("1.0", "end-1c").strip()
            peso_texto = questao_data['peso'].get().strip()
            
            peso_valido = True
            try:
                if peso_texto:
                    peso_val = float(peso_texto)
                    peso_valido = peso_val > 0
            except ValueError:
                peso_valido = False
            
            if questao_texto and peso_valido:
                questao_data['status_label'].configure(
                    text="✅ Questão válida", 
                    text_color="green"
                )
                return True
            else:
                questao_data['status_label'].configure(
                    text="⚠️ Preencha o enunciado e peso válido", 
                    text_color="orange"
                )
                return False
        
        # Bind para validação automática
        questao_data['questao'].bind('<KeyRelease>', lambda e: validar_questao())
        questao_data['peso'].bind('<KeyRelease>', lambda e: validar_questao())

    def _confirmar_cancelamento(self, janela):
        """Confirma o cancelamento da criação da atividade"""
        if messagebox.askyesno("⚠️ Confirmar Cancelamento", 
                              "Tem certeza que deseja cancelar?\n\nTodos os dados preenchidos serão perdidos."):
            janela.destroy()

    def _salvar_atividade_completa(self, entry_nome, entry_descricao, tipo_var, entry_data, 
                                  entry_pontuacao, status_var, professor_login, janela):
        """Salva a atividade completa com validação abrangente"""
        
        # === VALIDAÇÃO DOS DADOS BÁSICOS ===
        nome_atividade = entry_nome.get().strip()
        descricao_atividade = entry_descricao.get("1.0", "end-1c").strip()
        tipo_atividade = tipo_var.get()
        data_entrega = entry_data.get().strip()
        pontuacao_texto = entry_pontuacao.get().strip()
        status = status_var.get()

        # Validar campos obrigatórios
        if not nome_atividade:
            messagebox.showerror("❌ Erro", "Nome da atividade é obrigatório.")
            entry_nome.focus()
            return
            
        if not descricao_atividade or descricao_atividade == "Descreva detalhadamente os objetivos e instruções desta atividade...":
            messagebox.showerror("❌ Erro", "Descrição da atividade é obrigatória.")
            entry_descricao.focus()
            return
            
        if not data_entrega:
            messagebox.showerror("❌ Erro", "Data de entrega é obrigatória.")
            entry_data.focus()
            return
            
        # Validar formato da data
        try:
            data_entrega_obj = datetime.strptime(data_entrega, '%d/%m/%Y')
        except ValueError:
            messagebox.showerror("❌ Erro", "Data deve estar no formato DD/MM/AAAA e conter apenas números válidos.")
            entry_data.focus()
            return
            
        # Validar se a data não é passada (deve ser hoje ou futura)
        data_atual = datetime.now()
        data_atual_sem_hora = data_atual.replace(hour=0, minute=0, second=0, microsecond=0)
        if data_entrega_obj < data_atual_sem_hora:
            messagebox.showerror("❌ Erro", "A data de entrega não pode ser anterior à data atual.")
            entry_data.focus()
            return
            
        # Validar pontuação
        try:
            pontuacao_float = float(pontuacao_texto)
            if pontuacao_float <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("❌ Erro", "Pontuação deve ser um número positivo.")
            entry_pontuacao.focus()
            return

        # === VALIDAÇÃO DAS QUESTÕES ===
        if not self._config_widgets.get('questoes_widgets'):
            messagebox.showerror("❌ Erro", "É necessário criar pelo menos uma questão.")
            return
            
        perguntas_data = []
        questoes_invalidas = []
        
        for questao_data in self._config_widgets['questoes_widgets']:
            numero_questao = questao_data['numero']
            
            if tipo_atividade == "Múltipla Escolha":
                # Validar questão de múltipla escolha
                questao_texto = questao_data['questao'].get("1.0", "end-1c").strip()
                if not questao_texto or questao_texto.startswith("Digite aqui o enunciado"):
                    questoes_invalidas.append(f"Questão {numero_questao}: Enunciado vazio")
                    continue
                
                alternativas_textos = []
                for j, alt_widget in enumerate(questao_data['alternativas']):
                    alt_texto = alt_widget.get().strip()
                    if not alt_texto:
                        questoes_invalidas.append(f"Questão {numero_questao}: Alternativa {chr(ord('A')+j)} vazia")
                        break
                    alternativas_textos.append(alt_texto)
                
                if len(alternativas_textos) != 4:
                    continue
                    
                resposta_correta = questao_data['resposta_correta'].get()
                
                pergunta_obj = {
                    "numero": numero_questao,
                    "tipo": "multipla_escolha",
                    "pergunta": questao_texto,
                    "alternativas": {
                        "A": alternativas_textos[0],
                        "B": alternativas_textos[1],
                        "C": alternativas_textos[2],
                        "D": alternativas_textos[3]
                    },
                    "resposta_correta": resposta_correta
                }
                perguntas_data.append(pergunta_obj)
                
            else:  # Dissertativa
                # Validar questão dissertativa
                questao_texto = questao_data['questao'].get("1.0", "end-1c").strip()
                if not questao_texto or questao_texto.startswith("Digite aqui o enunciado"):
                    questoes_invalidas.append(f"Questão {numero_questao}: Enunciado vazio")
                    continue
                
                criterios_texto = questao_data['criterios'].get("1.0", "end-1c").strip()
                peso_texto = questao_data['peso'].get().strip()
                
                try:
                    peso_val = float(peso_texto) if peso_texto else 1.0
                    if peso_val <= 0:
                        raise ValueError()
                except ValueError:
                    questoes_invalidas.append(f"Questão {numero_questao}: Peso inválido")
                    continue
                
                pergunta_obj = {
                    "numero": numero_questao,
                    "tipo": "dissertativa",
                    "pergunta": questao_texto,
                    "criterios": criterios_texto,
                    "peso": peso_val
                }
                perguntas_data.append(pergunta_obj)
        
        # Se há questões inválidas, mostrar erros
        if questoes_invalidas:
            erros_texto = "\n".join(questoes_invalidas)
            messagebox.showerror("❌ Questões Inválidas", f"Corrija os seguintes problemas:\n\n{erros_texto}")
            return
        
        if not perguntas_data:
            messagebox.showerror("❌ Erro", "Nenhuma questão válida encontrada.")
            return

        # === CONFIRMAÇÃO FINAL ===
        confirmacao_texto = f"""
🎯 CONFIRMAR CRIAÇÃO DA ATIVIDADE

📝 Nome: {nome_atividade}
📋 Tipo: {tipo_atividade}
📅 Data de Entrega: {data_entrega}
🏆 Pontuação: {pontuacao_float}
❓ Questões: {len(perguntas_data)}
🔓 Status: {status}

✅ Deseja confirmar a criação desta atividade?
        """
        
        if not messagebox.askyesno("🎯 Confirmar Atividade", confirmacao_texto):
            return

        # === SALVAR ATIVIDADE ===
        try:
            # Criar ID único para a atividade
            atividade_id = int(time.time() * 1000)

            nova_atividade = {
                "id": atividade_id,
                "nome": nome_atividade,
                "descricao": descricao_atividade,
                "tipo": tipo_atividade,
                "data_entrega": data_entrega,
                "pontuacao_maxima": pontuacao_float,
                "status": status,
                "professor_login": professor_login,
                "data_criacao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "quantidade_questoes": len(perguntas_data),
                "perguntas": perguntas_data
            }

            # Carregar e atualizar registros de aula
            registros = carregar_json(REGISTROS_AULA_FILE)
            
            # Encontrar e atualizar o registro correspondente
            registro_encontrado = False
            for i, registro in enumerate(registros):
                if (registro.get('materia_id') == self.registro_selecionado.get('materia_id') and
                    registro.get('professor_login') == self.registro_selecionado.get('professor_login') and
                    registro.get('data') == self.registro_selecionado.get('data') and
                    registro.get('nome_aula') == self.registro_selecionado.get('nome_aula')):
                    
                    # Inicializar lista de atividades se não existir
                    if 'atividades' not in registros[i]:
                        registros[i]['atividades'] = []
                    
                    # Adicionar nova atividade
                    registros[i]['atividades'].append(nova_atividade)
                    registro_encontrado = True
                    break

            if not registro_encontrado:
                messagebox.showerror("❌ Erro", "Registro de aula não encontrado. Operação cancelada.")
                return

            # Salvar alterações
            salvar_json(REGISTROS_AULA_FILE, registros)
            
            # Sucesso!
            messagebox.showinfo(
                "🎉 Atividade Criada!", 
                f"✅ Atividade '{nome_atividade}' criada com sucesso!\n\n"
                f"📊 Detalhes:\n"
                f"• Tipo: {tipo_atividade}\n"
                f"• Questões: {len(perguntas_data)}\n"
                f"• Status: {status}\n\n"
                f"A atividade foi salva no sistema e está disponível para os alunos."
            )
            
            # Fechar dashboard
            janela.destroy()
            
        except Exception as e:
            messagebox.showerror("❌ Erro", f"Erro ao salvar atividade: {str(e)}")


    def _criar_config_multipla_escolha(self, parent_frame):
        """Cria interface para configurar atividade de múltipla escolha"""
        customtkinter.CTkLabel(parent_frame, text="Configuração - Múltipla Escolha", 
                              font=customtkinter.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Número de perguntas
        customtkinter.CTkLabel(parent_frame, text="Número de Perguntas:").grid(row=1, column=0, padx=10, pady=5, sticky='w')
        entry_num_perguntas = customtkinter.CTkEntry(parent_frame, placeholder_text="Ex: 5", width=100)
        entry_num_perguntas.grid(row=1, column=1, padx=10, pady=5, sticky='w')
        self._config_widgets['num_perguntas'] = entry_num_perguntas
        
        # Frame scrollável para perguntas
        scroll_frame = customtkinter.CTkScrollableFrame(parent_frame, height=200)
        scroll_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky='ew')
        scroll_frame.grid_columnconfigure(0, weight=1)
        self._config_widgets['scroll_frame'] = scroll_frame
        self._config_widgets['perguntas_widgets'] = []
        
        def gerar_perguntas():
            try:
                num = int(entry_num_perguntas.get())
                if num <= 0 or num > 20:
                    messagebox.showerror("Erro", "Número de perguntas deve ser entre 1 e 20.")
                    return
            except ValueError:
                messagebox.showerror("Erro", "Digite um número válido de perguntas.")
                return
            
            # Limpar perguntas anteriores
            for widget_group in self._config_widgets['perguntas_widgets']:
                for widget in widget_group.values():
                    if hasattr(widget, 'destroy'):
                        widget.destroy()
            self._config_widgets['perguntas_widgets'].clear()
            
            # Criar campos para cada pergunta
            for i in range(num):
                pergunta_frame = customtkinter.CTkFrame(scroll_frame)
                pergunta_frame.grid(row=i, column=0, padx=5, pady=5, sticky='ew')
                pergunta_frame.grid_columnconfigure(1, weight=1)
                
                # Pergunta
                customtkinter.CTkLabel(pergunta_frame, text=f"Pergunta {i+1}:").grid(row=0, column=0, padx=5, pady=5, sticky='nw')
                entry_pergunta = customtkinter.CTkTextbox(pergunta_frame, height=60)
                entry_pergunta.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
                
                # Alternativas
                alternativas = []
                for j in range(4):  # 4 alternativas
                    letra = chr(ord('A') + j)
                    customtkinter.CTkLabel(pergunta_frame, text=f"Alternativa {letra}:").grid(row=j+1, column=0, padx=5, pady=2, sticky='w')
                    entry_alt = customtkinter.CTkEntry(pergunta_frame)
                    entry_alt.grid(row=j+1, column=1, padx=5, pady=2, sticky='ew')
                    alternativas.append(entry_alt)
                
                # Resposta correta
                customtkinter.CTkLabel(pergunta_frame, text="Resposta Correta:").grid(row=5, column=0, padx=5, pady=5, sticky='w')
                combo_resposta = customtkinter.CTkComboBox(pergunta_frame, values=["A", "B", "C", "D"], width=100)
                combo_resposta.grid(row=5, column=1, padx=5, pady=5, sticky='w')
                combo_resposta.set("A")
                
                widgets_pergunta = {
                    'frame': pergunta_frame,
                    'pergunta': entry_pergunta,
                    'alternativas': alternativas,
                    'resposta': combo_resposta
                }
                self._config_widgets['perguntas_widgets'].append(widgets_pergunta)
        
        btn_gerar = customtkinter.CTkButton(parent_frame, text="Gerar Campos de Perguntas", command=gerar_perguntas)
        btn_gerar.grid(row=3, column=0, columnspan=2, pady=10)

    def _criar_config_dissertativa(self, parent_frame):
        """Cria interface para configurar atividade dissertativa"""
        customtkinter.CTkLabel(parent_frame, text="Configuração - Dissertativa", 
                              font=customtkinter.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Número de perguntas
        customtkinter.CTkLabel(parent_frame, text="Número de Perguntas:").grid(row=1, column=0, padx=10, pady=5, sticky='w')
        entry_num_perguntas = customtkinter.CTkEntry(parent_frame, placeholder_text="Ex: 3", width=100)
        entry_num_perguntas.grid(row=1, column=1, padx=10, pady=5, sticky='w')
        self._config_widgets['num_perguntas'] = entry_num_perguntas
        
        # Frame scrollável para perguntas
        scroll_frame = customtkinter.CTkScrollableFrame(parent_frame, height=200)
        scroll_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky='ew')
        scroll_frame.grid_columnconfigure(0, weight=1)
        self._config_widgets['scroll_frame'] = scroll_frame
        self._config_widgets['perguntas_widgets'] = []
        
        def gerar_perguntas():
            try:
                num = int(entry_num_perguntas.get())
                if num <= 0 or num > 10:
                    messagebox.showerror("Erro", "Número de perguntas deve ser entre 1 e 10.")
                    return
            except ValueError:
                messagebox.showerror("Erro", "Digite um número válido de perguntas.")
                return
            
            # Limpar perguntas anteriores
            for widget_group in self._config_widgets['perguntas_widgets']:
                for widget in widget_group.values():
                    if hasattr(widget, 'destroy'):
                        widget.destroy()
            self._config_widgets['perguntas_widgets'].clear()
            
            # Criar campos para cada pergunta
            for i in range(num):
                pergunta_frame = customtkinter.CTkFrame(scroll_frame)
                pergunta_frame.grid(row=i, column=0, padx=5, pady=5, sticky='ew')
                pergunta_frame.grid_columnconfigure(1, weight=1)
                
                # Pergunta
                customtkinter.CTkLabel(pergunta_frame, text=f"Pergunta {i+1}:").grid(row=0, column=0, padx=5, pady=5, sticky='nw')
                entry_pergunta = customtkinter.CTkTextbox(pergunta_frame, height=80)
                entry_pergunta.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
                
                # Critérios de avaliação (opcional)
                customtkinter.CTkLabel(pergunta_frame, text="Critérios de Avaliação:").grid(row=1, column=0, padx=5, pady=5, sticky='nw')
                entry_criterios = customtkinter.CTkTextbox(pergunta_frame, height=60)
                entry_criterios.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
                entry_criterios.insert("1.0", "Clareza, organização das ideias, uso correto da linguagem...")
                
                widgets_pergunta = {
                    'frame': pergunta_frame,
                    'pergunta': entry_pergunta,
                    'criterios': entry_criterios
                }
                self._config_widgets['perguntas_widgets'].append(widgets_pergunta)
        
        btn_gerar = customtkinter.CTkButton(parent_frame, text="Gerar Campos de Perguntas", command=gerar_perguntas)
        btn_gerar.grid(row=3, column=0, columnspan=2, pady=10)

    def _coletar_dados_multipla_escolha(self):
        """Coleta dados das perguntas de múltipla escolha"""
        if not self._config_widgets.get('perguntas_widgets'):
            messagebox.showerror("Erro", "Gere os campos de perguntas primeiro.")
            return None
        
        perguntas = []
        for i, widgets in enumerate(self._config_widgets['perguntas_widgets']):
            pergunta_texto = widgets['pergunta'].get("1.0", "end-1c").strip()
            if not pergunta_texto:
                messagebox.showerror("Erro", f"Pergunta {i+1} não pode estar vazia.")
                return None
            
            alternativas = []
            for j, alt_widget in enumerate(widgets['alternativas']):
                alt_texto = alt_widget.get().strip()
                if not alt_texto:
                    letra = chr(ord('A') + j)
                    messagebox.showerror("Erro", f"Alternativa {letra} da pergunta {i+1} não pode estar vazia.")
                    return None
                alternativas.append(alt_texto)
            
            resposta_correta = widgets['resposta'].get()
            
            pergunta_data = {
                "pergunta": pergunta_texto,
                "alternativas": {
                    "A": alternativas[0],
                    "B": alternativas[1],
                    "C": alternativas[2],
                    "D": alternativas[3]
                },
                "resposta_correta": resposta_correta
            }
            perguntas.append(pergunta_data)
        
        return perguntas

    def _coletar_dados_dissertativa(self):
        """Coleta dados das perguntas dissertativas"""
        if not self._config_widgets.get('perguntas_widgets'):
            messagebox.showerror("Erro", "Gere os campos de perguntas primeiro.")
            return None
        
        perguntas = []
        for i, widgets in enumerate(self._config_widgets['perguntas_widgets']):
            pergunta_texto = widgets['pergunta'].get("1.0", "end-1c").strip()
            if not pergunta_texto:
                messagebox.showerror("Erro", f"Pergunta {i+1} não pode estar vazia.")
                return None
            
            criterios = widgets['criterios'].get("1.0", "end-1c").strip()
            
            pergunta_data = {
                "pergunta": pergunta_texto,
                "criterios": criterios
            }
            perguntas.append(pergunta_data)
        
        return perguntas

    def _gerenciar_atividades_registro(self, professor_login):
        """Abre janela para gerenciar atividades do registro selecionado"""
        if not hasattr(self, 'registro_selecionado') or not self.registro_selecionado:
            messagebox.showerror("Erro", "Por favor, selecione um registro de aula primeiro.")
            return

        # Verificar se há atividades
        atividades = self.registro_selecionado.get('atividades', [])
        if not atividades:
            messagebox.showinfo("Informação", "Este registro de aula não possui atividades criadas.")
            return

        # Criar nova janela
        janela_gerenciar = customtkinter.CTkToplevel(self)
        janela_gerenciar.title("Gerenciar Atividades")
        janela_gerenciar.geometry("700x500")
        janela_gerenciar.transient(self)
        janela_gerenciar.grab_set()

        # Informações do registro selecionado
        info_frame = customtkinter.CTkFrame(janela_gerenciar)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        customtkinter.CTkLabel(info_frame, text=f"Registro: {self.registro_selecionado.get('nome_aula', '')}", 
                              font=customtkinter.CTkFont(weight="bold", size=16)).pack(pady=5)
        customtkinter.CTkLabel(info_frame, text=f"Data: {self.registro_selecionado.get('data', '')}").pack()

        # Tabela de atividades
        tree_frame = customtkinter.CTkFrame(janela_gerenciar)
        tree_frame.pack(fill='both', expand=True, padx=20, pady=10)

        tree_atividades = ttk.Treeview(tree_frame, columns=('nome', 'data_entrega', 'pontuacao', 'status'), show='headings')
        tree_atividades.heading('nome', text='Nome da Atividade')
        tree_atividades.column('nome', width=200)
        tree_atividades.heading('data_entrega', text='Data de Entrega')
        tree_atividades.column('data_entrega', width=120, anchor='center')
        tree_atividades.heading('pontuacao', text='Pontuação Máx.')
        tree_atividades.column('pontuacao', width=100, anchor='center')
        tree_atividades.heading('status', text='Status')
        tree_atividades.column('status', width=120, anchor='center')
        
        tree_atividades.pack(fill='both', expand=True, padx=10, pady=10)

        def carregar_atividades():
            """Carrega atividades na tabela"""
            for item in tree_atividades.get_children():
                tree_atividades.delete(item)
            
            atividades = self.registro_selecionado.get('atividades', [])
            for i, atividade in enumerate(atividades):
                tree_atividades.insert('', 'end', values=(
                    atividade.get('nome', ''),
                    atividade.get('data_entrega', ''),
                    f"{atividade.get('pontuacao_maxima', 0):.1f}",
                    atividade.get('status', 'Não Liberada')
                ), tags=(f"atividade_{i}",))

        carregar_atividades()

        # Botões de ação
        btn_frame = customtkinter.CTkFrame(janela_gerenciar)
        btn_frame.pack(fill='x', padx=20, pady=10)

        def liberar_atividade():
            """Libera a atividade selecionada para a turma"""
            alterar_status_atividade("Liberada")

        def bloquear_atividade():
            """Bloqueia a atividade selecionada"""
            alterar_status_atividade("Não Liberada")

        def alterar_status_atividade(novo_status):
            """Altera o status da atividade selecionada"""
            selection = tree_atividades.selection()
            if not selection:
                messagebox.showwarning("Aviso", "Por favor, selecione uma atividade.")
                return
            
            item = tree_atividades.item(selection[0])
            tags = item.get('tags', [])
            if not tags:
                messagebox.showerror("Erro", "Erro ao identificar a atividade.")
                return
            
            # Extrair índice da atividade
            tag = tags[0]
            if tag.startswith('atividade_'):
                atividade_index = int(tag.split('_')[1])
                
                # Carregar registros de aula
                registros = carregar_json(REGISTROS_AULA_FILE)
                
                # Encontrar e atualizar o registro correspondente
                for i, registro in enumerate(registros):
                    if (registro.get('materia_id') == self.registro_selecionado.get('materia_id') and
                        registro.get('professor_login') == self.registro_selecionado.get('professor_login') and
                        registro.get('data') == self.registro_selecionado.get('data') and
                        registro.get('nome_aula') == self.registro_selecionado.get('nome_aula')):
                        
                        # Atualizar status da atividade
                        if atividade_index < len(registro.get('atividades', [])):
                            registros[i]['atividades'][atividade_index]['status'] = novo_status
                            
                            # Salvar alterações
                            salvar_json(REGISTROS_AULA_FILE, registros)
                            
                            # Atualizar registro selecionado em memória
                            self.registro_selecionado = registros[i]
                            
                            # Recarregar tabela
                            carregar_atividades()
                            
                            action_text = "liberada" if novo_status == "Liberada" else "bloqueada"
                            messagebox.showinfo("Sucesso", f"Atividade {action_text} com sucesso!")
                            return
                
                messagebox.showerror("Erro", "Erro ao atualizar a atividade.")

        def excluir_atividade():
            """Exclui a atividade selecionada"""
            selection = tree_atividades.selection()
            if not selection:
                messagebox.showwarning("Aviso", "Por favor, selecione uma atividade.")
                return
            
            item = tree_atividades.item(selection[0])
            nome_atividade = item['values'][0]
            
            if not messagebox.askyesno("Confirmar", f"Deseja realmente excluir a atividade '{nome_atividade}'?"):
                return
            
            tags = item.get('tags', [])
            if not tags:
                messagebox.showerror("Erro", "Erro ao identificar a atividade.")
                return
            
            # Extrair índice da atividade
            tag = tags[0]
            if tag.startswith('atividade_'):
                atividade_index = int(tag.split('_')[1])
                
                # Carregar registros de aula
                registros = carregar_json(REGISTROS_AULA_FILE)
                
                # Encontrar e atualizar o registro correspondente
                for i, registro in enumerate(registros):
                    if (registro.get('materia_id') == self.registro_selecionado.get('materia_id') and
                        registro.get('professor_login') == self.registro_selecionado.get('professor_login') and
                        registro.get('data') == self.registro_selecionado.get('data') and
                        registro.get('nome_aula') == self.registro_selecionado.get('nome_aula')):
                        
                        # Remover atividade
                        if atividade_index < len(registro.get('atividades', [])):
                            del registros[i]['atividades'][atividade_index]
                            
                            # Salvar alterações
                            salvar_json(REGISTROS_AULA_FILE, registros)
                            
                            # Atualizar registro selecionado em memória
                            self.registro_selecionado = registros[i]
                            
                            # Recarregar tabela
                            carregar_atividades()
                            
                            messagebox.showinfo("Sucesso", "Atividade excluída com sucesso!")
                            return
                
                messagebox.showerror("Erro", "Erro ao excluir a atividade.")

        # Adicionar botões
        customtkinter.CTkButton(btn_frame, text="Liberar Atividade", command=liberar_atividade,
                               fg_color="green", hover_color="darkgreen").pack(side='left', padx=5)
        customtkinter.CTkButton(btn_frame, text="Bloquear Atividade", command=bloquear_atividade,
                               fg_color="orange", hover_color="darkorange").pack(side='left', padx=5)
        customtkinter.CTkButton(btn_frame, text="Excluir Atividade", command=excluir_atividade,
                               fg_color="red", hover_color="darkred").pack(side='left', padx=5)
        customtkinter.CTkButton(btn_frame, text="Fechar", command=janela_gerenciar.destroy).pack(side='right', padx=5)

    def _criar_aba_lancamento_notas(self, parent_tab, materias_prof, user_login):
        # --- Frame de Seleção ---
        top_frame = customtkinter.CTkFrame(parent_tab)
        top_frame.pack(fill='x', padx=10, pady=10)
        top_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(top_frame, text="Matéria:").grid(row=0, column=0, padx=10, pady=(10,0), sticky='w')
        # Obter informações das turmas para mostrar série e turma
        turmas = carregar_json(TURMAS_FILE)
        turma_info = {t['id']: f"{t.get('serie', '')} - {t.get('turma', '')}" for t in turmas}
        mapa_materias_prof = {f"{m['nome']} ({turma_info.get(m.get('turma_id'), 'N/A')})": m['id'] for m in materias_prof}
        combo_materias = customtkinter.CTkComboBox(top_frame, values=["Selecione uma matéria"] + list(mapa_materias_prof.keys()))
        combo_materias.grid(row=0, column=1, padx=10, pady=(10,0), sticky='ew')
        combo_materias.set("Selecione uma matéria")

        customtkinter.CTkLabel(top_frame, text="Bimestre:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        bimestre_var = tk.StringVar(value="1º Bimestre")
        segmented_bimestre = customtkinter.CTkSegmentedButton(top_frame, values=["1º Bimestre", "2º Bimestre", "3º Bimestre", "4º Bimestre"], variable=bimestre_var)
        segmented_bimestre.grid(row=1, column=1, padx=10, pady=10, sticky='w')

        # --- Frame de Alunos e Ações ---
        content_frame = customtkinter.CTkFrame(parent_tab)
        content_frame.pack(fill='both', expand=True, padx=10, pady=(0,10))
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        tree_alunos = ttk.Treeview(content_frame, columns=('ra', 'nome', 'np1', 'np2', 'media_bim'), show='headings')
        tree_alunos.heading('ra', text='RA')
        tree_alunos.column('ra', width=100)
        tree_alunos.heading('nome', text='Nome do Aluno')
        tree_alunos.column('nome', width=250)
        tree_alunos.heading('np1', text='NP1')
        tree_alunos.column('np1', width=80, anchor='center')
        tree_alunos.heading('np2', text='NP2')
        tree_alunos.column('np2', width=80, anchor='center')
        tree_alunos.heading('media_bim', text='Média Bimestre')
        tree_alunos.column('media_bim', width=100, anchor='center')
        tree_alunos.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        # --- Botões de Ação ---
        action_frame = customtkinter.CTkFrame(content_frame)
        action_frame.grid(row=0, column=1, sticky='ns', padx=5, pady=5)

        btn_lancar_np1 = customtkinter.CTkButton(action_frame, text="Lançar/Alterar NP1", state="disabled")
        btn_lancar_np1.pack(pady=5, padx=5, fill='x')
        btn_lancar_np2 = customtkinter.CTkButton(action_frame, text="Lançar/Alterar NP2", state="disabled")
        btn_lancar_np2.pack(pady=5, padx=5, fill='x')

        def get_bimestre_prefix():
            map_bimestre = {"1º Bimestre": "B1", "2º Bimestre": "B2", "3º Bimestre": "B3", "4º Bimestre": "B4"}
            return map_bimestre.get(bimestre_var.get())

        def refresh_lista_alunos():
            for i in tree_alunos.get_children(): tree_alunos.delete(i)
            
            materia_id = mapa_materias_prof.get(combo_materias.get())
            if not materia_id: return

            bimestre_prefix = get_bimestre_prefix()
            if not bimestre_prefix: return

            todas_materias = carregar_json(MATERIAS_FILE)
            materia_sel = next((m for m in todas_materias if m['id'] == materia_id), None)
            if not materia_sel: return

            turmas = carregar_json(TURMAS_FILE)
            turma_correta = next((t for t in turmas if t.get('id') == materia_sel.get('turma_id')), None)
            if not turma_correta: return

            usuarios = carregar_json(ALUNOS_FILE)  # Buscar apenas alunos
            notas = carregar_json(NOTAS_FILE)

            for ra_aluno in sorted(turma_correta.get('alunos', [])):
                aluno_info = next((u for u in usuarios if u.get('ra') == ra_aluno), None)
                if not aluno_info: continue

                nota_np1_obj = next((n for n in notas if n.get('aluno_ra') == ra_aluno and n.get('materia_id') == materia_id and n.get('tipo_nota') == f"{bimestre_prefix}_NP1"), None)
                nota_np2_obj = next((n for n in notas if n.get('aluno_ra') == ra_aluno and n.get('materia_id') == materia_id and n.get('tipo_nota') == f"{bimestre_prefix}_NP2"), None)
                
                val_np1 = nota_np1_obj.get('valor') if nota_np1_obj else "N/L"
                val_np2 = nota_np2_obj.get('valor') if nota_np2_obj else "N/L"
                
                media_bim = "N/A"
                if isinstance(val_np1, (int, float)) and isinstance(val_np2, (int, float)):
                    media_bim = f"{(val_np1 + val_np2) / 2:.2f}"

                tree_alunos.insert('', 'end', iid=ra_aluno, values=(ra_aluno, aluno_info.get('nome', ''), val_np1, val_np2, media_bim))

        def on_selection_change(event=None):
            materia_id = mapa_materias_prof.get(combo_materias.get())
            if materia_id:
                btn_lancar_np1.configure(state="normal")
                btn_lancar_np2.configure(state="normal")
                refresh_lista_alunos()
            else:
                btn_lancar_np1.configure(state="disabled")
                btn_lancar_np2.configure(state="disabled")
                for i in tree_alunos.get_children(): tree_alunos.delete(i)

        def lancar_nota_action(tipo_prova): # tipo_prova será "NP1" ou "NP2"
            sel = tree_alunos.selection()
            if not sel:
                messagebox.showwarning("Aviso", "Selecione um aluno da lista.")
                return
            ra_aluno = sel[0]
            materia_id = mapa_materias_prof.get(combo_materias.get())
            bimestre_prefix = get_bimestre_prefix()
            tipo_nota_completo = f"{bimestre_prefix}_{tipo_prova}"

            nota_atual_str = simpledialog.askstring("Lançar Nota", f"Digite a nota de {tipo_prova} ({bimestre_var.get()}) para o aluno (RA: {ra_aluno}):", parent=parent_tab)
            if nota_atual_str is None: return

            try:
                nota_valor = float(nota_atual_str.replace(',', '.'))
                if not (0 <= nota_valor <= 10):
                    raise ValueError("Nota fora do intervalo 0-10")
            except (ValueError, TypeError):
                messagebox.showerror("Erro", "Valor da nota inválido. Use um número entre 0 e 10.")
                return

            notas = carregar_json(NOTAS_FILE)
            nota_existente = next((n for n in notas if n.get('aluno_ra') == ra_aluno and n.get('materia_id') == materia_id and n.get('tipo_nota') == tipo_nota_completo), None)

            if nota_existente:
                nota_existente['valor'] = nota_valor
            else:
                notas.append({
                    "aluno_ra": ra_aluno, "materia_id": materia_id,
                    "tipo_nota": tipo_nota_completo, "valor": nota_valor,
                    "professor_login": user_login
                })
            
            salvar_json(NOTAS_FILE, notas)
            refresh_lista_alunos()

        combo_materias.configure(command=on_selection_change)
        segmented_bimestre.configure(command=lambda e: on_selection_change())
        btn_lancar_np1.configure(command=lambda: lancar_nota_action("NP1"))
        btn_lancar_np2.configure(command=lambda: lancar_nota_action("NP2"))

    def _visualizar_alunos_materia(self, tree_materias):
        sel = tree_materias.selection()
        if not sel:
            messagebox.showwarning('Erro', 'Selecione uma matéria para visualizar os alunos.')
            return
        
        # Extrair dados da matéria selecionada
        values = tree_materias.item(sel[0])['values']
        nome_materia = values[0]
        
        # Buscar matéria pelo nome (usando materias_prof que já está filtrada)
        materias_prof = carregar_json(MATERIAS_FILE)
        user_login = self.user_info.get('login')
        materias_prof = [m for m in materias_prof if m.get('professor_login') == user_login]
        
        materia_selecionada = next((m for m in materias_prof if m['nome'] == nome_materia), None)
        
        if not materia_selecionada:
            messagebox.showerror('Erro', 'Matéria não encontrada.')
            return

        # Criar nova janela principal (dashboard da matéria)
        dashboard_materia = customtkinter.CTkToplevel(self)
        
        # Buscar informações da turma
        turmas = carregar_json(TURMAS_FILE)
        turma_info = next((t for t in turmas if t.get('id') == materia_selecionada.get('turma_id')), {})
        serie_turma = f"{turma_info.get('serie', 'N/A')} - {turma_info.get('turma', 'N/A')}"
        
        dashboard_materia.title(f"📚 Dashboard - {materia_selecionada['nome']} ({serie_turma})")
        dashboard_materia.geometry('1200x800')
        dashboard_materia.resizable(True, True)
        dashboard_materia.transient(self)

        # Criar abas dentro da dashboard da matéria
        tabs_materia = customtkinter.CTkTabview(dashboard_materia)
        tabs_materia.pack(expand=True, fill='both', padx=10, pady=10)

        # ================= ABA: ALUNOS E NOTAS =================
        aba_alunos_notas = tabs_materia.add('👥 Alunos e Notas')
        self._criar_aba_alunos_notas(aba_alunos_notas, materia_selecionada)

        # ================= BOTÃO VOLTAR =================
        frame_botoes = customtkinter.CTkFrame(dashboard_materia, height=60)
        frame_botoes.pack(fill='x', padx=10, pady=(0, 10))
        frame_botoes.pack_propagate(False)

        btn_voltar = customtkinter.CTkButton(
            frame_botoes, 
            text="⬅️ Voltar ao Painel do Professor",
            command=dashboard_materia.destroy,
            font=customtkinter.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color=("#3b8ed0", "#1e6091"),
            hover_color=("#2e6da4", "#17537a")
        )
        btn_voltar.pack(side='left', padx=10, pady=10)

        # Informações da matéria no rodapé
        info_label = customtkinter.CTkLabel(
            frame_botoes, 
            text=f"📖 Matéria: {materia_selecionada['nome']} | 🎓 Turma: {serie_turma}",
            font=customtkinter.CTkFont(size=12),
            text_color="gray"
        )
        info_label.pack(side='right', padx=10, pady=10)

    def _criar_aba_alunos_notas(self, parent_tab, materia_selecionada):
        """Cria a aba com informações gerais dos alunos (apenas quantidade)"""
        # Cabeçalho da aba
        header_frame = customtkinter.CTkFrame(parent_tab, height=80)
        header_frame.pack(fill='x', padx=10, pady=10)
        header_frame.pack_propagate(False)

        customtkinter.CTkLabel(
            header_frame, 
            text=f"� Alunos da Matéria: {materia_selecionada['nome']}",
            font=customtkinter.CTkFont(size=18, weight="bold")
        ).pack(expand=True)

        # Frame para mostrar informações gerais
        info_frame = customtkinter.CTkFrame(parent_tab)
        info_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Calcular quantidade de alunos
        turmas = carregar_json(TURMAS_FILE)
        usuarios = carregar_json(ALUNOS_FILE)
        
        # Encontrar a turma correspondente
        turma_correta = next((t for t in turmas if t.get('id') == materia_selecionada.get('turma_id')), None)
        
        # Definir informações da turma para exibição
        serie_turma = f"{turma_correta.get('serie', 'N/A')} - {turma_correta.get('turma', 'N/A')}" if turma_correta else 'N/A'
        
        if not turma_correta:
            customtkinter.CTkLabel(
                info_frame,
                text="❌ Nenhuma turma encontrada para esta matéria",
                font=customtkinter.CTkFont(size=16)
            ).pack(expand=True)
            return

        # Contar alunos válidos
        alunos_validos = []
        for ra_aluno in turma_correta.get('alunos', []):
            aluno_info = next((u for u in usuarios if u.get('ra') == ra_aluno), None)
            if aluno_info:
                alunos_validos.append(aluno_info)

        quantidade_alunos = len(alunos_validos)

        # Mostrar informações gerais
        info_container = customtkinter.CTkFrame(info_frame, fg_color="transparent")
        info_container.pack(expand=True)

        customtkinter.CTkLabel(
            info_container,
            text=f"� Resumo da Turma",
            font=customtkinter.CTkFont(size=20, weight="bold")
        ).pack(pady=(50, 20))

        customtkinter.CTkLabel(
            info_container,
            text=f"Série/Turma: {serie_turma}",
            font=customtkinter.CTkFont(size=14)
        ).pack(pady=5)

        customtkinter.CTkLabel(
            info_container,
            text=f"👥 Total de Alunos: {quantidade_alunos}",
            font=customtkinter.CTkFont(size=16, weight="bold"),
            text_color=("#2e7d32", "#4caf50")
        ).pack(pady=10)

        if quantidade_alunos > 0:
            customtkinter.CTkLabel(
                info_container,
                text="ℹ️ Para gerenciar notas e ver detalhes dos alunos,\nacesse a aba 'Lançar Notas' no painel principal",
                font=customtkinter.CTkFont(size=12),
                text_color="gray",
                justify="center"
            ).pack(pady=(20, 50))

    def _abrir_janela_notas_aluno_especifico(self, ra_aluno, nome_aluno, materia_selecionada, callback_refresh=None):
        """Abre janela específica para lançar notas de um aluno"""
        janela_notas = customtkinter.CTkToplevel(self)
        janela_notas.title(f"📝 Lançar Notas - {nome_aluno}")
        janela_notas.geometry("800x600")
        janela_notas.transient(self)
        janela_notas.grab_set()

        # Cabeçalho
        header_frame = customtkinter.CTkFrame(janela_notas, height=80)
        header_frame.pack(fill='x', padx=20, pady=20)
        header_frame.pack_propagate(False)

        # Buscar informações da turma
        turmas = carregar_json(TURMAS_FILE)
        turma_info = next((t for t in turmas if t.get('id') == materia_selecionada.get('turma_id')), {})
        serie_turma_label = f"{turma_info.get('serie', 'N/A')} {turma_info.get('turma', 'N/A')}"
        
        customtkinter.CTkLabel(
            header_frame, 
            text=f"📚 {materia_selecionada['nome']} - {serie_turma_label}",
            font=customtkinter.CTkFont(size=16, weight="bold")
        ).pack()

        customtkinter.CTkLabel(
            header_frame, 
            text=f"👤 Aluno: {nome_aluno} (RA: {ra_aluno})",
            font=customtkinter.CTkFont(size=14)
        ).pack()

        # Frame principal com scroll
        main_frame = customtkinter.CTkScrollableFrame(janela_notas)
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Carregar notas existentes
        notas_db = carregar_json(NOTAS_FILE)
        materia_id = materia_selecionada['id']

        # Widgets para entrada de notas
        widgets_notas = {}

        # Criar seções para cada bimestre
        for i, bim in enumerate(['1º Bimestre', '2º Bimestre', '3º Bimestre', '4º Bimestre']):
            bim_prefix = f'B{i+1}'
            
            # Frame do bimestre
            bim_frame = customtkinter.CTkFrame(main_frame)
            bim_frame.pack(fill='x', pady=(0, 15))
            bim_frame.grid_columnconfigure(1, weight=1)
            bim_frame.grid_columnconfigure(3, weight=1)

            # Título do bimestre
            customtkinter.CTkLabel(
                bim_frame, 
                text=f"📊 {bim}",
                font=customtkinter.CTkFont(size=14, weight="bold"),
                text_color=("#1f538d", "#3b8ed0")
            ).grid(row=0, column=0, columnspan=4, pady=(15, 10), padx=20, sticky='w')

            # NP1
            customtkinter.CTkLabel(bim_frame, text="NP1:").grid(row=1, column=0, padx=(20, 10), pady=5, sticky='w')
            entry_np1 = customtkinter.CTkEntry(bim_frame, placeholder_text="0.0 a 10.0", width=100)
            entry_np1.grid(row=1, column=1, padx=10, pady=5, sticky='w')

            # NP2
            customtkinter.CTkLabel(bim_frame, text="NP2:").grid(row=1, column=2, padx=10, pady=5, sticky='w')
            entry_np2 = customtkinter.CTkEntry(bim_frame, placeholder_text="0.0 a 10.0", width=100)
            entry_np2.grid(row=1, column=3, padx=(10, 20), pady=5, sticky='w')

            # Média calculada
            label_media = customtkinter.CTkLabel(bim_frame, text="Média: N/A", 
                                               font=customtkinter.CTkFont(weight="bold"))
            label_media.grid(row=2, column=0, columnspan=4, pady=(5, 15), padx=20, sticky='w')

            # Salvar referências
            widgets_notas[bim_prefix] = {
                'np1': entry_np1,
                'np2': entry_np2,
                'media': label_media
            }

            # Carregar notas existentes
            nota_np1_obj = next((n for n in notas_db if 
                               n.get('aluno_ra') == ra_aluno and 
                               n.get('materia_id') == materia_id and 
                               n.get('tipo_nota') == f"{bim_prefix}_NP1"), None)
            
            nota_np2_obj = next((n for n in notas_db if 
                               n.get('aluno_ra') == ra_aluno and 
                               n.get('materia_id') == materia_id and 
                               n.get('tipo_nota') == f"{bim_prefix}_NP2"), None)

            if nota_np1_obj and isinstance(nota_np1_obj.get('valor'), (int, float)):
                entry_np1.insert(0, str(nota_np1_obj['valor']))
            
            if nota_np2_obj and isinstance(nota_np2_obj.get('valor'), (int, float)):
                entry_np2.insert(0, str(nota_np2_obj['valor']))

            # Função para atualizar média
            def atualizar_media(bim_prefix=bim_prefix):
                try:
                    np1_val = float(widgets_notas[bim_prefix]['np1'].get() or 0)
                    np2_val = float(widgets_notas[bim_prefix]['np2'].get() or 0)
                    media = (np1_val + np2_val) / 2
                    widgets_notas[bim_prefix]['media'].configure(text=f"Média: {media:.1f}")
                except ValueError:
                    widgets_notas[bim_prefix]['media'].configure(text="Média: N/A")

            # Bind para atualizar média automaticamente
            entry_np1.bind('<KeyRelease>', lambda e, bp=bim_prefix: atualizar_media(bp))
            entry_np2.bind('<KeyRelease>', lambda e, bp=bim_prefix: atualizar_media(bp))
            
            # Atualizar média inicial
            atualizar_media(bim_prefix)

        def salvar_notas():
            """Salva todas as notas do aluno"""
            notas_atualizadas = []
            
            for i, bim_prefix in enumerate(['B1', 'B2', 'B3', 'B4']):
                np1_text = widgets_notas[bim_prefix]['np1'].get().strip()
                np2_text = widgets_notas[bim_prefix]['np2'].get().strip()

                # Validar e converter notas
                for tipo_nota, valor_text in [('NP1', np1_text), ('NP2', np2_text)]:
                    if valor_text:  # Se campo não está vazio
                        try:
                            valor = float(valor_text)
                            if valor < 0 or valor > 10:
                                messagebox.showerror("Erro", f"Nota {tipo_nota} do {bim_prefix} deve estar entre 0 e 10.")
                                return
                            
                            nota_obj = {
                                'aluno_ra': ra_aluno,
                                'materia_id': materia_id,
                                'tipo_nota': f"{bim_prefix}_{tipo_nota}",
                                'valor': valor,
                                'professor': self.usuario_logado['usuario'],
                                'data_lancamento': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                            }
                            notas_atualizadas.append(nota_obj)
                        except ValueError:
                            messagebox.showerror("Erro", f"Valor inválido para {tipo_nota} do {bim_prefix}.")
                            return

            if not notas_atualizadas:
                messagebox.showwarning("Aviso", "Nenhuma nota foi preenchida.")
                return

            # Carregar notas existentes e atualizar
            notas_db = carregar_json(NOTAS_FILE)
            
            # Remover notas antigas deste aluno/matéria
            notas_db = [n for n in notas_db if not (
                n.get('aluno_ra') == ra_aluno and 
                n.get('materia_id') == materia_id
            )]
            
            # Adicionar novas notas
            notas_db.extend(notas_atualizadas)
            
            # Salvar
            salvar_json(NOTAS_FILE, notas_db)
            
            messagebox.showinfo("Sucesso", f"Notas de {nome_aluno} salvas com sucesso!")
            
            # Callback para refresh
            if callback_refresh:
                callback_refresh()
            
            janela_notas.destroy()

        # Botões
        botoes_frame = customtkinter.CTkFrame(janela_notas, height=60)
        botoes_frame.pack(fill='x', padx=20, pady=20)
        botoes_frame.pack_propagate(False)

        customtkinter.CTkButton(
            botoes_frame, 
            text="❌ Cancelar",
            command=janela_notas.destroy,
            height=40,
            fg_color=("#dc3545", "#c82333"),
            hover_color=("#c82333", "#a71e2a")
        ).pack(side='left', padx=10, pady=10)

        customtkinter.CTkButton(
            botoes_frame, 
            text="💾 Salvar Notas",
            command=salvar_notas,
            height=40,
            font=customtkinter.CTkFont(weight="bold"),
            fg_color=("#28a745", "#218838"),
            hover_color=("#218838", "#1e7e34")
        ).pack(side='right', padx=10, pady=10)

    # FUNÇÃO _criar_aba_noticias REMOVIDA - Sistema de notícias desativado
    
    def _formatar_detalhes_pedido(self, pedido):
        """Formata os detalhes do pedido de forma organizada e indentada"""
        try:
            # Verificar se é o formato novo (com dados estruturados)
            if 'dados_aluno' in pedido and 'dados_responsavel' in pedido:
                dados_aluno = pedido.get('dados_aluno', {})
                dados_responsavel = pedido.get('dados_responsavel', {})
                endereco = pedido.get('endereco', {})
                
                detalhes = f"""📋 PROTOCOLO: {pedido.get('id', 'N/A'):06d}
📅 DATA DA SOLICITAÇÃO: {pedido.get('data', 'N/A')}
📊 STATUS: {pedido.get('status', 'N/A')}

👨‍🎓 DADOS DO ALUNO
    Nome Completo: {dados_aluno.get('nome', 'N/A')}
    Data de Nascimento: {dados_aluno.get('data_nascimento', 'N/A')}
    CPF: {dados_aluno.get('cpf', 'N/A')}
    Nome da Mãe: {dados_aluno.get('nome_mae', 'N/A')}

� ENDEREÇO RESIDENCIAL
    Logradouro: {endereco.get('logradouro', 'N/A')}
    Número: {endereco.get('numero', 'N/A')}
    Bairro: {endereco.get('bairro', 'N/A')}
    Cidade: {endereco.get('cidade', 'N/A')}
    CEP: {endereco.get('cep', 'N/A')}
    Estado: {endereco.get('estado', 'N/A')}

👤 DADOS DO RESPONSÁVEL
    Nome Completo: {dados_responsavel.get('nome', 'N/A')}
    CPF: {dados_responsavel.get('cpf', 'N/A')}
    Relação com o Aluno: {dados_responsavel.get('relacao', 'N/A')}
    Telefone: {dados_responsavel.get('telefone', 'N/A')}
    E-mail: {dados_responsavel.get('email', 'N/A')}

🎓 DADOS ESCOLARES
    Série Desejada: {pedido.get('serie_desejada', 'N/A')}

📝 INFORMAÇÕES ADICIONAIS
    {pedido.get('informacoes_adicionais') if pedido.get('informacoes_adicionais') else 'Nenhuma informação adicional fornecida.'}"""
                
                return detalhes
            else:
                # Formato antigo - retornar descrição original com cabeçalho melhorado
                return f"""📋 PROTOCOLO: {pedido.get('id', 'N/A'):06d}
📅 DATA DA SOLICITAÇÃO: {pedido.get('data', 'N/A')}  
📊 STATUS: {pedido.get('status', 'N/A')}

{pedido.get('descricao', 'Nenhuma descrição disponível.')}"""
                
        except Exception as e:
            # Em caso de erro, retorna informações básicas
            return f"""❌ ERRO AO PROCESSAR DETALHES DO PEDIDO
📋 ID: {pedido.get('id', 'N/A')}
📅 DATA: {pedido.get('data', 'N/A')}
📊 STATUS: {pedido.get('status', 'N/A')}

Erro: {str(e)}

DADOS BRUTOS:
{pedido.get('descricao', 'Sem descrição')}"""

    def _criar_controles_inferiores(self, parent_tab):
        """Cria os botões de Sair e Alterar Senha na parte inferior."""
        bottom_frame = customtkinter.CTkFrame(parent_tab, fg_color="transparent")
        bottom_frame.pack(side='bottom', fill='x', padx=10, pady=10)

        customtkinter.CTkButton(
            bottom_frame,
            text='Alterar Minha Senha',
            command=self._alterar_propria_senha
        ).pack(side='left', padx=5)

        customtkinter.CTkButton(
            bottom_frame,
            text='Sair da Conta',
            command=self.sair_da_conta,
            fg_color="#dc3545",
            hover_color="#c82333"
        ).pack(side='right', padx=5)

    def _alterar_propria_senha(self):
        """Abre um formulário para o usuário logado alterar a própria senha."""
        top = customtkinter.CTkToplevel(self)
        top.title("Alterar Senha")
        top.geometry("400x300")
        top.resizable(False, False)
        top.grab_set()

        customtkinter.CTkLabel(top, text="Alterar Minha Senha", font=customtkinter.CTkFont(size=16, weight="bold")).pack(pady=(20,10))

        customtkinter.CTkLabel(top, text="Nova Senha:").pack(anchor='w', padx=20, pady=(10,0))
        e_nova_senha = customtkinter.CTkEntry(top, show='*')
        e_nova_senha.pack(fill='x', padx=20, pady=5)

        customtkinter.CTkLabel(top, text="Confirmar Nova Senha:").pack(anchor='w', padx=20, pady=(10,0))
        e_confirma_senha = customtkinter.CTkEntry(top, show='*')
        e_confirma_senha.pack(fill='x', padx=20, pady=5)

        def salvar_nova_senha():
            nova_senha = e_nova_senha.get()
            confirma_senha = e_confirma_senha.get()

            if not nova_senha or not confirma_senha:
                messagebox.showerror("Erro", "Ambos os campos são obrigatórios.", parent=top)
                return
            
            if nova_senha != confirma_senha:
                messagebox.showerror("Erro", "As senhas não coincidem.", parent=top)
                return

            valida, msg = self._validar_senha(nova_senha)
            if not valida:
                messagebox.showerror("Senha Inválida", msg, parent=top)
                return

            # Criptografar e salvar
            todos_usuarios = carregar_todos_usuarios()
            usuario_atual = next((u for u in todos_usuarios if u['usuario'] == self.usuario_logado['usuario']), None)
            
            if usuario_atual:
                hashed_pw = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                usuario_atual['senha'] = hashed_pw
                salvar_usuario_por_tipo(usuario_atual)
                messagebox.showinfo("Sucesso", "Senha alterada com sucesso!", parent=top)
                top.destroy()
            else:
                messagebox.showerror("Erro Crítico", "Não foi possível encontrar o usuário logado para alterar a senha.", parent=top)

        customtkinter.CTkButton(top, text="Salvar Nova Senha", command=salvar_nova_senha).pack(pady=20)

if __name__ == '__main__':
    app = App()
    app.mainloop()