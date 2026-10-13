-- Dados ficticios para a demonstracao
INSERT INTO ciclo (nome, inicio, fim) VALUES
  ('Perseveranca 2025', '2025-02-01', '2025-12-15'),
  ('Perseveranca 2026', '2026-02-01', '2026-12-15');

INSERT INTO formador (nome, capacitado) VALUES
  ('Ana', true), ('Bruno', false), ('Carla', true), ('Diego', false);

INSERT INTO tema (titulo, tipo, rotulo) VALUES
  ('Querigma',            'apostila', 'A01'),
  ('Batismo no Espirito', 'apostila', 'A02'),
  ('Vida de oracao',      'apostila', 'A03'),
  ('Palavra de Deus',     'apostila', 'A04'),
  ('Sacramentos',         'apostila', 'A05'),
  ('Servico no grupo',    'apostila', 'A06'),
  ('Louvor e musica',     'opcional', NULL);

INSERT INTO perseverante (nome, ciclo_id)
SELECT 'Perseverante ' || g, 2 FROM generate_series(1, 10) g;

-- formacoes: 2025 (ciclo anterior) e 2026
INSERT INTO formacao (data, formador_id, tema_id, situacao) VALUES
  ('2026-03-07', 1, 1, 'realizada'),   -- id 1
  ('2026-03-14', 2, 2, 'realizada'),   -- id 2
  ('2026-03-21', 3, 3, 'cancelada'),   -- id 3
  ('2026-11-07', 1, 4, 'prevista'),    -- id 4
  ('2026-04-04', 4, 7, 'realizada'),   -- id 5 (tema opcional)
  ('2025-05-10', 3, 1, 'realizada'),   -- id 6 (ciclo 2025)
  ('2025-06-14', 1, 3, 'realizada');   -- id 7 (ciclo 2025)

-- presenca ja lancada da formacao 1: perseverantes 1 a 7
INSERT INTO presenca (formacao_id, perseverante_id, situacao)
SELECT 1, g, CASE WHEN g = 5 THEN 'ausente' ELSE 'presente' END
FROM generate_series(1, 7) g;

-- troca registrada na formacao 4 (Diego -> Ana)
INSERT INTO troca_formador (formacao_id, formador_saiu_id, formador_entrou_id, data_troca)
VALUES (4, 4, 1, '2026-10-01');
