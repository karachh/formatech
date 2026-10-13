\echo '=== D1: quem ja deu o tema Querigma (id 1)? ==='
SELECT f.data, fo.nome AS formador, f.situacao
FROM formacao f
JOIN formador fo ON fo.id = f.formador_id
JOIN tema t      ON t.id  = f.tema_id
WHERE t.id = 1
  AND f.situacao <> 'cancelada'
ORDER BY f.data;

\echo '=== D2: temas da apostila sem formacao ativa no ciclo 2026 ==='
SELECT t.rotulo, t.titulo
FROM tema t
WHERE t.tipo = 'apostila'
  AND NOT EXISTS (
    SELECT 1 FROM formacao f
    WHERE f.tema_id = t.id
      AND f.situacao <> 'cancelada'
      AND f.data BETWEEN '2026-02-01' AND '2026-12-15')
ORDER BY t.rotulo;

\echo '=== D3: presenca duplicada (perseverante 7 na formacao 1) ==='
INSERT INTO presenca VALUES (DEFAULT, 1, 7, 'presente');

\echo '=== D4: lote que falha no meio ==='
SELECT count(*) AS antes FROM presenca WHERE formacao_id = 1;
BEGIN;
INSERT INTO presenca VALUES (DEFAULT, 1, 8, 'presente');
INSERT INTO presenca VALUES (DEFAULT, 1, 9, 'presente');
INSERT INTO presenca VALUES (DEFAULT, 1, 7, 'ausente');
ROLLBACK;
SELECT count(*) AS depois FROM presenca WHERE formacao_id = 1;

\echo '=== D5: chave estrangeira recusa formador inexistente ==='
INSERT INTO formacao (data, formador_id, tema_id) VALUES ('2026-11-14', 99, 5);

\echo '=== D6: ciclo sobreposto recusado ==='
INSERT INTO ciclo (nome, inicio, fim) VALUES ('Ciclo invalido', '2026-11-01', '2027-03-01');

\echo '=== D7: carga por formador no ciclo 2026 (calculada, RN006) ==='
SELECT fo.nome, count(f.id) AS formacoes
FROM formador fo
LEFT JOIN formacao f ON f.formador_id = fo.id
  AND f.situacao <> 'cancelada'
  AND f.data BETWEEN '2026-02-01' AND '2026-12-15'
GROUP BY fo.nome
ORDER BY formacoes DESC, fo.nome;

\echo '=== D8: frequencia do Perseverante 5 no ciclo 2026 ==='
SELECT p.situacao, count(*) AS encontros
FROM presenca p
JOIN perseverante pe ON pe.id = p.perseverante_id
WHERE pe.nome = 'Perseverante 5'
GROUP BY p.situacao;
