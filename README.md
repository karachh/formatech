# FORMATECH

Sistema web de controle das formações do Ministério de Formação de um grupo de oração jovem da Renovação Carismática Católica (RCC).

> Disciplina de Construção de Software — Universidade Estadual de Maringá (UEM)
> Curso de Engenharia de Software

## Equipe

| Integrante | RA |
|---|---|
| Cauã Karach Frederico | 140488 |
| Bruno Viana Felix da Silva | 139175 |
| Murilo de Bortoli Agudo | 142085 |

## Objetivo

Substituir o controle hoje feito em planilha, papel e mensagens de grupo pela organização anual da "Perseverança" — a turma que segue uma trilha de formações para se tornar servo do ministério.

O núcleo do sistema é a **alocação de formadores**: mostrar quem já ministrou quais temas, quantas formações cada formador já deu e quem está escalado em cada data do cronograma. Como consequência direta, o sistema também responde qual parte da apostila ainda não foi coberta no ciclo corrente.

## Descrição do software

O FORMATECH é uma aplicação web de uso interno, sem integração com outros sistemas. Principais funcionalidades:

- Cadastro de ciclos, perseverantes, formadores e temas da apostila;
- Montagem do cronograma do ciclo, com escalação de formadores e emissão de avisos não bloqueantes (ex.: formador que já ministrou aquele tema);
- Registro de troca de formador, com histórico;
- Lançamento de presença dos perseverantes em lote (uma tela por encontro);
- Consulta de cobertura da apostila, histórico de temas por formador, carga por formador e frequência da turma;
- Exportação do cronograma do mês em texto simples, para colar no grupo de mensagens do ministério;
- Controle de acesso por dois perfis: coordenador (acesso completo) e formador (acesso de consulta).

Uma decisão arquitetural central orienta o sistema: **regras de qualidade da escala são conselho, nunca lei**. O sistema pode avisar que um formador já ministrou determinado tema, mas nunca bloqueia o registro — a decisão final é sempre humana.

## Arquitetura

- Monolito modular em camadas (apresentação, serviço, repositório, domínio);
- MVC, com páginas renderizadas no servidor (sem API separada);
- Banco de dados relacional;
- Padrões de projeto: Repository, Strategy (avisos de escalação) e Template Method (exportações).

## Tecnologias
- Controle de versão: Git + GitHub
- Acompanhamento: Trello


## Como rodar o projeto

Pré-requisitos: Git, Python 3.10 ou mais novo e Docker (com o Docker Compose).

Rode os comandos na ordem, um por vez.

1. Baixar o código e entrar na pasta:

   - Linux e Windows: `git clone https://github.com/karachh/formatech.git` e depois `cd formatech`


2. Criar o ambiente virtual, uma pasta `.venv` onde ficam as bibliotecas só deste projeto:

   - Linux: `python3 -m venv .venv`
   - Windows: `python -m venv .venv`


3. Ativar o ambiente virtual (repita sempre que abrir um terminal novo):

   - Linux: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate`

   Se o PowerShell recusar com "execução de scripts foi desabilitada", use o Prompt de Comando (cmd).


4. Instalar as bibliotecas do projeto (Django e o driver do PostgreSQL) com o venv ativado:

   - Linux e Windows: `pip install -r requirements.txt`


5. Criar o seu arquivo de configuração a partir do modelo:

   - Linux: `cp .env.example .env`
   - Windows: `copy .env.example .env`

   Abra o `.env` e preencha `DB_PASSWORD` com uma senha qualquer. Esse arquivo fica só na sua máquina e não vai para o GitHub.


6. Subir o banco de dados PostgreSQL em um contêiner (no Windows, o Docker Desktop precisa estar aberto):

   - Linux e Windows: `docker compose up -d`


7. Criar as tabelas no banco:

   - Linux e Windows: `python manage.py migrate`


8. Criar o seu usuário administrador (cada pessoa cria o seu, com o nome e a senha que quiser):

   - Linux e Windows: `python manage.py createsuperuser`


9. Iniciar o servidor:

   - Linux e Windows: `python manage.py runserver`

   Acesse http://127.0.0.1:8000/admin/ e entre com o usuário do passo 8. Para parar o servidor, `Ctrl+C`.


### No dia a dia

Depois da primeira vez, bastam três comandos para voltar a trabalhar:

```bash
source .venv/bin/activate   # ativa o ambiente virtual (no Windows: .venv\Scripts\activate)
docker compose up -d        # sobe o banco
python manage.py runserver  # inicia o servidor
```

Depois de um `git pull`, rode também `pip install -r requirements.txt` e `python manage.py migrate`, para pegar bibliotecas e tabelas novas que os colegas tenham adicionado.

Para desligar o banco: `docker compose down` (os dados são mantidos).

## Links do projeto

- Quadro de acompanhamento (Trello): https://trello.com/b/8z6w9WBW/formatech
- Documento de especificação e arquitetura (Etapa 1): https://docs.google.com/document/d/1J410W6i5ZZJUHrE2-oC42c0n0oSF-nLuWoZoC-7WKz4/edit?tab=t.0
- Backlog do produto e da sprint: 


Projeto acadêmico, desenvolvido para a disciplina de Construção de Software (UEM).
