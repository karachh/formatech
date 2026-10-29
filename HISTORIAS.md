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



---

## US005 — Cadastrar temas da apostila

**Responsável:** Murilo · **Sprint:** 1 · **RF:** RF005 · **Situação:** em andamento

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
| T005.1 Criar o model Tema (nome, tipo apostila/opcional, rótulo da apostila) + migration | Feita | `cadastros/models.py`, `cadastros/admin.py`, `cadastros/migrations/<<nome da migração>>` |
| T005.2 Criar repositório e serviço de temas | Feita | `cadastros/repositories.py`, `cadastros/services.py` |
| T005.3 Criar telas de lista, cadastro e edição de tema | Feita | `cadastros/forms.py`, `cadastros/views.py`, `cadastros/urls.py`, `cadastros/templates/cadastros/temas.html`, `cadastros/templates/cadastros/editar_tema.html` |
| T005.4 Carregar os temas reais da apostila (carga inicial) | Feita (26 temas) | `cadastros/management/commands/carregar_temas.py`, `cadastros/dados/temas.csv` |
| T005.5 Testes do cadastro e da classificação | Feita (<<n>> testes) | `cadastros/tests/test_temas.py` |

### Mudanças em relação ao plano
- O campo se chama `nome`, como no Trello e em `Ciclo.nome`, e não `titulo`, como no
  `banco/schema.sql` (exemplo do seminário, não o esquema oficial).
- Unicidade do nome e rótulo opcional foram decisões nossas: a tarefa não as
  especifica. O rótulo guarda só o número da apostila.
- O vínculo do tema com a montagem do cronograma ("fica disponível para escolher")
  depende do módulo Cronograma, que ainda não existe. Esta história entrega a lista
  de temas que ele vai consumir.
- A edição de tema (T005.3) não altera o `HISTORIAS.md` da US001: os links de menu
  continuam provisórios, exceto "Temas".