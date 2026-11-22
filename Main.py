"""
Trabalho Final - Teoria das Estruturas de Dados
Simulador de Sistema Operacional (Tema 3)
Aluno: Daniel Santos Abreu
"""

from collections import deque

ARQUIVO = "dados_sistema.txt" # arquivo de persistência
DELIM = "|" # separador de campos no arquivo
QUANTUM = 2 # fatia de tempo de CPU para cada processo (round-robin)

# VARIÁVEIS

tabela_processos = []   # LISTA: cada item é um dicionário {pid, nome, prioridade, estado}
fila_cpu = deque()      # FILA: cada item é [pid, nome, tempo_restante]
pilha_chamadas = []     # PILHA: cada item é [tipo, descricao]; o topo é o último
arvore = {"tipo": "DIR", "filhos": {}} # ÁRVORE: raiz "/" com dicionários aninhados

proximo_pid = 1         # contador para gerar PIDs automaticamente

# FUNÇÕES DE ENTRADA

def ler_texto(msg): # Lê texto não vazio e sem o delimitador (que corromperia o arquivo).
    while True:
        valor = input(msg).strip()
        if not valor:
            print("  ! Valor não pode ser vazio.")
        elif DELIM in valor:
            print(f"  ! O caractere '{DELIM}' não é permitido.")
        else:
            return valor

def ler_inteiro(msg, minimo=1): # Lê um inteiro >= minimo, repetindo até ser válido.
    while True:
        try:
            n = int(input(msg).strip())
            if n >= minimo:
                return n
            print(f"  ! Informe um número maior ou igual a {minimo}.")
        except ValueError:
            print("  ! Entrada inválida: digite um número inteiro.")

def confirmar(msg):
    return input(msg + " (s/n): ").strip().lower() == "s"

# LISTA - TABELA DE PROCESSOS

def buscar_processo(pid): # Busca por chave (PID) na lista; retorna o dict ou None.
    for p in tabela_processos:
        if p["pid"] == pid:
            return p
    return None

def criar_processo():
    global proximo_pid
    nome = ler_texto("Nome do processo: ")
    prioridade = ler_inteiro("Prioridade (1 = mais alta): ")
    proc = {"pid": proximo_pid, "nome": nome, "prioridade": prioridade, "estado": "Novo"}
    tabela_processos.append(proc)      # inserção no fim da lista
    print(f"  Processo criado com PID {proximo_pid}.")
    proximo_pid += 1

def listar_processos():
    if not tabela_processos:
        print("  (tabela de processos vazia)")
        return
    print(f"  {'IDX':<4}{'PID':<6}{'NOME':<20}{'PRIOR.':<8}ESTADO")
    for i, p in enumerate(tabela_processos):
        print(f"  {i:<4}{p['pid']:<6}{p['nome']:<20}{p['prioridade']:<8}{p['estado']}")

def consultar_processo():
    p = buscar_processo(ler_inteiro("PID: "))
    if p:
        print(f"  PID {p['pid']} | {p['nome']} | prioridade {p['prioridade']} | {p['estado']}")
    else:
        print("  Processo não encontrado.")

def atualizar_processo():
    p = buscar_processo(ler_inteiro("PID do processo a atualizar: "))
    if not p:
        print("  Processo não encontrado.")
        return
    print("  (deixe em branco para manter o valor atual)")
    nome = input(f"  Novo nome [{p['nome']}]: ").strip()
    if nome and DELIM not in nome:
        p["nome"] = nome
    prior = input(f"  Nova prioridade [{p['prioridade']}]: ").strip()
    if prior.isdigit() and int(prior) >= 1:
        p["prioridade"] = int(prior)
    print("  Processo atualizado.")


def remover_processo():
    pid = ler_inteiro("PID do processo a remover: ")
    p = buscar_processo(pid)
    if not p:
        print("  Processo não encontrado.")
    elif any(item[0] == pid for item in fila_cpu):
        # Mantém a consistência: a fila só perde elementos pelo início
        print("  ! Processo está na fila da CPU. Execute-o até terminar antes de removê-lo.")
    else:
        tabela_processos.remove(p)
        print("  Processo removido.")

# FILA - ESCALONAMENTO DE PROCESSOS NA CPU (round-robin)

def enfileirar_processo():
    """Inserção no FIM da fila (enqueue)."""
    pid = ler_inteiro("PID do processo a escalonar: ")
    p = buscar_processo(pid)
    if not p:
        print("  Processo não existe na tabela de processos.")
        return
    if any(item[0] == pid for item in fila_cpu):
        print("  Processo já está na fila.")
        return
    tempo = ler_inteiro("Tempo de CPU necessário (unidades): ")
    fila_cpu.append([pid, p["nome"], tempo])
    p["estado"] = "Pronto"
    print("  Processo adicionado ao fim da fila.")


def listar_fila():
    if not fila_cpu:
        print("  (fila vazia)")
        return
    print("  Início da fila (próximo a executar) -> fim")
    for pos, (pid, nome, tempo) in enumerate(fila_cpu, start=1):
        print(f"  {pos}. PID {pid} | {nome} | restante: {tempo}")


def executar_proximo():
    """Remoção no INÍCIO da fila (dequeue). Executa um quantum; se sobrar
    tempo, o processo volta ao FIM da fila (Round-Robin)."""
    if not fila_cpu:
        print("  Fila vazia: nenhum processo para executar.")
        return
    pid, nome, tempo = fila_cpu.popleft()
    p = buscar_processo(pid)
    usado = min(QUANTUM, tempo)
    tempo -= usado
    print(f"  CPU executou PID {pid} ({nome}) por {usado} unidade(s).")
    if tempo > 0:
        fila_cpu.append([pid, nome, tempo])
        if p:
            p["estado"] = "Pronto"
        print(f"  Restam {tempo} unidade(s): volta ao fim da fila.")
    else:
        if p:
            p["estado"] = "Finalizado"
        print("  Processo finalizado.")


def atualizar_fila():
    """Altera o tempo restante de um item da fila (sem mudar sua ordem)."""
    listar_fila()
    if not fila_cpu:
        return
    pos = ler_inteiro("Posição do item: ")
    if pos > len(fila_cpu):
        print("  Posição inválida.")
        return
    fila_cpu[pos - 1][2] = ler_inteiro("Novo tempo restante: ")
    print("  Item atualizado.")

# PILHA - CHAMADAS DE SUB-ROTINAS E INTERRUPÇÕES

def empilhar():
    """Push: insere no TOPO (final da list)."""
    print("  Tipo: 1) Sub-rotina  2) Interrupção")
    tipo = "INTERRUPCAO" if input("  Escolha: ").strip() == "2" else "SUBROTINA"
    desc = ler_texto("Descrição (ex.: funcao_leitura, IRQ_teclado): ")
    pilha_chamadas.append([tipo, desc])
    print(f"  {tipo} empilhada.")


def desempilhar():
    """Pop: remove do TOPO."""
    if not pilha_chamadas:
        print("  Pilha vazia.")
        return
    tipo, desc = pilha_chamadas.pop()
    print(f"  Retorno de {tipo}: {desc}")


def ver_topo():
    if not pilha_chamadas:
        print("  Pilha vazia.")
    else:
        print(f"  Topo: {pilha_chamadas[-1][0]} - {pilha_chamadas[-1][1]}")


def listar_pilha():
    if not pilha_chamadas:
        print("  (pilha vazia)")
        return
    print("  TOPO")
    for tipo, desc in reversed(pilha_chamadas):   # mostra do topo para a base
        print(f"   | {tipo:<12} {desc}")
    print("  BASE")


def atualizar_topo():
    """Só o topo pode ser alterado, respeitando o acesso LIFO."""
    if not pilha_chamadas:
        print("  Pilha vazia.")
        return
    pilha_chamadas[-1][1] = ler_texto("Nova descrição do topo: ")
    print("  Topo atualizado.")

# ÁRVORE - SISTEMA DE ARQUIVOS (dicionários aninhados)
# Cada nó contém: {"tipo": "DIR" ou "ARQ", "filhos": {nome: nó, ...}}

def separar_caminho(caminho):
    """'/home/user' -> ['home', 'user']; '/' -> []"""
    return [parte for parte in caminho.strip().split("/") if parte]


def localizar_no(partes):
    """Desce na árvore seguindo os nomes; retorna o nó ou None."""
    no = arvore
    for nome in partes:
        if no["tipo"] != "DIR" or nome not in no["filhos"]:
            return None
        no = no["filhos"][nome]
    return no


def criar_no(tipo):
    caminho = ler_texto("Diretório pai (ex.: / ou /home): ")
    pai = localizar_no(separar_caminho(caminho))
    if pai is None or pai["tipo"] != "DIR":
        print("  Diretório pai não encontrado.")
        return
    nome = ler_texto("Nome: ")
    if "/" in nome:
        print("  Nome não pode conter '/'.")
    elif nome in pai["filhos"]:
        print("  Já existe um item com esse nome.")
    else:
        pai["filhos"][nome] = {"tipo": tipo, "filhos": {}}
        print("  Criado com sucesso.")


def imprimir_arvore(no, nome="/", nivel=0):
    """Percurso recursivo em pré-ordem, com indentação por nível."""
    sufixo = "/" if no["tipo"] == "DIR" and nome != "/" else ""
    print("  " + "    " * nivel + nome + sufixo)
    for filho in sorted(no["filhos"]):
        imprimir_arvore(no["filhos"][filho], filho, nivel + 1)


def listar_diretorio():
    caminho = ler_texto("Caminho (ex.: / ou /home): ")
    no = localizar_no(separar_caminho(caminho))
    if no is None:
        print("  Caminho não encontrado.")
    elif no["tipo"] == "ARQ":
        print("  É um arquivo.")
    elif not no["filhos"]:
        print("  (diretório vazio)")
    else:
        for nome in sorted(no["filhos"]):
            print(f"  [{no['filhos'][nome]['tipo']}] {nome}")


def renomear_no():
    partes = separar_caminho(ler_texto("Caminho do item (ex.: /home/doc.txt): "))
    if not partes:
        print("  A raiz não pode ser renomeada.")
        return
    pai = localizar_no(partes[:-1])
    if pai is None or partes[-1] not in pai["filhos"]:
        print("  Item não encontrado.")
        return
    novo = ler_texto("Novo nome: ")
    if "/" in novo or novo in pai["filhos"]:
        print("  Nome inválido ou já existente.")
        return
    pai["filhos"][novo] = pai["filhos"].pop(partes[-1])
    print("  Renomeado.")


def remover_no():
    partes = separar_caminho(ler_texto("Caminho do item a remover: "))
    if not partes:
        print("  A raiz não pode ser removida.")
        return
    pai = localizar_no(partes[:-1])
    if pai is None or partes[-1] not in pai["filhos"]:
        print("  Item não encontrado.")
        return
    alvo = pai["filhos"][partes[-1]]
    if alvo["filhos"] and not confirmar("  Diretório não vazio: remover com todo o conteúdo?"):
        return
    del pai["filhos"][partes[-1]]
    print("  Removido.")

# PERSISTÊNCIA EM ARQUIVO TXT
# Formatos:
#   LISTA|pid|nome|prioridade|estado
#   FILA|pid|nome|tempo_restante
#   PILHA|tipo|descricao           (da base para o topo)
#   ARVORE|DIR ou ARQ|nome1|nome2|...   (caminho completo, em pré-ordem)

def linhas_arvore(no, caminho):
    """Gera uma linha por nó, pais antes dos filhos (facilita a reconstrução)."""
    for nome in sorted(no["filhos"]):
        filho = no["filhos"][nome]
        novo = caminho + [nome]
        yield DELIM.join(["ARVORE", filho["tipo"]] + novo)
        yield from linhas_arvore(filho, novo)


def salvar_dados():
    try:
        with open(ARQUIVO, "w", encoding="utf-8") as f:
            for p in tabela_processos:
                f.write(DELIM.join(["LISTA", str(p["pid"]), p["nome"],
                                    str(p["prioridade"]), p["estado"]]) + "\n")
            for pid, nome, tempo in fila_cpu:
                f.write(DELIM.join(["FILA", str(pid), nome, str(tempo)]) + "\n")
            for tipo, desc in pilha_chamadas:
                f.write(DELIM.join(["PILHA", tipo, desc]) + "\n")
            for linha in linhas_arvore(arvore, []):
                f.write(linha + "\n")
        print(f"  Dados salvos em '{ARQUIVO}'.")
    except OSError as erro:
        print(f"  Erro ao salvar: {erro}")


def carregar_dados():
    global proximo_pid
    try:
        with open(ARQUIVO, "r", encoding="utf-8") as f:
            linhas = f.read().splitlines()
    except FileNotFoundError:
        print(f"  Arquivo '{ARQUIVO}' não encontrado. Salve os dados primeiro.")
        return
    except OSError as erro:
        print(f"  Erro ao ler: {erro}")
        return

    # Limpa a memória (mesmos objetos, para manter as referências globais)
    tabela_processos.clear()
    fila_cpu.clear()
    pilha_chamadas.clear()
    arvore["filhos"].clear()
    ignoradas = 0

    for linha in linhas:
        campos = linha.split(DELIM)
        ident = campos[0]
        try:
            if ident == "LISTA" and len(campos) == 5:
                tabela_processos.append({"pid": int(campos[1]), "nome": campos[2],
                                         "prioridade": int(campos[3]), "estado": campos[4]})
            elif ident == "FILA" and len(campos) == 4:
                fila_cpu.append([int(campos[1]), campos[2], int(campos[3])])
            elif ident == "PILHA" and len(campos) == 3:
                pilha_chamadas.append([campos[1], campos[2]])
            elif ident == "ARVORE" and len(campos) >= 3:
                pai = localizar_no(campos[2:-1])
                if pai is None:
                    raise ValueError("pai inexistente")
                pai["filhos"][campos[-1]] = {"tipo": campos[1], "filhos": {}}
            else:
                raise ValueError("linha inválida")
        except ValueError:
            ignoradas += 1

    # Evita PIDs repetidos: continua a partir do maior PID carregado
    proximo_pid = max([p["pid"] for p in tabela_processos], default=0) + 1
    print(f"  Dados carregados ({len(linhas) - ignoradas} registros, {ignoradas} ignorados).")

# MENUS

def executar_submenu(titulo, opcoes):
    """Exibe um submenu numérico e chama a função da opção escolhida.
    'opcoes' é uma lista de tuplas (rótulo, função)."""
    while True:
        print(f"\n--- {titulo} ---")
        for i, (rotulo, _) in enumerate(opcoes, start=1):
            print(f"{i}. {rotulo}")
        print("0. Voltar")
        escolha = input("Opção: ").strip()
        if escolha == "0":
            return
        if escolha.isdigit() and 1 <= int(escolha) <= len(opcoes):
            opcoes[int(escolha) - 1][1]()
        else:
            print("  Opção inválida.")


def menu_processos():
    executar_submenu("TABELA DE PROCESSOS (LISTA)", [
        ("Criar processo", criar_processo),
        ("Listar processos", listar_processos),
        ("Consultar por PID", consultar_processo),
        ("Atualizar processo", atualizar_processo),
        ("Remover processo", remover_processo),
    ])


def menu_fila():
    executar_submenu("ESCALONADOR DE CPU (FILA)", [
        ("Enfileirar processo (fim)", enfileirar_processo),
        ("Listar fila", listar_fila),
        (f"Executar próximo (remove do início, quantum={QUANTUM})", executar_proximo),
        ("Atualizar tempo restante de um item", atualizar_fila),
    ])


def menu_pilha():
    executar_submenu("PILHA DE CHAMADAS E INTERRUPÇÕES (PILHA)", [
        ("Empilhar (push)", empilhar),
        ("Desempilhar (pop)", desempilhar),
        ("Ver topo", ver_topo),
        ("Listar pilha", listar_pilha),
        ("Atualizar topo", atualizar_topo),
    ])


def menu_arquivos():
    executar_submenu("SISTEMA DE ARQUIVOS (ÁRVORE)", [
        ("Criar diretório", lambda: criar_no("DIR")),
        ("Criar arquivo", lambda: criar_no("ARQ")),
        ("Exibir árvore completa", lambda: imprimir_arvore(arvore)),
        ("Listar conteúdo de um diretório", listar_diretorio),
        ("Renomear item", renomear_no),
        ("Remover item", remover_no),
    ])


def menu_principal():
    while True:
        print("\n===== SIMULADOR DE SISTEMA OPERACIONAL =====")
        print("1. Tabela de processos (Lista)")
        print("2. Escalonador de CPU (Fila)")
        print("3. Pilha de chamadas/interrupções (Pilha)")
        print("4. Sistema de arquivos (Árvore)")
        print("5. Salvar dados")
        print("6. Carregar dados")
        print("0. Sair")
        escolha = input("Opção: ").strip()
        if escolha == "1":
            menu_processos()
        elif escolha == "2":
            menu_fila()
        elif escolha == "3":
            menu_pilha()
        elif escolha == "4":
            menu_arquivos()
        elif escolha == "5":
            salvar_dados()
        elif escolha == "6":
            carregar_dados()
        elif escolha == "0":
            if confirmar("Salvar dados antes de sair?"):
                salvar_dados()
            print("Encerrando.")
            break
        else:
            print("  Opção inválida.")


if __name__ == "__main__":
    menu_principal()