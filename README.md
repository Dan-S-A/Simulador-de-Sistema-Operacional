# Simulador de Sistema Operacional

Projeto final de **Teoria das Estruturas de Dados** — Tema 3: Simulador de Sistema Operacional.

Sistema em Python (CLI) que integra as quatro estruturas fundamentais — **Lista, Fila, Pilha e Árvore** — e persiste tudo em um único arquivo texto, `dados_sistema.txt`.

## Como executar

Requisitos: Python 3.8 ou superior (apenas biblioteca padrão, nada a instalar).

```bash
python main.py
```

(em Linux/macOS pode ser necessário usar `python3 main.py`)

O sistema inicia **vazio**. Navegue pelo menu numérico:

| Opção | Módulo |
|-------|--------|
| 1 | Tabela de processos (Lista) |
| 2 | Escalonador de CPU (Fila) |
| 3 | Pilha de chamadas/interrupções (Pilha) |
| 4 | Sistema de arquivos (Árvore) |
| 5 | Salvar dados |
| 6 | Carregar dados |
| 0 | Sair (pergunta se deseja salvar) |

Fluxo sugerido: crie processos (1) → enfileire-os informando o PID (2) → execute o próximo para ver o Round-Robin (quantum = 2) → empilhe chamadas (3) → crie diretórios e arquivos (4) → salve (5). Em outra execução, use "Carregar" (6) para reconstruir o estado.

## Justificativa técnica das estruturas

### Lista (`list`) — Tabela de processos ativos
Uma tabela de processos precisa de **inclusão, consulta, alteração e remoção de qualquer elemento**, não só das pontas. A lista permite acesso por índice e busca por chave (PID), além de manter a ordem de criação. Cada processo é um dicionário (`pid`, `nome`, `prioridade`, `estado`).

### Fila (`collections.deque`) — Escalonamento de CPU
O escalonador Round-Robin é naturalmente **FIFO**: o processo que está esperando há mais tempo é o próximo a ocupar a CPU. A inserção ocorre no **fim** (`append`) e a remoção no **início** (`popleft`). Usamos `deque` porque `popleft` é O(1), enquanto `list.pop(0)` é O(n). Ao executar, o processo recebe um quantum; se ainda precisar de CPU, volta ao fim da fila.

### Pilha (`list`) — Chamadas de sub-rotinas e interrupções
Chamadas aninhadas seguem **LIFO**: a última sub-rotina ou interrupção chamada é a primeira a retornar (como o *call stack* real; uma interrupção que ocorre no meio de uma rotina precisa ser tratada antes de a rotina continuar). `append` (push) e `pop` operam no topo em O(1), e só o topo pode ser consultado ou alterado.

### Árvore (dicionários aninhados) — Sistema de arquivos
Diretórios e arquivos formam uma **hierarquia** (um pai, vários filhos). Cada nó é `{"tipo": "DIR"|"ARQ", "filhos": {nome: nó}}`. O dicionário de filhos garante nomes únicos por diretório e acesso direto por nome, e a navegação por caminho (`/home/docs`) é uma descida pela árvore. A exibição usa percurso recursivo em pré-ordem.

## Persistência (`dados_sistema.txt`)

Um único arquivo texto, uma linha por registro, campos separados por `|` (o caractere é bloqueado nas entradas para não corromper o arquivo).

O arquivo **nunca é sobrescrito**: cada salvamento é acrescentado ao final (modo `"a"`) e começa com uma linha `SALVAMENTO|data e hora`. Ao carregar, o sistema reconstrói apenas o **último** salvamento, ou seja, o estado mais recente; os anteriores ficam preservados como histórico.

```
SALVAMENTO|data e hora
LISTA|pid|nome|prioridade|estado
FILA|pid|nome|tempo_restante
PILHA|tipo|descricao                  (gravada da base para o topo)
ARVORE|DIR ou ARQ|nome1|nome2|...     (caminho completo; pais antes dos filhos)
```

Exemplo:

```
SALVAMENTO|2026-11-26 20:49:00
LISTA|1|init|1|Pronto
LISTA|2|shell|2|Novo
FILA|1|init|3
PILHA|SUBROTINA|main
PILHA|INTERRUPCAO|irq_teclado
ARVORE|DIR|home
ARVORE|ARQ|home|notas.txt
```

Ao carregar, as estruturas em memória são esvaziadas e reconstruídas linha a linha a partir do último salvamento; linhas inválidas são ignoradas e contabilizadas, e o contador de PIDs continua após o maior PID lido.

## Estrutura do código (`main.py`)

Funções agrupadas por estrutura (processos, fila, pilha, árvore), seguidas da persistência (`salvar_dados` / `carregar_dados`) e dos menus (`menu_principal` e submenus).
