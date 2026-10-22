# AGENTS.md — FORMATECH

Instruções para quem constrói neste repositório, seja pessoa ou agente de IA (Claude, Copilot, Cursor etc.). Este arquivo descreve **como** trabalhar aqui. O **o quê** está nos documentos da disciplina e no Trello.

## Fontes de verdade

| O quê | Onde |
|---|---|
| Requisitos (RF), regras de negócio (RN), arquitetura | Especificação da Etapa 1 (link no README) |
| Decisão sobre o banco e suas restrições | Seminário da Etapa 2 |
| Esquema do banco | os `models.py` de cada app (as migrações geram as tabelas) |
| Exemplos de SQL do seminário da Etapa 2 (não são o esquema oficial) | [banco/](banco/) |
| Histórias, responsáveis e andamento | Trello: https://trello.com/b/8z6w9WBW/formatech |
| O que cada história entregou e como foi feita | [HISTORIAS.md](HISTORIAS.md) |
| Como rodar o projeto | [README.md](README.md) |

Se o código e a especificação divergirem, **pare e avise a equipe** em vez de escolher um lado em silêncio. Mudanças de decisão são permitidas, desde que registradas e justificadas.

## Stack

Python 3.10+, Django 5.2, PostgreSQL rodando em Docker (`docker compose`), `django-environ` para ler o `.env`. As páginas são renderizadas no servidor com templates do Django. **Não há API separada nem frontend em JavaScript.**

## Arquitetura: regras que não se quebram

O sistema é um monolito modular em camadas. Cada app do Django é um módulo de domínio:

| App | Entidades | Responsável por |
|---|---|---|
| `acesso` | `Usuario` | login e perfis (coordenador / formador) |
| `cadastros` | `Ciclo`, `Perseverante`, `Formador`, `Tema` | cadastros de base |
| `core` | `RegistroBase` (abstrata) | o que é compartilhado por todos os módulos |

Os módulos Cronograma, Presença e Relatórios ainda não existem. Cada um vira uma app nova quando a primeira história dele começar. Crie com `python manage.py startapp <nome>`, siga a mesma estrutura de arquivos das apps atuais e registre a app em `INSTALLED_APPS`.

Dentro de cada app, as camadas são:

- `views.py`: recebe a requisição, chama o serviço e devolve o template. **Não decide nada.**
- `services.py`: regra de negócio. **Nunca recebe `request`** e não escreve consultas ao banco.
- `repositories.py`: **o único lugar** que usa o ORM (`Modelo.objects...`).
- `models.py`: entidades e as restrições do banco.

Regras de negócio que afetam o código:

- **RN008:** todo modelo herda de `RegistroBase`, que traz `criado_em` e `atualizado_em`.
- **Restrições estruturais ficam no modelo**, em `Meta.constraints` (`CheckConstraint`, `UniqueConstraint`, `ExclusionConstraint`). Não as espalhe em validações de tela. A tela só traduz o erro do banco numa mensagem amigável.
- **RN001:** as regras de qualidade da escala (por exemplo, "formador já deu este tema") são **aviso, nunca bloqueio**. Elas não viram constraint nem exceção: o serviço devolve uma lista de avisos junto com o registro já salvo.
- **RN006:** nada que possa ser calculado é armazenado. Nada de contadores ou campos de "total".
- **NFR001:** gravação em lote (presença) acontece dentro de `transaction.atomic()`.
- **Nomes em português**, curtos e sem prefixo de tipo (`inicio`, `fim`, `situacao`, `formador`...).

## Fluxo de trabalho: da branch ao merge

### 1. Pegar a história
No Trello, mova o cartão da história de **Backlog da sprint** para **Em desenvolvimento** e confira se o seu nome está nele. Trabalhe uma história por vez.

### 2. Criar a branch a partir da `main` atualizada
```bash
git switch main
git pull
git switch -c us002-ciclo        # padrão: us<número>-<palavra-chave>
```
Nunca faça commit direto na `main`.

### 3. Construir em passos pequenos
Antes de abrir o PR, cada passo tem que estar funcionando:
```bash
python manage.py check          # "System check identified no issues"
python manage.py test           # todos os testes passando
```

### 4. Migrações (o ponto onde três pessoas mais se atrapalham)
- **Antes** de rodar `makemigrations`, traga a `main` atualizada para a sua branch com `git pull origin main`.
- Rode `python manage.py makemigrations <app>` e **leia o arquivo gerado** antes de commitar.
- Faça commit da migração **junto** com o modelo que ela descreve.
- **Nunca edite uma migração que já está na `main`.** Para corrigir, crie uma migração nova.
- Se a migração der conflito com a de um colega (dois arquivos `0002_...`): apague a **sua** migração, que ainda não foi para a `main`, traga a `main` e gere de novo.
- Não altere o banco à mão pelo `psql` ou por uma ferramenta gráfica. Toda mudança de esquema passa por migração.

### 5. Commits
Cada commit é pequeno, roda sozinho e cita a tarefa:
```
T002.1: cria RegistroBase com criado_em e atualizado_em
```
Antes de cada commit, rode `git status` e confira que **nada** destes está entrando: `.env`, `.venv/`, `db.sqlite3`, dumps e backups. O histórico do Git é permanente.

### 6. Subir e abrir o Pull Request
Antes de abrir o PR, atualize a seção da história em [HISTORIAS.md](HISTORIAS.md):
a situação de cada tarefa, as decisões de implementação e as mudanças em relação
ao plano. A atualização vai no mesmo PR que o código, para o revisor conferir as duas coisas juntas.

```bash
git push -u origin us002-ciclo
```
No GitHub, abra um PR para a `main` com:
- **Título:** `US002 — Abrir um ciclo`
- **Descrição:** o que foi feito, as tarefas cobertas (T002.x), o link do cartão do Trello e **como testar** (passo a passo para quem vai revisar), mencionando se há migração nova.
- **Revisor:** pelo menos um colega da equipe.

No Trello, coloque o link do PR no cartão.

### 7. Revisão
Quem revisa baixa a branch, roda `migrate` e `test`, e testa o critério de aceitação da história na tela. A ordem de prioridade da revisão:
1. Faz o que a história pede?
2. Respeita as camadas e as regras acima?
3. Só depois disso: nomes e estilo.

O autor corrige na mesma branch e faz push de novo. O PR atualiza sozinho.

### 8. Merge
- Só faça merge com **aprovação de um colega** e com os testes passando.
- Use **"Squash and merge"**: a história vira um único commit na `main`.
- Depois de mesclar, apague a branch, no GitHub e na sua máquina:
  ```bash
  git switch main && git pull
  git branch -d us002-ciclo
  ```
- Mova o cartão para **Concluído**.
- Avise no grupo quando o PR trouxer migração nova. Os colegas precisam rodar `python manage.py migrate` depois do próximo `git pull`.

## Regras para agentes de IA

- Leia este arquivo e a história do Trello antes de propor código.
- Não rode comandos destrutivos (`rm -rf`, `DROP`, `git reset --hard`, `push --force`) sem confirmação explícita.
- Não faça commit, push nem merge sem que o integrante peça.
- Não leia nem exiba o conteúdo do `.env`.
- Não fazer tudo sozinho. Sempre avise o desenvolvedor sobre a importância de entender o código e o que está sendo construído, e que ele terá que apresentar ao professor. Esse projeto prioriza o aprendizado sobre a entrega.
