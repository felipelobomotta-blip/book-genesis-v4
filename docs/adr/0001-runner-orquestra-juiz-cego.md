# ADR 0001 — O runner orquestra; o juiz é cego e comparativo

**Status:** aceito em 02/09/2026 pelo autor (Felipe), a partir da revisão em
`docs/REVISAO-CONSISTENCIA-2026-09.md`. Implementado no branch `arch/runner-orchestrates` no mesmo
dia (54 testes; smoke real de ponta a ponta em `docs/runner.md`, seção "Measured run").
**Veto pendente:** a movimentação dos pipelines antigos para `legacy/` (seção 5) acontece no
branch e só vira definitiva se o Felipe aprovar o merge.

## 1. Contexto

O repositório tinha três pipelines, quatro portões e três rubricas coexistindo, e o portão de
qualidade era o próprio sistema dando nota à própria prosa. No único projeto real recente
(agenda-2030), o loop de agentes não foi usado: os capítulos saíram de um brief humano mais uma
chamada de modelo, e nenhum capítulo foi avaliado. O objetivo declarado do produto é que uma
pessoa criativa sem ofício de escrita gere um livro publicável a partir de uma ideia.

## 2. Decisões

1. **O orquestrador é código.** O runner Python (`runner/`) executa o loop: lê estado, monta o
   pacote a partir de arquivos, chama o modelo por um adaptador, valida a saída, grava, avança.
   Nenhum modelo recebe ferramentas; toda leitura e escrita de arquivo é do runner. O agente
   `book-orchestrator` deixa de existir como agente.
2. **Agentes são templates de prompt.** Os arquivos `agents/*.md` continuam sendo a fonte única
   dos prompts. O runner ignora o frontmatter, injeta as constantes e acrescenta um contrato de
   saída ("você não tem ferramentas; devolva só X").
3. **O juiz é cego.** O template `book-judge` recebe apenas a prosa do capítulo, as últimas ~300
   palavras do capítulo anterior, o gênero e o leitor-alvo. Nunca recebe outline, fundação,
   personas ou notas do escritor. Um leitor não tem o gabarito.
4. **O juiz compara, não pontua.** Perguntas de leitor (viraria a página; onde parou; o que lembra
   amanhã) mais comparação pareada: rascunho novo contra rascunho anterior e, se existir um trecho
   âncora publicado do mesmo gênero em `anchors/`, contra a âncora. Nota absoluta 0–10 deixa de
   existir como portão.
5. **Rubrica vira diagnóstico.** O `book-evaluator` (sete dimensões, scan anti-IA) pode rodar como
   diagnóstico opcional para orientar o editor. Não aprova nem reprova.
6. **Três passes por capítulo, não sete.** Escritor → disruptor (opcional; padrão ligado para
   ficção) → juiz → editor só se o juiz mandar → juiz compara. Máximo de ciclos vem das
   constantes. `dialogue-polish` e `hook-craft` deixam de ser agentes e viram modos do editor,
   acionados pelas flags do juiz.
7. **O brief é artefato de primeira classe.** `briefs/chapter-NN.md` é montado de forma
   determinística pelo runner: seção do capítulo no outline, motor da história, personagens,
   cauda do capítulo anterior e constantes do gênero. O escritor recebe o brief, não a fundação
   inteira.
8. **Uma fonte para as constantes.** `runner/config/genre-profiles.yaml` (faixas de palavras por
   capítulo, faixa de diálogo, orçamento de padrões de IA, ciclos máximos) e
   `runner/config/models.yaml` (adaptador e modelo por papel). Prompts referenciam, nunca
   reescrevem números.
9. **Modelo por tarefa.** Papéis: `writer`, `disruptor`, `judge`, `editor`, `architect`,
   `extractor`. O juiz usa por padrão uma família diferente do escritor quando houver dois CLIs
   disponíveis. Tarefas mecânicas usam a classe mais barata.
10. **O escritor não conhece a rubrica.** Sai do template do escritor a instrução de construir os
    critérios do avaliador no primeiro rascunho. Quem escreve escreve; quem julga julga.
11. **Um humano lê o capítulo 1.** Depois do primeiro capítulo aceito, o runner para em
    `awaiting_human` até existir `approvals/chapter-01.approved` (criado por `runner approve`).
    O portão final do livro é leitura humana, não nota.

## 3. Adaptadores

- `claude`: CLI `claude -p` com prompt por stdin, `--output-format text`, `--model <alias>`.
- `codex`: CLI `codex exec` com prompt por stdin e `--output-last-message <arquivo>`.
- `fake`: respostas roteirizadas, só para testes.
- `manual`: grava o prompt em `work/manual/` e para; caminho fail-closed quando não há CLI.

Nenhum adaptador toca chave de API. Os CLIs usam a sessão já autenticada da máquina.

## 4. Layout do projeto de livro

```
<projeto>/
  PROJECT_STATE.yaml
  ASSUMPTIONS.md
  artifacts/00..07            (fases 0–2, como hoje)
  briefs/chapter-NN.md        (montado pelo runner)
  manuscript/chapters/        (só capítulos aceitos)
  manuscript/drafts/chapter-NN/draft-K.md
  evaluations/chapter-NN-judge-K.md
  approvals/chapter-01.approved
  anchors/<genero>.md         (opcional, local, nunca versionado)
  work/                       (pacotes, logs, prompts manuais)
```

## 5. O que sai do caminho canônico (movido, não apagado)

Para `legacy/`, com histórico git preservado: `skills/book-genesis-full`, `skills/book-genesis`
(cópia divergente do codex), `skills/deprecated`, `skills/optional`, `agents/book-orchestrator.md`,
`agents/dialogue-polish.md`, `agents/hook-craft.md`, `docs/architecture.md`. README, AGENTS.md e
instaladores passam a descrever um único caminho. **Esta é a parte que depende de aprovação.**

## 6. Costuras sob teste (seams)

Testes só nas interfaces públicas abaixo; nada de teste em função interna.

| costura | comportamento verificado |
|---|---|
| `runner.judge.parse_verdict(text)` | lê as respostas de leitor de um bloco YAML literal |
| `runner.judge.judge_chapter(prose, previous_tail, genre, adapter, model)` | o prompt enviado contém a prosa e a cauda; devolve `Verdict` |
| `runner.chapter.run_chapter(project, n, adapters)` | o escritor recebe o brief; o juiz **não** recebe o outline (sentinela); rascunhos e vereditos gravados; editor só roda com flag; loop respeita o máximo |
| `runner.brief.build_chapter_brief(project, n)` | extrai a seção do capítulo e a cauda do anterior; injeta constantes |
| `runner.constants.load_genre_profile(genre)` / `load_model_map()` | valores vêm dos YAML; gênero desconhecido cai no perfil `default` |
| `runner.phases.run_phase(project, adapters)` | divide a saída multi-arquivo e grava só os artefatos exigidos pela fase |
| `runner.adapters.parse_codex_last_message` / comando do `claude` | construção de comando e leitura de resposta sem chamar rede |
| CLI `judge`, `chapter`, `approve`, `run-phase` | rodam por caminho com `--adapter fake` |
| checkpoint | `run_chapter(2)` recusa rodar sem `approvals/chapter-01.approved` |

## 7. Fora do escopo desta ADR

Geração de EPUB/PDF; o teste cego com leitores humanos (protocolo em `felipe-cortex/estudos/`);
o painel de leitores simulados (`book-swarm-panel`); o registro de 14 agentes do
`book-bestseller-studio` (fica como está); qualquer push.

## 8. Reversão

Tudo vive no branch `arch/runner-orchestrates`. Não mesclar é a reversão.
