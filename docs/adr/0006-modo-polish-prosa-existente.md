# ADR 0006 — Modo polish: o loop a partir de prosa existente

Data: 2026-09-03

## Contexto

O runner só entra pela porta do writer: `run_chapter` sempre chama o escritor
(a partir do brief) e depois o disruptor, e só então juiz e editor. `run_book`
pula capítulos que já existem (`already written, skipped`). Resultado: um
manuscrito completo que veio de fora do pipeline (rascunho anterior, reescrita,
livro importado) não tem caminho de entrada — ou ele é reescrito do zero, ou o
sistema não o toca. O caso de uso real existe e é frequente: polir um livro
pronto com o mesmo controle de qualidade da geração.

## Decisão

1. `run_chapter` ganha `seed_draft: Optional[str] = None`. Quando presente,
   o loop pula brief, writer e disruptor e trata o texto existente como
   draft 1; o resto (juiz cego → editor → juiz comparativo, orçamento de
   revisão do perfil de gênero) é idêntico ao fluxo de geração.
2. `run_polish` (em `runner/book.py`) percorre os capítulos que já existem em
   `manuscript/chapters/chapter-NN.md` dentro do intervalo pedido, lê o texto
   e chama `run_chapter(seed_draft=...)`. Capítulo sem arquivo é pulado com
   aviso, não é erro.
3. Novo comando `book-genesis polish <projeto> [--from N] [--to M]`, com a
   mesma fiação de adaptadores do comando `book` (sem painel e sem
   human-checkpoint: o humano já leu o livro que está sendo polido).
4. O original nunca é perdido: ele é salvo como
   `manuscript/drafts/chapter-NN/draft-1.md`, e o capítulo final só é
   sobrescrito quando o juiz aprova (`turn_page: yes` e não-pior). Se o
   orçamento de revisão se esgota sem aprovação, o capítulo fica intacto e o
   run report marca `blocked`.
5. No modo polish, flags do juiz disparam o editor mesmo com `turn_page: yes`
   (`revise_on_flags=True`): no fluxo de geração, flags são aviso para o
   editor da próxima rodada; num livro pronto, elas são o único sinal de que
   há trabalho a fazer. O guard `vs_previous` continua valendo — revisão pior
   não substitui o original.

## Consequências

- Um manuscrito externo entra no mesmo controle de qualidade da geração, sem
  que o writer ou o editor conheçam a rubrica (ADR 0001 se mantém).
- O writer e o disruptor não são chamados no modo polish; um projeto pode ser
  polido com apenas as roles judge e editor disponíveis.
- Continuidade global continua fora do escopo do juiz por capítulo (ele vê
  apenas a prosa e a cauda do capítulo anterior); buracos que atravessam o
  livro inteiro seguem exigindo leitura humana ou passes dedicados.
