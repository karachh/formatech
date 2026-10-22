# Histórias implementadas

O que cada história entrega e como foi construída. A especificação diz o que
deveria ser feito; este arquivo registra o que foi feito e por quê.

Cada história tem uma seção com:
- **O que faz:** narrativa e critérios de aceitação.
- **Como foi feita:** as decisões de implementação e o motivo de cada uma.
- **Tarefas:** cada item da checklist do Trello (Tnnn.k), com o mesmo texto da Etapa 3, a situação e onde está no código.
- **Mudanças em relação ao plano:** o que divergiu da Etapa 3 e por quê.

---

## US002 — Abrir um ciclo

**Responsável:** Cauã · **Sprint:** 1 · **RF:** RF002 · **Situação:** em andamento

### O que faz
Como coordenador, quero criar um ciclo anual com data de início e fim, para
organizar as formações da turma daquele ano separadamente das demais.

Critérios de aceitação: um ciclo cadastrado (nome, início e fim) aparece na lista;
um ciclo com datas sobrepostas a outro mostra erro e não é salvo; um ciclo pode ser encerrado.

### Como foi feita
- `Ciclo` herda de `RegistroBase` (`core`), uma classe abstrata: ela não vira tabela,
  só empresta `criado_em` e `atualizado_em` a cada modelo (RN008).
- As regras estruturais ficam na própria tabela (`Meta.constraints`) e valem mesmo
  para gravações que não passam pela tela:
  - CHECK `ciclo_fim_depois_inicio`: o fim vem depois do início.
  - EXCLUDE `ciclo_sem_sobreposicao`: dois ciclos não podem ter períodos que se
    cruzam (RN002). O intervalo é `'[]'`, então o último dia pertence ao ciclo, e um
    ciclo que começa no dia em que outro termina é recusado.
- `Periodo` dá acesso à função `daterange()` do PostgreSQL, usada pela EXCLUDE.
- Mensagens amigáveis: o `clean()` aponta o erro no campo `fim`, e a EXCLUDE tem
  `violation_error_message` ("Já existe um ciclo nesse período."). O `clean()` também
  evita um `DataError`: sem ele, a validação de sobreposição montaria um `daterange`
  com o fim antes do início, e o PostgreSQL recusaria a consulta.
- O admin (`CicloAdmin`) é só ferramenta de desenvolvimento. Ele permite apagar
  ciclos, o que o RF002 não prevê.

### Tarefas
| Tarefa | Situação | Onde |
|---|---|---|
| T002.1 Criar a classe abstrata RegistroBase no core (criado_em / atualizado_em — RN008) | Feita | `core/models.py` |
| T002.2 Criar o model Ciclo (nome, inicio, fim) + CheckConstraint + ExclusionConstraint (RN002) + migration | Feita | `cadastros/models.py`, `cadastros/migrations/0001_initial.py` |
| T002.3 Criar repositório de ciclos (listar, salvar) | Pendente | |
| T002.4 Criar serviço abrir_ciclo, que traduz a recusa de sobreposição do banco (RN002) em mensagem | Pendente | |
| T002.5 Criar tela de lista e cadastro de ciclos (form, view, template, urls) | Pendente | |
| T002.6 Testes da regra de sobreposição (inclui datas que se encostam e fim antes do início) | Feita no modelo e no banco (12 testes); faltam os do serviço | `cadastros/tests/test_ciclo.py` |
| T002.7 Permitir encerrar um ciclo (situação aberto/encerrado + ação na tela — RF002) | Pendente | |

### Mudanças em relação ao plano
- A RN002 é garantida no banco (EXCLUDE), como definido no seminário da Etapa 2.
  O texto da Etapa 3 previa só a CheckConstraint na T002.2 e a verificação de
  sobreposição no repositório e no serviço. Com a EXCLUDE, o repositório (T002.3)
  só lista e salva, e o serviço (T002.4) traduz a recusa do banco em mensagem.
- Campos `inicio` e `fim` em vez de `data_inicio` e `data_fim`, seguindo a regra de
  nomes do `AGENTS.md`.
