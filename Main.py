"""
Trabalho Final - Teoria das Estruturas de Dados
Simulador de Sistema Operacional (Tema 3)
Aluno: Daniel Santos Abreu
"""

# "deque" é a fila do Python: permite tirar do início (popleft) de forma rápida.
from collections import deque
# "datetime" dá a data e hora atuais, usadas para identificar cada salvamento no arquivo.
from datetime import datetime

ARQUIVO = "dados_sistema.txt" # arquivo de persistência
DELIM = "|" # separador de campos no arquivo
QUANTUM = 2 # fatia de tempo de CPU para cada processo (round-robin)

# VARIÁVEIS
# Estas quatro variáveis são a "memória" do programa. Elas começam vazias
# (o enunciado proíbe dados pré-carregados) e ficam fora de qualquer função
# para que todas as funções possam enxergá-las.

tabela_processos = []   # LISTA: cada item é um dicionário {pid, nome, prioridade, estado}
fila_cpu = deque()      # FILA: cada item é [pid, nome, tempo_restante]
pilha_chamadas = []     # PILHA: cada item é [tipo, descricao]; o topo é o último
arvore = {"tipo": "DIR", "filhos": {}} # ÁRVORE: raiz "/" com dicionários aninhados
# Exemplo de como a árvore fica depois de criar /home e /home/nota.txt:
# {"tipo": "DIR", "filhos": {
#     "home": {"tipo": "DIR", "filhos": {
#         "nota.txt": {"tipo": "ARQ", "filhos": {}}}}}}

proximo_pid = 1         # contador para gerar PIDs automaticamente

# FUNÇÕES DE ENTRADA
# Estas funções existem para não repetir validação de digitação em todo lugar.

def ler_texto(msg):
    # Lê texto não vazio e sem o delimitador (que corromperia o arquivo).
    while True:                       # repete até o usuário digitar algo válido
        valor = input(msg).strip()    # strip() remove espaços do começo e do fim
        if not valor:                 # string vazia é "falsa" em Python
            print("  ! Valor não pode ser vazio.")
        elif DELIM in valor:          # "|" dentro do texto quebraria a linha do arquivo
            print(f"  ! O caractere '{DELIM}' não é permitido.")
        else:
            return valor              # valor válido: sai do loop devolvendo o texto

def ler_inteiro(msg, minimo=1):
    # Lê um inteiro >= minimo, repetindo até ser válido.
    while True:
        try:
            n = int(input(msg).strip())   # se digitar letras, int() gera ValueError
            if n >= minimo:
                return n
            print(f"  ! Informe um número maior ou igual a {minimo}.")
        except ValueError:                # cai aqui quando o texto não é um número
            print("  ! Entrada inválida: digite um número inteiro.")

def confirmar(msg):
    # Pergunta s/n. Devolve True só se o usuário digitar "s" (ou "S").
    return input(msg + " (s/n): ").strip().lower() == "s"

# LISTA - TABELA DE PROCESSOS

def buscar_processo(pid):
    # Busca por chave (PID) na lista; retorna o dict ou None.
    # É a busca linear: olha um por um até achar. Várias funções usam esta.
    for p in tabela_processos:        # p é um dicionário de processo
        if p["pid"] == pid:
            return p                  # achou: devolve o próprio dicionário (não uma cópia)
    return None                       # percorreu tudo e não achou

def criar_processo():
    global proximo_pid                # "global" é necessário porque vamos REATRIBUIR a variável
    nome = ler_texto("Nome do processo: ")
    prioridade = ler_inteiro("Prioridade (1 = mais alta): ")
    # Monta o registro do processo como um dicionário. O PID vem do contador.
    proc = {"pid": proximo_pid, "nome": nome, "prioridade": prioridade, "estado": "Novo"}
    tabela_processos.append(proc)      # inserção no fim da lista
    print(f"  Processo criado com PID {proximo_pid}.")
    proximo_pid += 1                  # prepara o próximo PID (nunca repete)

def listar_processos():
    if not tabela_processos:          # lista vazia é "falsa"
        print("  (tabela de processos vazia)")
        return                        # sai da função sem imprimir a tabela
    # Em f-strings, {texto:<20} significa "alinhar à esquerda em 20 caracteres" (colunas alinhadas).
    print(f"  {'IDX':<4}{'PID':<6}{'NOME':<20}{'PRIOR.':<8}ESTADO")
    # enumerate() entrega o índice (i) junto com cada item (p).
    for i, p in enumerate(tabela_processos):
        print(f"  {i:<4}{p['pid']:<6}{p['nome']:<20}{p['prioridade']:<8}{p['estado']}")

def consultar_processo():
    # Aqui ler_inteiro está dentro da chamada de buscar_processo: digita o PID e já busca.
    p = buscar_processo(ler_inteiro("PID: "))
    if p:                             # p é None (falso) quando não achou
        print(f"  PID {p['pid']} | {p['nome']} | prioridade {p['prioridade']} | {p['estado']}")
    else:
        print("  Processo não encontrado.")

def atualizar_processo():
    p = buscar_processo(ler_inteiro("PID do processo a atualizar: "))
    if not p:
        print("  Processo não encontrado.")
        return
    print("  (deixe em branco para manter o valor atual)")
    # Aqui usamos input() puro (e não ler_texto) porque vazio é permitido: significa "manter".
    nome = input(f"  Novo nome [{p['nome']}]: ").strip()
    if nome and DELIM not in nome:    # só troca se digitou algo E não tem "|"
        p["nome"] = nome              # como p é o dicionário da lista, isto altera a tabela direto
    prior = input(f"  Nova prioridade [{p['prioridade']}]: ").strip()
    # isdigit() garante que só tem dígitos, então int() não vai dar erro
    if prior.isdigit() and int(prior) >= 1:
        p["prioridade"] = int(prior)
    print("  Processo atualizado.")


def remover_processo():
    pid = ler_inteiro("PID do processo a remover: ")
    p = buscar_processo(pid)
    if not p:
        print("  Processo não encontrado.")
    # any(...) devolve True se ALGUM item da fila tiver este PID (item[0] é o pid)
    elif any(item[0] == pid for item in fila_cpu):
        # Mantém a consistência: a fila só perde elementos pelo início
        print("  ! Processo está na fila da CPU. Execute-o até terminar antes de removê-lo.")
    else:
        tabela_processos.remove(p)    # remove() apaga o item da lista comparando pelo valor
        print("  Processo removido.")

# FILA - ESCALONAMENTO DE PROCESSOS NA CPU (round-robin)

def enfileirar_processo():
    # Inserção no FIM da fila (enqueue).
    pid = ler_inteiro("PID do processo a escalonar: ")
    p = buscar_processo(pid)
    if not p:                         # só dá para escalonar quem existe na tabela
        print("  Processo não existe na tabela de processos.")
        return
    if any(item[0] == pid for item in fila_cpu):   # evita o mesmo processo duas vezes na fila
        print("  Processo já está na fila.")
        return
    tempo = ler_inteiro("Tempo de CPU necessário (unidades): ")
    fila_cpu.append([pid, p["nome"], tempo])       # append no deque = entra no FIM
    p["estado"] = "Pronto"            # atualiza o estado na tabela de processos (lista)
    print("  Processo adicionado ao fim da fila.")


def listar_fila():
    if not fila_cpu:
        print("  (fila vazia)")
        return
    print("  Início da fila (próximo a executar) -> fim")
    # Cada item da fila é [pid, nome, tempo]; o "for" já separa nas três variáveis.
    # start=1 faz a contagem das posições começar em 1 (mais natural para o usuário).
    for pos, (pid, nome, tempo) in enumerate(fila_cpu, start=1):
        print(f"  {pos}. PID {pid} | {nome} | restante: {tempo}")


def executar_proximo():
    # Remoção no INÍCIO da fila (dequeue). Executa um quantum; se sobrar
    # tempo, o processo volta ao FIM da fila (Round-Robin).
    if not fila_cpu:
        print("  Fila vazia: nenhum processo para executar.")
        return
    pid, nome, tempo = fila_cpu.popleft()   # tira o PRIMEIRO da fila (o que espera há mais tempo)
    p = buscar_processo(pid)                # pega o registro na tabela para poder mudar o estado
    usado = min(QUANTUM, tempo)             # usa no máximo QUANTUM; se faltar menos, usa só o que falta
    tempo -= usado                          # desconta o tempo usado do que restava
    print(f"  CPU executou PID {pid} ({nome}) por {usado} unidade(s).")
    if tempo > 0:
        # Ainda não terminou: volta para o FIM da fila (é isso que faz o rodízio)
        fila_cpu.append([pid, nome, tempo])
        if p:                         # "if p" protege caso o processo não exista mais na tabela
            p["estado"] = "Pronto"
        print(f"  Restam {tempo} unidade(s): volta ao fim da fila.")
    else:
        # Tempo zerou: NÃO volta para a fila, e a tabela marca como finalizado
        if p:
            p["estado"] = "Finalizado"
        print("  Processo finalizado.")


def atualizar_fila():
    # Altera o tempo restante de um item da fila (sem mudar sua ordem).
    listar_fila()                     # mostra a fila para o usuário escolher a posição
    if not fila_cpu:                  # fila vazia: não há o que atualizar
        return
    pos = ler_inteiro("Posição do item: ")
    if pos > len(fila_cpu):
        print("  Posição inválida.")
        return
    # O usuário vê posições começando em 1, mas o deque começa em 0, daí o "pos - 1".
    # O "[2]" é o terceiro campo do item [pid, nome, tempo], ou seja, o tempo restante.
    fila_cpu[pos - 1][2] = ler_inteiro("Novo tempo restante: ")
    print("  Item atualizado.")

# PILHA - CHAMADAS DE SUB-ROTINAS E INTERRUPÇÕES

def empilhar():
    # Push: insere no TOPO (final da list).
    print("  Tipo: 1) Sub-rotina  2) Interrupção")
    # Expressão condicional: se digitou "2" vira INTERRUPCAO; qualquer outra coisa vira SUBROTINA.
    tipo = "INTERRUPCAO" if input("  Escolha: ").strip() == "2" else "SUBROTINA"
    desc = ler_texto("Descrição (ex.: funcao_leitura, IRQ_teclado): ")
    pilha_chamadas.append([tipo, desc])    # append no fim da lista = topo da pilha
    print(f"  {tipo} empilhada.")


def desempilhar():
    # Pop: remove do TOPO.
    if not pilha_chamadas:
        print("  Pilha vazia.")
        return
    tipo, desc = pilha_chamadas.pop()      # pop() sem argumento remove E devolve o último (topo)
    print(f"  Retorno de {tipo}: {desc}")


def ver_topo():
    if not pilha_chamadas:
        print("  Pilha vazia.")
    else:
        # [-1] é o último elemento (o topo). [0] é o tipo e [1] é a descrição.
        # Aqui só LEMOS o topo, não removemos (diferente do pop).
        print(f"  Topo: {pilha_chamadas[-1][0]} - {pilha_chamadas[-1][1]}")


def listar_pilha():
    if not pilha_chamadas:
        print("  (pilha vazia)")
        return
    print("  TOPO")
    # reversed() percorre de trás para frente, assim o topo (último) aparece primeiro.
    # {tipo:<12} alinha a coluna do tipo em 12 caracteres.
    for tipo, desc in reversed(pilha_chamadas):   # mostra do topo para a base
        print(f"   | {tipo:<12} {desc}")
    print("  BASE")


def atualizar_topo():
    # Só o topo pode ser alterado, respeitando o acesso LIFO.
    if not pilha_chamadas:
        print("  Pilha vazia.")
        return
    # [-1] é o topo; [1] é a descrição dele. Troca só a descrição, o tipo continua.
    pilha_chamadas[-1][1] = ler_texto("Nova descrição do topo: ")
    print("  Topo atualizado.")

# ÁRVORE - SISTEMA DE ARQUIVOS (dicionários aninhados)
# Cada nó contém: {"tipo": "DIR" ou "ARQ", "filhos": {nome: nó, ...}}
# Ou seja: um diretório guarda seus filhos em um dicionário, e cada filho é
# outro nó com o mesmo formato. É isso que faz os dicionários ficarem "aninhados".

def separar_caminho(caminho):
    # '/home/user' -> ['home', 'user']; '/' -> []
    # split("/") quebra o texto em cada "/". O "if parte" descarta pedaços vazios
    # (por exemplo o que vem antes do primeiro "/" ou de "//").
    return [parte for parte in caminho.strip().split("/") if parte]


def localizar_no(partes):
    # Desce na árvore seguindo os nomes; retorna o nó ou None.
    # Exemplo: partes = ["home", "docs"] -> entra em home, depois em docs.
    # Lista vazia (a raiz "/") faz o loop não rodar e devolve a própria raiz.
    no = arvore                       # começa sempre na raiz
    for nome in partes:
        # Falha se o nó atual é um arquivo (não tem como entrar nele)
        # ou se o nome procurado não existe entre os filhos dele.
        if no["tipo"] != "DIR" or nome not in no["filhos"]:
            return None
        no = no["filhos"][nome]       # desce um nível: o filho vira o nó atual
    return no                         # chegou ao fim do caminho: este é o nó procurado


def criar_no(tipo):
    # Serve para criar diretório e arquivo: o menu passa "DIR" ou "ARQ" em "tipo".
    caminho = ler_texto("Diretório pai (ex.: / ou /home): ")
    pai = localizar_no(separar_caminho(caminho))    # texto -> lista de nomes -> nó
    # O pai precisa existir E ser diretório (não dá para criar algo "dentro" de um arquivo)
    if pai is None or pai["tipo"] != "DIR":
        print("  Diretório pai não encontrado.")
        return
    nome = ler_texto("Nome: ")
    if "/" in nome:                   # "/" no nome confundiria a separação de caminhos
        print("  Nome não pode conter '/'.")
    elif nome in pai["filhos"]:       # chave duplicada sobrescreveria o item existente
        print("  Já existe um item com esse nome.")
    else:
        # Inserção hierárquica: cria a chave "nome" nos filhos do pai, com um nó novo e vazio.
        pai["filhos"][nome] = {"tipo": tipo, "filhos": {}}
        print("  Criado com sucesso.")


def imprimir_arvore(no, nome="/", nivel=0):
    # Percurso recursivo em pré-ordem, com indentação por nível.
    # Recursão: a função chama a si mesma para cada filho, aumentando o nível.
    # Pré-ordem: imprime o nó ANTES de imprimir os filhos dele.
    # Só diretórios (exceto a raiz) ganham "/" no final do nome.
    sufixo = "/" if no["tipo"] == "DIR" and nome != "/" else ""
    # "    " * nivel repete 4 espaços "nivel" vezes: quanto mais fundo, mais à direita.
    print("  " + "    " * nivel + nome + sufixo)
    # sorted() dá a ordem alfabética dos nomes dos filhos.
    # CASO-BASE: arquivo ou diretório vazio não tem filhos, o "for" não roda
    # e a recursão termina ali.
    for filho in sorted(no["filhos"]):
        imprimir_arvore(no["filhos"][filho], filho, nivel + 1)   # nivel + 1 = um nível mais fundo


def listar_diretorio():
    caminho = ler_texto("Caminho (ex.: / ou /home): ")
    no = localizar_no(separar_caminho(caminho))
    if no is None:
        print("  Caminho não encontrado.")
    elif no["tipo"] == "ARQ":
        print("  É um arquivo.")
    elif not no["filhos"]:            # dicionário de filhos vazio
        print("  (diretório vazio)")
    else:
        # Mostra só os filhos DIRETOS (um nível), cada um com [DIR] ou [ARQ].
        for nome in sorted(no["filhos"]):
            print(f"  [{no['filhos'][nome]['tipo']}] {nome}")


def renomear_no():
    partes = separar_caminho(ler_texto("Caminho do item (ex.: /home/doc.txt): "))
    if not partes:                    # caminho "/" vira lista vazia: é a raiz
        print("  A raiz não pode ser renomeada.")
        return
    # Para renomear, precisamos do PAI: partes[:-1] é o caminho sem o último nome.
    # Ex.: ["home", "doc.txt"][:-1] = ["home"]. O último nome é partes[-1].
    pai = localizar_no(partes[:-1])
    if pai is None or partes[-1] not in pai["filhos"]:
        print("  Item não encontrado.")
        return
    novo = ler_texto("Novo nome: ")
    if "/" in novo or novo in pai["filhos"]:
        print("  Nome inválido ou já existente.")
        return
    # pop() remove a chave antiga e DEVOLVE o nó (com todos os filhos dele).
    # Em seguida o nó é guardado de novo, agora com a chave nova.
    pai["filhos"][novo] = pai["filhos"].pop(partes[-1])
    print("  Renomeado.")


def remover_no():
    partes = separar_caminho(ler_texto("Caminho do item a remover: "))
    if not partes:
        print("  A raiz não pode ser removida.")
        return
    pai = localizar_no(partes[:-1])   # o pai do item (mesma ideia do renomear)
    if pai is None or partes[-1] not in pai["filhos"]:
        print("  Item não encontrado.")
        return
    alvo = pai["filhos"][partes[-1]]
    # Se o alvo tem filhos, apagar leva a subárvore inteira junto: pede confirmação.
    # Se o usuário disser "n", o "return" cancela a remoção.
    if alvo["filhos"] and not confirmar("  Diretório não vazio: remover com todo o conteúdo?"):
        return
    del pai["filhos"][partes[-1]]     # apaga a chave do dicionário do pai
    print("  Removido.")

# PERSISTÊNCIA EM ARQUIVO TXT
# O arquivo NUNCA é sobrescrito: cada salvamento é ACRESCENTADO ao final.
# Para saber onde começa cada salvamento, ele inicia com uma linha de marcação.
# Ao carregar, só o ÚLTIMO salvamento (o estado mais recente) é reconstruído.
# Formatos:
#   SALVAMENTO|data e hora         (marca o início de cada salvamento)
#   LISTA|pid|nome|prioridade|estado
#   FILA|pid|nome|tempo_restante
#   PILHA|tipo|descricao           (da base para o topo)
#   ARVORE|DIR ou ARQ|nome1|nome2|...   (caminho completo, em pré-ordem)

def linhas_arvore(no, caminho):
    # Gera uma linha por nó, pais antes dos filhos (facilita a reconstrução).
    # Esta é uma função GERADORA: em vez de "return", usa "yield" para entregar
    # uma linha de cada vez. "caminho" é a lista de nomes desde a raiz até este nó.
    for nome in sorted(no["filhos"]):
        filho = no["filhos"][nome]
        novo = caminho + [nome]       # caminho do filho = caminho do pai + o nome dele
        # DELIM.join(lista) junta os itens com "|". Ex.: ["ARVORE","DIR","home"] -> "ARVORE|DIR|home"
        yield DELIM.join(["ARVORE", filho["tipo"]] + novo)    # 1º entrega a linha do filho...
        # ...2º entrega as linhas dos descendentes (recursão). "yield from" repassa tudo
        # o que a chamada recursiva gerar. Por isso o pai sempre vem antes dos filhos.
        yield from linhas_arvore(filho, novo)


def salvar_dados():
    try:
        # "a" = acréscimo (append): se o arquivo já existe, o conteúdo anterior é
        # MANTIDO e o que gravarmos vai para o final; se não existe, ele é criado.
        # O "with" fecha o arquivo sozinho no final, mesmo se der erro.
        with open(ARQUIVO, "a", encoding="utf-8") as f:
            # Linha de marcação: diz onde começa este salvamento. strftime formata a data/hora.
            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(DELIM.join(["SALVAMENTO", agora]) + "\n")
            for p in tabela_processos:
                # Todo campo precisa virar texto (str) antes de juntar. "\n" termina a linha.
                f.write(DELIM.join(["LISTA", str(p["pid"]), p["nome"],
                                    str(p["prioridade"]), p["estado"]]) + "\n")
            # Cada item da fila é [pid, nome, tempo]; o "for" separa nas 3 variáveis.
            # A fila é gravada do início ao fim, então a ordem é preservada.
            for pid, nome, tempo in fila_cpu:
                f.write(DELIM.join(["FILA", str(pid), nome, str(tempo)]) + "\n")
            # Gravada da BASE para o TOPO, para recarregar na mesma ordem.
            for tipo, desc in pilha_chamadas:
                f.write(DELIM.join(["PILHA", tipo, desc]) + "\n")
            # Começa na raiz com caminho vazio []. Cada linha gerada vira uma linha do arquivo.
            for linha in linhas_arvore(arvore, []):
                f.write(linha + "\n")
        print(f"  Dados salvos em '{ARQUIVO}'.")
    except OSError as erro:           # erros de disco, permissão, etc.
        print(f"  Erro ao salvar: {erro}")


def carregar_dados():
    global proximo_pid                # vamos reatribuir o contador de PIDs no final
    try:
        with open(ARQUIVO, "r", encoding="utf-8") as f:    # "r" = leitura
            # splitlines() corta o texto em uma lista de linhas, sem o "\n" no final.
            linhas = f.read().splitlines()
    except FileNotFoundError:         # ainda não existe arquivo salvo
        print(f"  Arquivo '{ARQUIVO}' não encontrado. Salve os dados primeiro.")
        return
    except OSError as erro:
        print(f"  Erro ao ler: {erro}")
        return

    # O arquivo acumula vários salvamentos. Procuramos a ÚLTIMA linha de marcação
    # e descartamos tudo o que vem antes dela, ficando só com o estado mais recente.
    # Se não houver nenhuma marcação (arquivo sem ela), "inicio" fica 0 e lemos tudo.
    inicio = 0
    for i, linha in enumerate(linhas):
        if linha.startswith("SALVAMENTO" + DELIM):
            inicio = i + 1            # o bloco começa na linha SEGUINTE à marcação
    linhas = linhas[inicio:]          # fatia: do início do último bloco até o fim

    # Limpa a memória (mesmos objetos, para manter as referências globais)
    # clear() esvazia o objeto existente. Se fizéssemos "tabela_processos = []"
    # criaríamos uma variável local nova e a global não mudaria.
    tabela_processos.clear()
    fila_cpu.clear()
    pilha_chamadas.clear()
    arvore["filhos"].clear()          # esvazia só os filhos: a raiz em si continua existindo
    ignoradas = 0                     # conta as linhas defeituosas

    for linha in linhas:
        campos = linha.split(DELIM)   # "FILA|1|init|3" -> ["FILA", "1", "init", "3"]
        ident = campos[0]             # o primeiro campo diz a qual estrutura a linha pertence
        try:
            # Além do identificador, confere a quantidade de campos de cada formato.
            if ident == "LISTA" and len(campos) == 5:
                # int() converte o texto lido do arquivo de volta para número
                tabela_processos.append({"pid": int(campos[1]), "nome": campos[2],
                                         "prioridade": int(campos[3]), "estado": campos[4]})
            elif ident == "FILA" and len(campos) == 4:
                fila_cpu.append([int(campos[1]), campos[2], int(campos[3])])   # entra no fim, na mesma ordem
            elif ident == "PILHA" and len(campos) == 3:
                # Como foi salva da base para o topo, o último lido vira o topo
                pilha_chamadas.append([campos[1], campos[2]])
            elif ident == "ARVORE" and len(campos) >= 3:
                # Ex.: ["ARVORE","DIR","home","docs"]
                #   campos[1]    = "DIR" (o tipo do nó)
                #   campos[2:-1] = ["home"] (o caminho do PAI: do índice 2 até antes do último)
                #   campos[-1]   = "docs" (o nome do nó novo)
                pai = localizar_no(campos[2:-1])
                if pai is None:
                    # Isto falha se o arquivo estiver fora de ordem (filho antes do pai).
                    # Por isso o salvar grava sempre os pais primeiro.
                    raise ValueError("pai inexistente")
                pai["filhos"][campos[-1]] = {"tipo": campos[1], "filhos": {}}
            else:
                raise ValueError("linha inválida")   # identificador desconhecido ou nº de campos errado
        except ValueError:
            # Pega os dois casos: int() falhando em texto não numérico e os "raise" acima.
            # A linha ruim é só contada e o carregamento continua.
            ignoradas += 1

    # Evita PIDs repetidos: continua a partir do maior PID carregado
    # default=0 evita erro quando a tabela está vazia (max de lista vazia daria erro).
    proximo_pid = max([p["pid"] for p in tabela_processos], default=0) + 1
    print(f"  Dados carregados ({len(linhas) - ignoradas} registros, {ignoradas} ignorados).")

# MENUS

def executar_submenu(titulo, opcoes):
    # Exibe um submenu numérico e chama a função da opção escolhida.
    # 'opcoes' é uma lista de tuplas (rótulo, função).
    # Esta função serve para os 4 submenus: eles só mudam o título e a lista de opções.
    while True:
        print(f"\n--- {titulo} ---")
        # Cada tupla é (rotulo, funcao). O "_" ignora a função, pois aqui só imprimimos o texto.
        # start=1 numera as opções a partir de 1.
        for i, (rotulo, _) in enumerate(opcoes, start=1):
            print(f"{i}. {rotulo}")
        print("0. Voltar")
        escolha = input("Opção: ").strip()
        if escolha == "0":
            return                    # volta ao menu anterior
        # isdigit() primeiro, para int() não dar erro com letras; depois confere o intervalo.
        if escolha.isdigit() and 1 <= int(escolha) <= len(opcoes):
            # opcoes[n-1] é a tupla (rotulo, funcao). O [1] pega a função e os "()" a executam.
            opcoes[int(escolha) - 1][1]()
        else:
            print("  Opção inválida.")


def menu_processos():
    # Funções são passadas SEM parênteses (criar_processo, não criar_processo()),
    # porque queremos entregar a função em si, para ser chamada depois.
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
        # criar_no precisa de um argumento ("DIR"/"ARQ"), mas o submenu chama a função sem argumentos.
        # O lambda cria uma funçãozinha sem argumentos que, ao ser chamada, executa criar_no("DIR").
        ("Criar diretório", lambda: criar_no("DIR")),
        ("Criar arquivo", lambda: criar_no("ARQ")),
        # Mesma ideia: imprimir_arvore precisa receber a raiz.
        ("Exibir árvore completa", lambda: imprimir_arvore(arvore)),
        ("Listar conteúdo de um diretório", listar_diretorio),
        ("Renomear item", renomear_no),
        ("Remover item", remover_no),
    ])


def menu_principal():
    while True:                       # o programa só termina pelo "break" da opção 0
        print("\n===== SIMULADOR DE SISTEMA OPERACIONAL =====")
        print("1. Tabela de processos (Lista)")
        print("2. Escalonador de CPU (Fila)")
        print("3. Pilha de chamadas/interrupções (Pilha)")
        print("4. Sistema de arquivos (Árvore)")
        print("5. Salvar dados")
        print("6. Carregar dados")
        print("0. Sair")
        escolha = input("Opção: ").strip()
        # Cada opção chama um submenu (que tem o próprio loop) ou uma função de persistência.
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
            break                     # quebra o while True e encerra o programa
        else:
            print("  Opção inválida.")


# Só executa o menu se o arquivo for rodado diretamente (python main.py).
# Se alguém importar este arquivo como módulo, o menu não abre sozinho.
if __name__ == "__main__":
    menu_principal()