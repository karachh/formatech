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


## Links do projeto

- Quadro de acompanhamento (Trello): 
- Documento de especificação e arquitetura (Etapa 1): 
- Backlog do produto e da sprint: 


Projeto acadêmico, desenvolvido para a disciplina de Construção de Software (UEM).
