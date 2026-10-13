-- FORMATECH — esquema relacional (PostgreSQL 16)
-- Toda tabela tem criado_em e atualizado_em (RN008).

CREATE TABLE ciclo (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nome          text NOT NULL,
  inicio        date NOT NULL,
  fim           date NOT NULL,
  criado_em     timestamptz NOT NULL DEFAULT now(),
  atualizado_em timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ciclo_fim_depois_inicio CHECK (fim > inicio),
  -- RN002: ciclos nao podem se sobrepor
  CONSTRAINT ciclo_sem_sobreposicao
    EXCLUDE USING gist (daterange(inicio, fim, '[]') WITH &&)
);

CREATE TABLE perseverante (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nome          text NOT NULL,
  ciclo_id      bigint NOT NULL REFERENCES ciclo (id),
  criado_em     timestamptz NOT NULL DEFAULT now(),
  atualizado_em timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE formador (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nome          text NOT NULL,
  inicio_servico date,
  capacitado    boolean NOT NULL DEFAULT false,
  criado_em     timestamptz NOT NULL DEFAULT now(),
  atualizado_em timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE tema (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  titulo        text NOT NULL,
  tipo          text NOT NULL CHECK (tipo IN ('apostila', 'opcional')),
  rotulo        text,
  criado_em     timestamptz NOT NULL DEFAULT now(),
  atualizado_em timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE formacao (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  data          date NOT NULL,
  formador_id   bigint NOT NULL REFERENCES formador (id),
  tema_id       bigint REFERENCES tema (id),      -- opcional (RF017)
  situacao      text NOT NULL DEFAULT 'prevista'
                CHECK (situacao IN ('prevista', 'realizada', 'cancelada')),
  criado_em     timestamptz NOT NULL DEFAULT now(),
  atualizado_em timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE presenca (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  formacao_id     bigint NOT NULL REFERENCES formacao (id),
  perseverante_id bigint NOT NULL REFERENCES perseverante (id),
  situacao        text NOT NULL
                  CHECK (situacao IN ('presente', 'ausente', 'justificado')),
  criado_em       timestamptz NOT NULL DEFAULT now(),
  atualizado_em   timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT presenca_formacao_id_perseverante_id_key
    UNIQUE (formacao_id, perseverante_id)
);

CREATE TABLE troca_formador (
  id                bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  formacao_id       bigint NOT NULL REFERENCES formacao (id),
  formador_saiu_id  bigint NOT NULL REFERENCES formador (id),
  formador_entrou_id bigint NOT NULL REFERENCES formador (id),
  data_troca        date NOT NULL,
  criado_em         timestamptz NOT NULL DEFAULT now(),
  atualizado_em     timestamptz NOT NULL DEFAULT now(),
  CHECK (formador_saiu_id <> formador_entrou_id)
);

CREATE TABLE usuario (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  login         text NOT NULL UNIQUE,
  senha_hash    text NOT NULL,
  perfil        text NOT NULL CHECK (perfil IN ('coordenador', 'formador')),
  formador_id   bigint REFERENCES formador (id),
  criado_em     timestamptz NOT NULL DEFAULT now(),
  atualizado_em timestamptz NOT NULL DEFAULT now()
);
