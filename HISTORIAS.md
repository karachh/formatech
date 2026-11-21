# Histórias implementadas

O que cada história entrega e como foi construída. A especificação diz o que
deveria ser feito; este arquivo registra o que foi feito e por quê.

Cada história tem uma seção com:
- **O que faz:** narrativa e critérios de aceitação.
- **Como foi feita:** as decisões de implementação e o motivo de cada uma.
- **Tarefas:** cada item da checklist do Trello (Tnnn.k), com o mesmo texto da Etapa 3, a situação e onde está no código.
- **Mudanças em relação ao plano:** o que divergiu da Etapa 3 e por quê.

---

---

## US001 — Login no sistema

**Responsável:** Murilo · **Sprint:** 1 · **RF:** RF001 · **Situação:** finalizado

### O que faz
Como coordenador ou formador, quero entrar no sistema com login e senha, para
acessar apenas as telas permitidas ao meu perfil.

Critérios de aceitação: o login com usuário e senha cadastrados abre a tela inicial
do perfil (o coordenador vê o menu completo; o formador vê apenas o cronograma e os
temas que já ministrou); tentar acessar uma tela sem estar logado redireciona para a
tela de login. A senha é armazenada com hash (NFS001).

### Como foi feita
- `Usuario` herda de `RegistroBase` (RN008) e de `AbstractUser`, que traz usuário,
  e-mail e a senha com hash do Django. O campo `perfil` usa `TextChoices`
  (coordenador/formador), com `formador` como padrão por ser o perfil de menor
  privilégio. O CHECK `usuario_perfil_valido` impede outro valor gravado por fora,
  porque `choices` só vale nos formulários.
- Não existe tela de cadastro: o sistema é de uso interno, e os usuários são criados
  pelo coordenador no admin. Uma tela pública de cadastro deixaria qualquer pessoa
  criar conta.
- O login segue as camadas do AGENTS.md:
  - `LoginForm` só converte o que veio da tela.
  - `repositories.autenticar_usuario` chama `authenticate()`, que consulta o banco.
  - `services.autenticar` devolve o usuário ou levanta `ValidationError` com a
    mensagem "Usuário ou senha inválidos.", genérica de propósito: não revela se o
    erro foi no usuário ou na senha. O serviço não recebe `request`.
  - A view chama o serviço e, em seguida, `login()` do Django, que grava a sessão e
    por isso precisa do `request`. Os apelidos `login_django` e `logout_django`
    evitam que o import seja sobrescrito pelas views de mesmo nome.
- O logout só aceita POST (`@require_POST`): um GET (link, pré-carregamento do
  navegador) não pode encerrar a sessão. O botão "Sair" é um formulário com CSRF.
- Login obrigatório em todas as telas pelo `LoginRequiredMiddleware` do Django
  (5.1+), colocado depois do `AuthenticationMiddleware`. Esquecer de proteger uma
  tela deixa de ser possível: as telas dos próximos módulos já nascem protegidas, e só
  a tela de login é liberada, com `@login_not_required`. O destino do redirecionamento
  vem de `LOGIN_URL`.
- O perfil é verificado por view, com o decorator `coordenador_required`: anônimo vai
  ao login (middleware) e formador recebe 403, porque já está autenticado e falta
  permissão, não identidade. Foi aplicado às três telas de ciclos, que são cadastro de
  base.
- Esconder um link no menu não protege a tela: quem digita a URL ignora o menu. A
  proteção real é o decorator; o menu é só conveniência.
- A tela inicial (`acesso:home`) estende `core/base.html` e mostra o menu conforme
  `user.perfil`.

### Tarefas
| Tarefa | Situação | Onde |
|---|---|---|
| T001.1 Configurar autenticação do Django (LOGIN_URL, views de login e logout) | Feita | `config/settings.py`, `acesso/forms.py`, `acesso/repositories.py`, `acesso/services.py`, `acesso/views.py`, `acesso/urls.py`, `config/urls.py` |
| T001.2 Adicionar perfil (coordenador/formador) ao modelo Usuario + migration | Feita | `acesso/models.py`, `acesso/admin.py`, `acesso/migrations/0002_alter_usuario_options_usuario_atualizado_em_and_more.py` |
| T001.3 Criar o template da tela de login | Feita | `acesso/templates/acesso/login.html` |
| T001.4 Exigir login em todas as telas e restringir telas por perfil | Feita | `config/settings.py` (middleware), `acesso/decorators.py`, `cadastros/views.py` |
| T001.5 Criar tela inicial com menu conforme o perfil | Feita, com links provisórios (ver abaixo) | `acesso/templates/acesso/home.html`, `acesso/views.py` |
| T001.6 Testes: redirecionamento sem login, menu por perfil e senha com hash (NFS001) | Feita (11 testes) | `acesso/tests/test_autenticacao.py` |

### Mudanças em relação ao plano
- A T001.1 não cita as camadas de serviço e repositório, mas o AGENTS.md as exige;
  por isso o login foi dividido em formulário, repositório, serviço e view.
- A migração da T001.2 inclui `criado_em` e `atualizado_em` (RN008), além do `perfil`.
  Como a tabela já tinha usuários, o Django pediu um valor padrão para as linhas
  existentes (`timezone.now`).
- Na T001.4, o login é exigido por middleware global, e não por `@login_required` em
  cada view, e a restrição por perfil foi aplicada em `cadastros/views.py`, arquivo de
  outra história. Os testes de ciclos (`cadastros/tests/test_tela_ciclos.py`) passaram
  a entrar como coordenador, com o mixin `ComoCoordenador`.
- Na T001.5, só "Ciclos" tem rota real. Os demais links do menu (`#`) serão ligados
  quando as telas existirem. "Temas que já ministrei" depende do vínculo entre
  `Usuario` e `Formador`, que não existe ainda (o model `Formador` é de outra história).
  Esse vínculo precisa ser decidido pela equipe.
- O botão "Sair" está na home. Quando houver um menu global no `base.html`, ele pode
  migrar para lá.

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
- O repositório converte a recusa da EXCLUDE em `PeriodoOcupado`, identificando a
  restrição pelo nome que o psycopg informa, e grava dentro de `transaction.atomic()`.
- O serviço valida com `clean_fields()` e `clean()`, sem `full_clean()`, porque este
  consulta o banco e o NFM001 exige regra testável sem banco. Os testes do serviço usam
  `SimpleTestCase`, que proíbe consultas, com o repositório substituído por um dublê.
- Encerrar (T002.7): `situacao` usa `TextChoices` e tem o CHECK `ciclo_situacao_valida`,
  porque `choices` só vale nos formulários. A view só aceita POST (GET recebe 405),
  ciclo inexistente dá 404 e encerrar um ciclo já encerrado mostra mensagem de erro.
- Editar (T002.8): ciclo encerrado só tem o nome alterado. As datas definem quais
  formações pertencem ao ciclo (RN002), por isso ficam congeladas após o encerramento.
  A regra fica em `Ciclo.datas_editaveis`; o formulário desabilita as datas e o serviço
  recusa a mudança mesmo que ela chegue. Abrir e editar compartilham `_validar_e_salvar`.

### Tarefas
| Tarefa | Situação | Onde |
|---|---|---|
| T002.1 Criar a classe abstrata RegistroBase no core (criado_em / atualizado_em — RN008) | Feita | `core/models.py` |
| T002.2 Criar o model Ciclo (nome, inicio, fim) + CheckConstraint + ExclusionConstraint (RN002) + migration | Feita | `cadastros/models.py`, `cadastros/migrations/0001_initial.py` |
| T002.3 Criar repositório de ciclos (listar, salvar) | Feita | `cadastros/repositories.py` |
| T002.4 Criar serviço abrir_ciclo, que traduz a recusa de sobreposição do banco (RN002) em mensagem | Feita | `cadastros/services.py` |
| T002.5 Criar tela de lista e cadastro de ciclos (form, view, template, urls) | Feita | `cadastros/forms.py`, `cadastros/views.py`, `cadastros/templates/cadastros/ciclos.html`, `core/templates/core/base.html` |
| T002.6 Testes da regra de sobreposição (inclui datas que se encostam e fim antes do início) | Feita (22 testes: modelo, banco, repositório e serviço) | `cadastros/tests/` |
| T002.7 Permitir encerrar um ciclo (situação aberto/encerrado + ação na tela — RF002) | Feita | `cadastros/models.py`, `cadastros/migrations/0002_ciclo_situacao.py`, `services.encerrar_ciclo`, `views.encerrar_ciclo` |
| T002.8 Permitir editar um ciclo (nome e datas — RF002) | Feita | `Ciclo.datas_editaveis`, `services.editar_ciclo`, `views.editar_ciclo`, `cadastros/templates/cadastros/editar_ciclo.html` |

### Mudanças em relação ao plano
- A RN002 é garantida no banco (EXCLUDE), como definido no seminário da Etapa 2.
  O texto da Etapa 3 previa só a CheckConstraint na T002.2 e a verificação de
  sobreposição no repositório e no serviço. Com a EXCLUDE, o repositório (T002.3)
  só lista e salva, e o serviço (T002.4) traduz a recusa do banco em mensagem.
- Campos `inicio` e `fim` em vez de `data_inicio` e `data_fim`, seguindo a regra de
  nomes do `AGENTS.md`.
- T002.8 (editar ciclo) incluída em 26/10: o RF002 prevê "criar, consultar, editar e
  encerrar", e nenhuma tarefa cobria a edição.


## US003 — Cadastrar formadores

**Responsável:** Bruno · **Sprint:** 1 · **RF:** RF003 · **Situação:** concluída; mesclada na `main` (PR #6, junto com a US004); os 21 testes passam desde a correção de 03/11/2026

### O que faz
Como coordenador, quero cadastrar, editar e inativar formadores, para manter a lista
de pessoas que podem ser escaladas nas formações. A lista apresenta formadores ativos
e inativos com a situação identificada.

### Como foi feita
- `Formador` herda de `RegistroBase`, tem nome, início de serviço obrigatório,
  indicação de capacitação e estado ativo (T003.1). Novos registros começam ativos.
- `Usuario` e `Formador` continuam sem relacionamento. A contagem de formações e a
  lista de temas não são armazenadas, conforme RN006. A edição não reativa registros.
- O repositório concentra listar, buscar, salvar e inativar; o serviço valida os dados
  sem receber `request` nem acessar diretamente o ORM.
- As telas e operações são restritas a coordenadores. A inativação é lógica, aceita
  somente POST e mantém o registro visível na listagem com estado "Inativo".

### Tarefas
| Tarefa | Situação | Onde |
|---|---|---|
| T003.1 Criar o model Formador + migration | Feita | `cadastros/models.py`, `cadastros/migrations/0004_formador.py` |
| T003.2 Criar repositório e serviço de formadores (listar, salvar, inativar) | Feita | `cadastros/repositories.py`, `cadastros/services.py` |
| T003.3 Criar telas de lista, cadastro e edição de formador | Feita | `cadastros/forms.py`, `cadastros/views.py`, `cadastros/urls.py`, `cadastros/templates/cadastros/formadores.html`, `cadastros/templates/cadastros/editar_formador.html` |
| T003.4 Implementar inativação lógica | Feita | `cadastros/services.py`, `cadastros/repositories.py`, `cadastros/views.py`, `cadastros/templates/cadastros/formadores.html` |
| T003.5 Testes do cadastro e da inativação | Feita (21 testes, todos passando em 03/11/2026) | `cadastros/tests/test_formador.py` |

### Mudanças em relação ao plano
- A relação entre `Usuario` e `Formador` permaneceu fora do escopo, pois não foi
  confirmada pela equipe.
- A listagem inclui ambos os estados; a ação de inativar aparece apenas para registros
  ativos. Não há ação de reativação.
- A US003 e a US004 foram entregues juntas, num único commit e num único PR (#6),
  em vez de um commit por tarefa e uma branch por história, como pede o AGENTS.md.

### Correção pós-merge (branch `fix-us003-us004-testes`, 03/11/2026)
- O PR #6 foi mesclado sem os testes rodados (o banco de teste não subia) e sem
  revisão de um colega. Na primeira execução completa, falharam
  `test_cadastrar_mostra_formador_ativo_na_lista` e
  `test_inativar_por_post_preserva_registro`.
- Causa: as mensagens usavam aspas retas (`"Ana"`), que o template escapa para
  `&quot;Ana&quot;`, e o `assertContains` compara o texto cru. A tela funcionava.
- Correção: as mensagens de formador e de perseverante (views e serviços) passaram
  a usar aspas curvas (`“Ana”`), como as telas de ciclo e de tema, que não são
  escapadas. Os testes foram ajustados ao novo texto.

### Pendências
- ~~Não existe `listar_formadores_ativos()`.~~ Resolvida na US006: a função existe
  em `cadastros/repositories.py` e `cadastros/services.py`, e a escolha de formador do
  cronograma só oferece ativos. A escalação (US007) deve usar a mesma função.



---

## US005 — Cadastrar temas da apostila

**Responsável:** Murilo · **Sprint:** 1 · **RF:** RF005 · **Situação:** concluída; mesclada na `main` (PR #5); os 14 testes passam (revisão de 03/11/2026)

### O que faz
Como coordenador, quero cadastrar temas classificando cada um como obrigatório
(apostila) ou opcional, para que o sistema saiba o que entra na cobertura da apostila.

Critérios de aceitação: o cadastro de tema com classificação apostila/opcional aparece
na lista de temas e fica disponível para escolher na montagem do cronograma.

### Como foi feita
- `Tema` herda de `RegistroBase` (RN008). O campo `tipo` usa `TextChoices`
  (apostila/opcional) e tem o CHECK `tema_tipo_valido`, porque `choices` só vale nos
  formulários. O `rotulo` é opcional e guarda o número da apostila (1 ou 2).
- O `nome` é único (`tema_nome_unico`): a regra fica no banco e vale mesmo para
  gravações que não passam pela tela. O repositório identifica a restrição pelo nome
  que o psycopg informa e a converte em `NomeDeTemaEmUso`; o serviço a traduz na
  mensagem "Já existe um tema com esse nome.".
- Camadas do AGENTS.md: o formulário só converte o que veio da tela; o serviço
  (`cadastrar_tema`, `editar_tema`) valida com `clean_fields()`, sem `full_clean()`,
  e não recebe `request`; só o repositório usa o ORM; a view chama o serviço e traduz
  o `ValidationError` em erro do formulário.
- As telas (lista com cadastro, e edição) exigem `@coordenador_required`: anônimo vai
  ao login e formador recebe 403. A exclusão não existe, pois o RF005 não a prevê.
- A carga inicial é o comando `python manage.py carregar_temas`, que lê
  `cadastros/dados/temas.csv` (26 temas, separador `;`, UTF-8). O serviço
  `carregar_temas` só cria os que ainda não existem, então o comando pode rodar
  várias vezes sem duplicar.
- O link "Temas" da home do coordenador passou a apontar para `/temas/`.

### Tarefas
| Tarefa | Situação | Onde |
|---|---|---|
| T005.1 Criar o model Tema (nome, tipo apostila/opcional, rótulo da apostila) + migration | Feita | `cadastros/models.py`, `cadastros/admin.py`, `cadastros/migrations/0003_tema.py` |
| T005.2 Criar repositório e serviço de temas | Feita | `cadastros/repositories.py`, `cadastros/services.py` |
| T005.3 Criar telas de lista, cadastro e edição de tema | Feita | `cadastros/forms.py`, `cadastros/views.py`, `cadastros/urls.py`, `cadastros/templates/cadastros/temas.html`, `cadastros/templates/cadastros/editar_tema.html` |
| T005.4 Carregar os temas reais da apostila (carga inicial) | Feita (26 temas) | `cadastros/management/commands/carregar_temas.py`, `cadastros/dados/temas.csv` |
| T005.5 Testes do cadastro e da classificação | Feita (14 testes) | `cadastros/tests/test_temas.py` |

### Mudanças em relação ao plano
- O campo se chama `nome`, como no Trello e em `Ciclo.nome`, e não `titulo`, como no
  `banco/schema.sql` (exemplo do seminário, não o esquema oficial).
- Unicidade do nome e rótulo opcional foram decisões nossas: a tarefa não as
  especifica. O rótulo guarda só o número da apostila.
- **Por que o rótulo não é obrigatório, se a RF005 diz "registrando o rótulo"
  (revisão de 03/11/2026):** o rótulo é informativo. A cobertura da apostila (RF010)
  separa os temas pelo `tipo`, não pelo rótulo. Os temas reais entram pela carga
  inicial, todos com rótulo, e a apostila praticamente não muda. Por isso não foi
  criada a restrição "apostila exige rótulo; opcional não tem rótulo".
- **Limite conhecido:** a unicidade do nome diferencia maiúsculas de minúsculas.
  "Sagrada Tradição" e "SAGRADA TRADIÇÃO" podem coexistir, e um tema da apostila
  duplicado assim apareceria sempre como "não alocado" na cobertura. O risco foi
  aceito porque temas novos são raros. A correção, se necessária, é uma
  `UniqueConstraint` sobre `Lower("nome")`.
- Não há exclusão de tema: a RF005 pede só cadastrar, consultar e editar. A seção
  3.1.6 da especificação cita "exclusão lógica" para todos os cadastros, mas a RF005,
  que é mais específica, prevaleceu.
- O vínculo do tema com a montagem do cronograma ("fica disponível para escolher")
  depende do módulo Cronograma, que ainda não existe. Esta história entrega a lista
  de temas que ele vai consumir.
- A edição de tema (T005.3) não altera o `HISTORIAS.md` da US001: os links de menu
  continuam provisórios, exceto "Temas".


## US004 — Cadastrar perseverantes do ciclo

**Responsável:** Bruno · **Sprint:** 1 · **RF:** RF004 · **Situação:** concluída; mesclada na `main` (PR #6, junto com a US003); exclusão a pedido (T004.4) feita em 03/11/2026; os 26 testes passam

### O que faz
Permite ao coordenador cadastrar, editar, consultar por ciclo, inativar e excluir a
pedido os perseverantes. A consulta pode mostrar ativos e inativos; a inativação
preserva o registro, e a exclusão a pedido o apaga.

### Como foi feita
- `Perseverante` herda de `RegistroBase` e contém somente nome, ciclo obrigatório e
  estado ativo, iniciado como verdadeiro. A FK usa `PROTECT`, evitando apagar um ciclo
  que tenha perseverantes associados.
- O repositório oferece listagem por ciclo e uma consulta separada que retorna apenas
  ativos, para eventual consumo futuro pela grade de presença. A grade não existe e
  não foi implementada nem declarada como integrada.
- Cadastro e edição resolvem o ciclo no serviço; somente os repositórios consultam o
  ORM. As operações de tela são protegidas para coordenadores; inativação é POST.
- Exclusão a pedido (NFC002): o botão "Excluir a pedido" faz um POST para
  `perseverantes/<id>/excluir/`. O serviço `excluir_perseverante` busca o registro e
  pede ao repositório que o apague (`delete()`). Funciona para ativos e inativos.
  A tela avisa que a ação é definitiva, e a mensagem de sucesso não repete o nome.
- Não foram adicionados campos de dados pessoais além do nome, nem campos de contagem
  ou presença (NFC001, RN006).

### Tarefas
| Tarefa | Situação | Onde |
|---|---|---|
| T004.1 Criar o model Perseverante (nome, ciclo, ativo) + migration | Feita | `cadastros/models.py`, `cadastros/migrations/0005_perseverante.py` |
| T004.2 Criar repositório e serviço de perseverantes | Feita | `cadastros/repositories.py`, `cadastros/services.py` |
| T004.3 Criar telas de lista (filtrada por ciclo), cadastro e edição | Feita | `cadastros/forms.py`, `cadastros/views.py`, `cadastros/urls.py`, `cadastros/templates/cadastros/perseverantes.html`, `cadastros/templates/cadastros/editar_perseverante.html` |
| T004.4 Implementar inativação e exclusão a pedido (LGPD — NFC002) | Feita (exclusão em 03/11/2026) | `cadastros/repositories.py`, `cadastros/services.py`, `cadastros/views.py`, `cadastros/urls.py`, `cadastros/templates/cadastros/perseverantes.html` |
| T004.5 Testes do cadastro de perseverantes | Feita (26 testes) | `cadastros/tests/test_perseverante.py` |

### Decisões
- **Exclusão a pedido apaga o registro, não anonimiza.** É o que a NFC002 da
  especificação determina, com a ressalva registrada de que a exclusão remove também
  as presenças. A anonimização foi considerada e descartada: numa turma de cerca de
  20 pessoas, o registro continuaria identificável pela ordem de cadastro e pelo
  histórico de presença.
- **Para o módulo Presença:** a FK de Presença para Perseverante deve usar
  `on_delete=CASCADE`, para que a exclusão a pedido apague as presenças, como manda a
  NFC002. Com `PROTECT`, a exclusão de quem já tem presença seria bloqueada.

### Validação
- Em 03/11/2026, com o PostgreSQL no ar, `manage.py check` não acusou problemas e os
  26 testes de `cadastros/tests/test_perseverante.py` passaram (suíte completa: 123).
- As migrações `0004_formador` e `0005_perseverante` estão aplicadas no banco de
  desenvolvimento. A exclusão a pedido não exigiu migração.

### Correção pós-merge (branch `fix-us003-us004-testes`, 03/11/2026)
- As mensagens passaram a usar aspas curvas, pela mesma causa descrita na US003.
- `test_anonimo_e_redirecionado` falhava (200 em vez de 302): o `postar()` usa
  `follow=True` e seguia o redirecionamento até a página de login. O teste passou a
  fazer o POST direto, sem `follow`, como o teste equivalente de formador. O
  `postar()` continua com `follow=True`, porque os testes de cadastro precisam ler a
  mensagem na página final.

### Pendências
- ~~O critério "imediatamente disponível na grade de presença" só pode ser verificado
  quando o módulo Presença existir.~~ Resolvida na US014: a grade usa
  `listar_perseverantes_ativos`, e o teste `test_lista_os_ativos_do_ciclo_com_presente_marcado`
  confirma que um perseverante ativo do ciclo aparece na grade.

---

## US006 — Montar o cronograma do ciclo

**Responsável:** Cauã · **Sprint:** 1 (entregue na Sprint 2) · **RF:** RF006 · **Situação:** em revisão (branch `us006-montar-cronograma-do-ciclo`); 23 testes novos, suíte completa com 146 passando (03/11/2026)

### O que faz
Como coordenador, quero agendar formações informando data, tema e formador, para ter o
cronograma completo do ciclo em um só lugar.

Critério de aceitação: cadastrar uma formação com data, tema e formador faz ela
aparecer no cronograma, em ordem cronológica, com data, tema, formador e situação
visíveis.

### Como foi feita
- Nova app `cronograma`, registrada em `INSTALLED_APPS`, com as mesmas camadas das
  outras (views → services → repositories → models).
- `Formacao` herda de `RegistroBase` (RN008) e tem `data`, `tema` (opcional),
  `formador` (opcional), `situacao` e `descricao`. A situação usa `TextChoices`
  (prevista, realizada, cancelada) e tem o CHECK `formacao_situacao_valida`, como o
  `tipo` do tema. As FKs para tema e formador usam `PROTECT`: não se apaga um tema ou
  formador que já está no cronograma.
- **O ciclo não é guardado na formação (RN002).** Ele é derivado da data: o
  repositório lista as formações com `data` entre `inicio` e `fim` do ciclo, e o
  serviço descobre o ciclo de uma data com `buscar_ciclo_da_data`. Isso funciona
  porque os ciclos não se sobrepõem (`ExclusionConstraint` da US002).
- Uma data fora de qualquer ciclo é recusada com a mensagem "Não há ciclo cadastrado
  para esta data." É bloqueio, e não aviso, porque sem ciclo a formação não aparece
  em cronograma nenhum (não é regra de qualidade da escala, então a RN001 não se
  aplica).
- O serviço `agendar_formacao` sempre grava a situação "prevista" (T006.3). O
  `editar_formacao` muda só data, tema e descrição: a troca de formador precisa ficar
  registrada (RN007, US009) e a mudança de situação é da US007, então a tela de edição
  mostra os dois apenas para leitura.
- O serviço do cronograma usa a app `cadastros` pelos serviços dela
  (`buscar_ciclo_da_data`, `buscar_tema`, `buscar_formador`,
  `listar_formadores_ativos`), nunca pelos modelos ou pelo ORM diretamente.
- A escolha de formador só oferece formadores ativos, e o serviço recusa um formador
  inativo mesmo que o ID chegue por outro caminho. A escolha de tema separa "Temas da
  apostila" e "Temas opcionais".
- A tela `/cronograma/` mostra o ciclo de hoje, ou o escolhido no filtro, com o
  formulário de agendamento. Depois de agendar, volta ao ciclo da formação. O
  formulário não pede o ciclo.
- O link "Cronograma" da home do coordenador passou a apontar para `/cronograma/`.

### Tarefas
| Tarefa | Situação | Onde |
|---|---|---|
| T006.1 Criar o model Formacao (data, tema opcional, formador, situação, descrição) + migration | Feita | `cronograma/models.py`, `cronograma/admin.py`, `cronograma/migrations/0001_initial.py` |
| T006.2 Criar repositório de formações por ciclo, derivando o ciclo pela data (RN002) | Feita | `cronograma/repositories.py`; `buscar_ciclo_da_data` em `cadastros/repositories.py` e `cadastros/services.py` |
| T006.3 Criar serviço de agendamento (situação inicial "prevista") | Feita | `cronograma/services.py` |
| T006.4 Criar tela do cronograma em ordem cronológica (data, tema, formador, situação) | Feita | `cronograma/views.py`, `cronograma/urls.py`, `cronograma/templates/cronograma/cronograma.html`, `config/urls.py` |
| T006.5 Criar formulário de inclusão e edição de formação | Feita | `cronograma/forms.py`, `cronograma/templates/cronograma/editar_formacao.html` |
| T006.6 Testes: ordem cronológica, derivação do ciclo e situação inicial | Feita (23 testes) | `cronograma/tests/test_formacao.py` (21), `cadastros/tests/test_consultas_para_cronograma.py` (2) |

### Mudanças em relação ao plano
- **Formador opcional.** A T006.1 lista o formador sem "opcional", mas a US007
  (escalar formador) pressupõe formações ainda sem formador. A tela mostra "A
  escalar" nesses casos.
- **A edição não troca o formador nem a situação.** Ficam para a US007 e a US009,
  que registram a troca (RN007).
- Sem exclusão de formação: a RF006 não a pede. Uma formação que não vai acontecer
  deve ser marcada como cancelada (US007).
- Os avisos de qualidade da escala (RN001, US008) não entram aqui: o agendamento não
  devolve lista de avisos.

### Validação
- Em 03/11/2026, `manage.py check` não acusou problemas, `makemigrations --check`
  não encontrou mudanças pendentes e a suíte completa (146 testes) passou.
- **Migração nova:** `cronograma/0001_initial`. Quem baixar a branch precisa rodar
  `python manage.py migrate`.


## US007 — Escalar formador e alterar situação da formação

**Responsável:** Bruno · **Sprint:** 2 · **Situação:** em desenvolvimento (branch `us007-escalar-formador`)

### O que faz
Como coordenador, quero escalar um formador para uma formação e alterar sua
situação entre prevista, realizada e cancelada, para manter o cronograma atualizado.

### Como foi feita
- A escalação usa os serviços e repositórios do cronograma, oferecendo formadores
  ativos e impedindo substituir um formador já escalado. A consulta de temas
  ministrados e carga do ciclo é informativa; cancelar formações não conta na carga.
- A alteração da situação valida no serviço os três valores definidos pelo modelo
  e persiste pelo repositório, sem introduzir migração. No cronograma, a ação usa
  formulário POST com CSRF e é restrita ao coordenador.

### Tarefas
| Tarefa | Situação | Onde |
|---|---|---|
| T007.1 Implementar escalação de formador | Feita (commit `ad0394e`) | `cronograma/services.py`, `cronograma/repositories.py`, `cronograma/forms.py`, `cronograma/views.py`, `cronograma/templates/cronograma/` |
| T007.2 Serviço de alteração de situação | Feita | `cronograma/services.py` |
| T007.3 Alteração de situação pelo cronograma | Feita | `cronograma/forms.py`, `cronograma/views.py`, `cronograma/urls.py`, `cronograma/templates/cronograma/cronograma.html` |
| T007.4 Testes da US007 | Feita (8 testes novos) | `cronograma/tests/test_formacao.py` |

### Mudanças em relação ao plano
- Os testes já existentes da T007.1 cobrem escalação de formador ativo, recusa de
  formador inativo, proteção contra substituição e atualização do cronograma; não
  foram duplicados.

### Validação
- `python manage.py check` não acusou problemas e `python manage.py test` passou
  com 183 testes.
- `python manage.py makemigrations --check --dry-run` não encontrou mudanças; a
  US007 não precisa de migração.




---

## US011 — Consultar cobertura da apostila

**Responsável:** Murilo · **Sprint:** 2 · **RF:** RF011 · **Situação:** em andamento

### O que faz
Como coordenador ou formador, quero ver quais temas obrigatórios ainda não têm data
marcada no ciclo, para garantir que a apostila inteira seja coberta a tempo.

Critérios de aceitação: selecionado um ciclo, a tela mostra os temas da apostila
separados em três listas: não alocados, agendados e realizados.

### Como foi feita
- A cobertura é sempre calculada a partir das formações do ciclo e nunca armazenada
  (RN005, RN006): não há contador nem campo de situação do tema. Não há model novo
  nem migração.
- As formações do ciclo são as que têm data entre o início e o fim, inclusive (RN002),
  porque o ciclo é derivado da data. Só entram na conta os temas com `tipo=apostila`;
  os opcionais ficam fora.
- Classificação de cada tema (`services.classificar_cobertura`):
  - **realizado:** existe formação `realizada` com o tema no ciclo;
  - **agendado:** existe formação `prevista` e nenhuma realizada;
  - **não alocado:** nenhuma formação, ou só formações `canceladas` (a cancelada não
    cobre o tema, que volta a não alocado).
  - Se o mesmo tema tem várias formações, vale a mais avançada: realizada > prevista.
  - Formação sem tema (CA002) não cobre nada.
- Camadas do AGENTS.md: o repositório (`listar_temas_da_apostila`,
  `listar_formacoes_com_tema_do_ciclo`) é o único que usa o ORM; o serviço classifica
  sem receber `request`; a view só lê o ciclo escolhido e chama o serviço.
- A tela (`/cobertura/`) tem seletor de ciclo; sem escolha, usa o ciclo que contém o
  dia de hoje (`ciclo_do_cronograma`). Os não alocados vêm primeiro e em destaque.
- A tela é de consulta para os dois perfis: não usa `@coordenador_required`, só o login
  exigido pelo middleware. O link "Cobertura da apostila" fica na home para
  coordenador e formador.

### Tarefas
| Tarefa | Situação | Onde |
|---|---|---|
| T011.1 Criar consulta dos temas da apostila e das formações do ciclo (repositório) | Feita | `cronograma/repositories.py` |
| T011.2 Criar serviço que classifica cada tema em não alocado / agendado / realizado, sempre calculado (RN005) | Feita | `cronograma/services.py` |
| T011.3 Criar tela de cobertura com seleção de ciclo e destaque para os não alocados | Feita | `cronograma/views.py`, `cronograma/urls.py`, `cronograma/templates/cronograma/cobertura.html`, `acesso/templates/acesso/home.html` |
| T011.4 Testes: cancelada volta a não alocado, opcionais ficam fora, soma = total de temas (CA004) | Feita (<<n>> testes) | `cronograma/tests/test_cobertura.py` |

### Mudanças em relação ao plano
- Decisão nossa, não especificada: com várias formações do mesmo tema no ciclo, vale a
  mais avançada (realizada > prevista).
- A situação da formação só muda para `realizada` pelo admin por enquanto: nenhuma
  tela altera a situação. Sem isso, a lista "realizados" só se preenche por esse
  caminho.
- Ao incluir o link da cobertura, o link "Cronograma" da home foi removido por engano e
  quebrou `test_menu_completo_para_coordenador` (US001); foi restaurado.



  
---

## US012 — Consultar histórico de temas por formador

**RF:** RF012 · **Situação:** em desenvolvimento (branch `us012-historico-temas-formador`)

### O que faz
Como coordenador ou formador, quero consultar os temas que um formador já ministrou
e, no sentido inverso, os formadores que já ministraram determinado tema.

Critérios de aceitação: buscar um formador mostra os temas ministrados e suas datas;
buscar um tema mostra os formadores que o ministraram.

### Como foi feita
- O histórico é consultado a partir das formações com situação `realizada`, usando
  tema, formador e data já registrados; cada formação é uma ocorrência histórica.
- O filtro comum de formações realizadas é reutilizado pela consulta existente da
  T007.1 e pelas duas novas consultas. Formadores inativos continuam elegíveis.
- A tela oferece buscas GET independentes por formador e por tema, exibindo cada
  ocorrência em ordem cronológica decrescente. O middleware de login permite o
  acesso dos dois perfis; os links estão na home de cada um.
- Nenhum campo ou migration é necessário.

### Tarefas
| Tarefa | Situação | Onde |
|---|---|---|
| T012.1 Consultas de histórico por formador e tema | Feita | `cronograma/repositories.py`, `cronograma/services.py` |
| T012.2 Tela de histórico com as duas modalidades de busca | Feita | `cronograma/forms.py`, `cronograma/views.py`, `cronograma/urls.py`, `cronograma/templates/cronograma/historico.html`, `acesso/templates/acesso/home.html` |
| T012.3 Testes das consultas, tela e permissões | Feita (9 testes novos) | `cronograma/tests/test_historico.py` |

### Mudanças em relação ao plano
- Nenhuma até o momento.

### Validação
- `python manage.py check` não acusou problemas e `python manage.py test` passou
  com 192 testes.
- `python manage.py makemigrations --check --dry-run` não encontrou mudanças.

---

## US014 — Lançar presença em lote

**Responsável:** Cauã · **Sprint:** 2 · **RF:** RF014 · **Situação:** em desenvolvimento (branch `us014-presenca-em-lote`)

### O que faz
Como coordenador, quero marcar a presença de toda a turma de um encontro em uma única
tela e gravar tudo de uma vez, para não perder tempo lançando perseverante por perseverante.

Critérios de aceitação: escolhida uma formação, a tela lista todos os perseverantes do
ciclo com "presente" marcado por padrão; marcar as exceções e confirmar grava o
encontro inteiro de uma vez; reabrir a mesma formação mostra as marcações já salvas,
permitindo corrigir. A gravação é atômica: se uma linha falhar, nenhuma é salva (NFR001).

### Como foi feita
- Nova app `presenca`, o primeiro model do módulo Presença. `Presenca` herda de
  `RegistroBase` (RN008) e tem formação, perseverante e situação
  (presente/ausente/justificado, os mesmos valores do `banco/schema.sql` do seminário).
- Restrições no banco: `presenca_unica_por_formacao` (UNIQUE formação + perseverante)
  impede duas linhas da mesma pessoa no mesmo encontro, e o CHECK
  `presenca_situacao_valida` impede outro valor gravado por fora.
- FKs: `perseverante` usa `CASCADE`, como a US004 decidiu (a exclusão a pedido da
  NFC002 apaga as presenças). `formacao` usa `PROTECT`: não se apaga uma formação com
  presença lançada.
- A grade é calculada, não armazenada (RN006): os perseverantes **ativos** do ciclo da
  formação, sendo o ciclo derivado da data (RN002). Cada um vem com a situação já salva
  ou, se ainda não houver, com "presente".
- Gravação em lote (`repositories.salvar_presencas`): um `update_or_create` por
  perseverante dentro de um único `transaction.atomic()` (NFR001). Na primeira vez cria
  as linhas; na reabertura corrige as existentes, sem duplicar.
- O serviço (`lancar_presencas`) recusa perseverante que não está na grade (inativo ou
  de outro ciclo) e situação inválida antes de chegar ao banco. Os dados vêm de um POST
  e podem ser adulterados.
- A presença acessa formação e perseverantes pelos serviços de `cronograma` e
  `cadastros`, sem usar o ORM de outra app.
- A tela (`/presenca/<id>/`) é só do coordenador e tem um rádio por perseverante.
  Depois de gravar, volta para a mesma tela, que já mostra o que foi salvo. A formação é
  escolhida pelo link "Presença" em cada linha do cronograma; o link "Presença" da home
  passou a levar ao cronograma.

### Tarefas
| Tarefa | Situação | Onde |
|---|---|---|
| T014.1 Criar o model Presenca (formação, perseverante, situação) com UNIQUE(formação, perseverante) + migration | Feita | `presenca/models.py`, `presenca/migrations/0001_initial.py`, `presenca/admin.py`, `config/settings.py` |
| T014.2 Criar tela em grade com todos os perseverantes ativos e "presente" marcado por padrão | Feita | `presenca/services.py` (`grade_de_presenca`), `presenca/forms.py`, `presenca/views.py`, `presenca/urls.py`, `presenca/templates/presenca/lancar_presenca.html`, `config/urls.py`, `cronograma/templates/cronograma/cronograma.html`, `acesso/templates/acesso/home.html` |
| T014.3 Criar serviço de gravação em lote dentro de uma transação atômica (NFR001) | Feita | `presenca/services.py` (`lancar_presencas`), `presenca/repositories.py` (`salvar_presencas`) |
| T014.4 Reabrir formação já lançada trazendo as marcações salvas, permitindo correção | Feita | `presenca/repositories.py` (`situacoes_da_formacao`, `update_or_create`) |
| T014.5 Testes: uma linha por perseverante; falha simulada não grava nenhuma linha | Feita (20 testes) | `presenca/tests/test_presenca.py` |

### Mudanças em relação ao plano
- A falha da T014.5 é simulada com uma situação inválida no meio do lote: o CHECK do
  banco recusa essa linha, e o teste confere que as linhas anteriores também foram
  desfeitas. Sem o `atomic()`, os dois testes de falha quebram (verificado).
- Decisão nossa, não especificada: só perseverantes **ativos** entram na grade. Quem
  for inativado depois de ter presença lançada continua com a presença salva no banco,
  mas some da grade.
- Decisão nossa, não especificada: a tela não bloqueia formação `cancelada` nem
  `prevista`. O cartão não pede esse bloqueio.

### Validação
- Em 17/11/2026, `python manage.py check` não acusou problemas e `python manage.py test`
  passou com 212 testes (20 novos).
- Migração nova: `presenca/migrations/0001_initial.py`. Quem baixar a branch precisa
  rodar `python manage.py migrate`.


## US016 — Exportar o cronograma do mês

**Responsável:** Murilo · **Sprint:** 2 · **RF:** RF016 · **Situação:** em andamento

### O que faz
Como coordenador, quero ver o cronograma do mês já formatado como texto, com botão de
copiar, para colar direto no grupo de mensagens do ministério.

Critérios de aceitação: escolhido um mês, a tela mostra o cronograma como texto corrido
pronto para copiar, com uma linha por formação (data, tema, formador); formações
canceladas não aparecem no texto exportado.

### Como foi feita
- Não há model novo nem migração: o texto é sempre gerado a partir das formações
  (RN006), nada é armazenado.
- Padrão **Template Method** (`cronograma/exportacao.py`): `ExportadorBase.exportar`
  define o esqueleto fixo (cabeçalho, uma linha por formação, rodapé) e as subclasses
  definem cada passo. `ExportadorTexto` produz o texto simples para o grupo de
  mensagens. Um novo formato de exportação (por exemplo, HTML) só precisa de outra
  subclasse, sem mexer no esqueleto.
- O repositório (`listar_formacoes_do_mes`) é o único que usa o ORM: filtra por ano e
  mês, exclui as canceladas e ordena por data. O serviço (`exportar_cronograma_do_mes`)
  monta o título e chama o exportador, sem receber `request`.
- O mês vem de um `<input type="month">`, no formato `AAAA-MM`. Sem escolha, ou com
  valor inválido, o serviço usa o mês de hoje (`mes_da_exportacao`).
- Formato da linha: `dd/mm - tema - formador`. Formação sem tema aparece como
  "Sem tema" e sem formador, como "a definir". Mês sem formações mostra
  "Nenhuma formação neste mês.".
- A tela (`/exportar/`) mostra o texto em uma área somente leitura, com botão
  "Copiar" que usa `navigator.clipboard`.
- A tela é só do coordenador (`@coordenador_required`): formador recebe 403 e anônimo
  vai ao login. O link "Exportação" da home do coordenador passou a apontar para ela.

### Tarefas
| Tarefa | Situação | Onde |
|---|---|---|
| T016.1 Criar o formatador de texto do cronograma (padrão Template Method) | Feita | `cronograma/exportacao.py` |
| T016.2 Criar serviço que busca as formações do mês, sem as canceladas | Feita | `cronograma/repositories.py`, `cronograma/services.py` |
| T016.3 Criar tela com seletor de mês e botão de copiar | Feita | `cronograma/views.py`, `cronograma/urls.py`, `cronograma/templates/cronograma/exportar.html`, `acesso/templates/acesso/home.html` |
| T016.4 Testes do texto gerado (uma linha por formação, canceladas fora) | Feita (<<n>> testes) | `cronograma/tests/test_exportacao.py` |

### Mudanças em relação ao plano
- Decisões nossas, não especificadas: o formato `dd/mm - tema - formador`, os textos
  "Sem tema" e "a definir", e o mês de hoje como padrão.
- A mudança da situação de uma formação para `cancelada` só é possível pelo admin por
  enquanto; nenhuma tela altera a situação.
- O botão "Copiar" só funciona em `localhost` ou HTTPS, por exigência do
  `navigator.clipboard`.


  
---

## US013 — Consultar carga de formações por formador

**Responsável:** Murilo · **Sprint:** 3 · **RF:** RF013 · **Situação:** finalizada

### O que faz
Como coordenador, quero ver quantas formações cada formador já ministrou no ciclo,
para distribuir a escala de forma mais equilibrada.

Critérios de aceitação: selecionado um ciclo, a tela mostra quantas formações cada
formador já ministrou nele.

### Como foi feita
- Não há model novo nem migração: a carga é sempre calculada a partir das formações
  registradas e nunca armazenada (RN006).
- A consulta agregada (`repositories.contar_formacoes_por_formador`) usa `COUNT` no
  banco: filtra as formações do ciclo (data entre início e fim, RN002), só as
  `realizadas` e com formador, agrupa por formador e devolve um dicionário
  `{formador_id: total}`. É o único ponto que usa o ORM.
- O serviço (`services.carga_por_formador`) combina essa contagem com os formadores
  ativos (`listar_formadores_ativos`, de `cadastros`) e devolve a lista
  `(formador, total)` do maior para o menor, com desempate por nome. Formador ativo
  sem formação aparece com 0, o que ajuda a equilibrar a escala. O serviço não
  recebe `request`.
- A tela (`/carga/`) tem seletor de ciclo; sem escolha, usa o ciclo que contém o dia
  de hoje (`ciclo_do_cronograma`).
- A tela é só do coordenador (`@coordenador_required`): formador recebe 403 e anônimo
  vai ao login. O link "Carga por formador" fica no menu do coordenador na home.

### Tarefas
| Tarefa | Situação | Onde |
|---|---|---|
| T013.1 Criar consulta agregada (COUNT) de formações por formador no ciclo, nunca armazenada (RN006) | Feita | `cronograma/repositories.py`, `cronograma/services.py` |
| T013.2 Criar tela de carga por formador com seleção de ciclo | Feita | `cronograma/views.py`, `cronograma/urls.py`, `cronograma/templates/cronograma/carga.html`, `acesso/templates/acesso/home.html` |
| T013.3 Testes da contagem | Feita (<<n>> testes) | `cronograma/tests/test_carga.py` |

### Mudanças em relação ao plano
-
---

## US017 — Registrar encontro sem tema da apostila

**Responsável:** Cauã · **Sprint:** 3 · **RF:** RF017 · **Situação:** em andamento (branch `us017-encontro-sem-tema`)

### O que faz
Como coordenador, quero registrar encontros que não têm tema obrigatório (oração,
dinâmica), para que esses encontros também apareçam no cronograma e recebam
lançamento de presença.

Critérios de aceitação:
- Cadastrar uma formação sem tema da apostila (ou com tema opcional) faz ela aparecer
  no cronograma e permite lançar presença nela.
- Esse encontro não aparece na consulta de cobertura da apostila.

### Como foi feita
- **A maior parte já estava pronta nas histórias anteriores.** `Formacao.tema` aceita
  ficar vazio e o formulário oferece "Sem tema" e "Temas opcionais" (US006). A cobertura
  só considera temas `tipo=apostila` (US011). A presença não depende do tema (US014).
  A US017 confirma isso com testes, sem model novo e sem migração.
- **Lacuna encontrada:** um encontro sem tema aparecia como "Sem tema" no cronograma, na
  presença, na escalação e no texto exportado, mesmo com a descrição preenchida. Com
  isso, não dava para diferenciar uma oração de uma dinâmica.
- Para resolver, `Formacao` ganhou a propriedade `titulo`: o nome do tema, senão a
  descrição, senão "Sem tema". É calculada e não armazenada (RN006). Fica no modelo
  para que as telas e a exportação usem a mesma regra, em vez de repetir o
  `default:"Sem tema"` em cada template. O `__str__` também passou a usá-la.
- O campo "Descrição" do formulário de formação ganhou um texto de ajuda sugerindo
  usá-lo para encontros sem tema (ex.: Oração, Dinâmica).

### Tarefas
| Tarefa | Situação | Onde |
|---|---|---|
| T017.1 Permitir tema em branco ou opcional no formulário de formação | Feita (já existia desde a US006; agora o encontro é identificado pela descrição) | `cronograma/models.py` (`titulo`), `cronograma/forms.py`, `cronograma/templates/cronograma/cronograma.html`, `cronograma/templates/cronograma/escalar_formador.html`, `cronograma/exportacao.py` |
| T017.2 Garantir que esses encontros aceitem presença e fiquem fora da cobertura | Feita (sem mudança de regra; coberto por testes) | `presenca/templates/presenca/lancar_presenca.html` |
| T017.3 Testes: encontro sem tema aparece no cronograma e não entra na cobertura | Feita (13 testes) | `cronograma/tests/test_encontro_sem_tema.py` (11), `presenca/tests/test_presenca.py` (2) |

### Mudanças em relação ao plano
- Não havia regra nova a implementar: os critérios já eram atendidos pela US006, US011
  e US014. O trabalho foi provar isso com testes e mostrar a descrição no lugar do tema.
- A exportação do cronograma (US016) passou a mostrar a descrição dos encontros sem
  tema (`10/03 - Oração - a definir`). Sem descrição, continua "Sem tema".

### Validação
- Em 21/11/2026, `manage.py check` não acusou problemas, `makemigrations --check` não
  encontrou mudanças pendentes e a suíte completa (234 testes) passou.
- Sem migração nova.
