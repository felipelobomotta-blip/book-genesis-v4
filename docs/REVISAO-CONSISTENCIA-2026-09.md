# Revisão de consistência — Book Genesis v4

**Base:** HEAD `14b5dc4` (= `origin/master`, github.com/felipelobomotta-blip/book-genesis-v4)
**Data:** 02/09/2026
**Objetivo declarado pelo autor:** "qualquer pessoa criativa com uma ideia boa gera um livro de nível best-seller."
**Pergunta desta revisão:** o repositório, como está, entrega esse objetivo? Onde ele se contradiz?

---

## 0. Método — o que foi lido e como

Este repositório é ~900 KB de prompt-código em markdown mais um runner Python. "Linha por linha" aqui
significa ler os prompts como código. Tudo abaixo cita `arquivo:linha` conferível no HEAD acima.

**Lidos integralmente por mim (não por resumo):**

- `README.md`, `AGENTS.md`, `install.sh`, `install.ps1`, `SHOWCASE.md`, `docs/book-gallery.md`
- os 12 arquivos de `agents/` (3.256 linhas no total)
- `docs/genesis-score.md`
- `skills/book-genesis-codex/SKILL.md` + `references/pipeline/manifest.yaml` + `references/prompts/adversarial-audit.md` + `references/scoring/genesis-score-codex.md`
- `skills/book-genesis/SKILL.md` + `references/pipeline/manifest.yaml`
- `skills/book-bestseller-studio/references/agent-registry.yaml`
- `runner/cli.py`, `runner/filesystem.py`, `tests/test_runner.py`
- `knowledge/bestseller-dna.md`
- `examples/protocolo-nao-encontrado/genesis-score.md`, `examples/cases/agenda-2030.md`, `examples/age-of-aquarius/synopses.md`

**Só por grep (estrutura, contagens, referências):** `skills/book-genesis-full/SKILL.md` (998 linhas),
`docs/architecture.md`, `docs/system-analysis.md`, `docs/book-genesis-codex.md`, os outros quatro
`knowledge/*.md`, as demais 20 skills.

**Não lidos:** `docs/superpowers/*`, `docs/faq.md`, `docs/portability.md`, `docs/runner.md`,
`examples/cases/*` exceto agenda-2030, `web/landing.html`, `video-demo/`.

**Executado:** `tests/test_runner.py` — 12 testes, **12 passam** em dois interpretadores (venv 3.11 e Python do sistema).

**Fora do repositório, usado como evidência:** a saída real de `book-genesis/books/agenda-2030/`
(clone do Desktop, não commitada), a pasta `studio/` (não commitada), a API do GitHub (issues, PRs, forks).

Uma varredura por cinco revisores automáticos foi tentada e caiu por limite de cota da API antes de
produzir resultado; nada abaixo vem deles.

---

## 1. O achado central: três pipelines, quatro portões, três rubricas

O repositório contém **três pipelines distintos**, cada um documentado como "o atual" em um lugar diferente:

| pipeline | onde é chamado de canônico | estado | fases | rubrica | portão de aprovação |
|---|---|---|---|---|---|
| **A. Agentes V4** (`agents/`, `book-orchestrator`) | `README.md` inteiro | `STATE.yaml` + `ENTITY_STATE.yaml` | 1, 1.5, 2, 2.5, 2.7, 2.8, 3 (A–G), 4, 5, 5.5, 5.6, 6 | 7 dimensões, piso, escala 6–10, anti-AI 20 padrões, 4(+1) leitores, CVI | Floor ≥ 8.5 **e** Casual ≥ 8.5 por capítulo; CVI-Launch ≥ 9.0 no manuscrito |
| **B. Universal Core** (`skills/book-genesis-codex/`) | `AGENTS.md:7-13` ("Treat legacy V4 material as historical reference") | `PROJECT_STATE.yaml` + `ASSUMPTIONS.md` | 0–6 com **Phase 4 Adversarial Audit obrigatória** | **10 dimensões, média ponderada**, sem anti-AI scan, sem leitores simulados, sem CVI (`genesis-score-codex.md:20-31,99-113`) | Floor ≥ 8.5 **e** média ponderada ≥ 9.0 **e** nenhuma < 8.0 **e** auditoria ≠ MAJOR REWRITE (`:115-123`) |
| **C. V4 skills 17 fases** (`skills/book-genesis-full/`) | `install.ps1:96` manda digitar `/book-genesis`; `docs/architecture.md` descreve este | `STATE.yaml` | 17 fases (`SKILL.md:28,66-86`) | 7 dimensões | **Floor ≥ piso do gênero (7.0–7.5)** e CVI-Launch ≥ **7.0** (`SKILL.md:350,371-372`); loop máx **3** (`:82`) |

E o `docs/genesis-score.md` — autointitulado "Complete Specification" — define uma **quarta** variante
de portão: CVI-Launch ≥ 7.0 para submissão (`:249`) com inputs diferentes dos do avaliador
(`:227-236` vs `agents/book-evaluator.md:326-335`).

**Consequências diretas:**

- O README promete "7-dimension Genesis Score, 20-pattern anti-AI scan, 4 reader types" (`README.md:181-185`).
  O pipeline que `AGENTS.md` chama de canônico **não tem nenhum dos três**.
- O instalador termina com "type `/book-genesis` or `/book-genesis-codex`" (`install.ps1:96`, `install.sh:103`).
  O README diz para digitar "I have an idea for a book" e deixar o `book-orchestrator` assumir (`README.md:57-61`).
  São três portas de entrada para três sistemas diferentes.
- O runner (`runner/filesystem.py:11-12`) lê **só** o manifesto do codex (7 fases). O `/book-genesis` que o
  instalador anuncia tem manifesto próprio com **8** fases (`skills/book-genesis/references/pipeline/manifest.yaml:47-54`,
  "Literary Barrier Revision Loop"). O runner não conhece esse pipeline.
- O `agent-registry.yaml` do bestseller-studio define uma **quarta taxonomia** de 14 agentes cujos contratos
  apontam para `foundation/`, `research/comps.md`, `revision/`, `launch/` — diretórios que nem o
  orquestrador A nem o `scaffold_project()` do runner criam (`runner/filesystem.py:114-119`).
  `prepare-agent-packet` lista todos os inputs como `missing` num projeto recém-criado.
- O produto tem **cinco nomes**: Best Seller Studio (`README.md:3`), Book Genesis (`install.ps1:17`),
  book-genesis-v4 (repositório), Book Genesis Universal Core (`book-genesis-codex/SKILL.md:6`),
  Book Genesis Studio (`studio/`, não commitado).

**Severidade: bloqueia o objetivo.** "Qualquer pessoa" não consegue saber qual sistema está rodando,
e cada um passa um livro por um portão diferente.

---

## 2. O portão de 8.5 é auto-confirmação por construção

O README vende o portão como o diferencial ("This is what makes Best Seller Studio different from just
asking ChatGPT", `README.md:156`). O próprio código diz o contrário, em três lugares:

1. **O avaliador declara que o portão está na zona não confiável.** `agents/book-evaluator.md:433`:
   *"BIAS CHECK: ... Confidence in scores above 8.0 requires external validation."* O portão é 8.5.
   Pela regra do próprio avaliador, **todo PASS é uma nota sem validação**. E `:416`: *"You are evaluating
   prose that THIS SYSTEM wrote. Your bias is maximum."*
2. **O orquestrador se contradiz sobre o que é sucesso.** `agents/book-orchestrator.md:352`:
   *"EXCELLENCE TARGET: Genesis Floor ≥ 8.5 AND Casual ≥ 8.5. This is the only PASS. 'Good enough' does not exist."*
   E `:526`: *"A finished book with floor 7.5 is infinitely better than an unfinished book targeting 9.0."*
   Um LLM instruído a exigir 8.5 **e** a "keep moving forward" tem um caminho de menor resistência: o
   avaliador (outro LLM do mesmo sistema) distribui 8.5.
3. **O escritor é treinado para a prova.** `agents/book-writer.md:39`: *"The evaluator's unlock criteria are
   public — build them into the FIRST draft."* O escritor otimiza para a rubrica do avaliador, não para o
   leitor. O pipeline B diz o oposto (`skills/book-genesis/SKILL.md:104`: *"Do not optimize prose to
   satisfy rubrics while drafting"*). As duas filosofias estão instaladas ao mesmo tempo.

**Não existe nenhum ponto do pipeline A em que um humano real leia prosa.** Os três checkpoints
(`book-orchestrator.md:47-63`) aprovam resumos, não texto. O "4-reader simulation" é o mesmo modelo.

**O exemplo-vitrine confirma o padrão.** `examples/protocolo-nao-encontrado/genesis-score.md:13-26`:
três iterações, **todas as dez dimensões sobem e nenhuma desce**, 8.70 → 8.95 → 9.04 — cruzando o
limiar de 9.0 por 0.04 na terceira. Na iteração 3 só os capítulos 1, 6 e 10 foram expandidos, mas
Originalidade, Personagens, Prosa e Emoção subiram todas +0.1. E esse exemplo foi avaliado por uma
rubrica que **não é nenhuma das três atuais** (10 dimensões com pesos 1.2/1.1/1.0/0.8/0.7,
aprovação por média ponderada > 9.0 e mínimo 8.0 — `:33-34`).

O próprio `SHOWCASE.md` admite: *"internal score can rise fast, but external taste still matters"* (`:12`),
*"The evaluator needed calibration against external reader response"* (`:59`). Isso está escrito no repo
e não está refletido no README.

**Severidade: bloqueia o objetivo.** O sistema não consegue distinguir, por si só, um capítulo bom de um
medíocre, e afirma que consegue.

---

## 3. Evidência de execução real: o portão nunca disparou

`book-genesis/books/agenda-2030/` (clone do Desktop, não commitado) é o projeto mais recente do autor:

| medida | valor |
|---|---|
| capítulos escritos | **7** (3.358 / 2.783 / 5.069 / 3.131 / 3.537 / 4.690 / 3.807 palavras) |
| `evaluations/` | **0 arquivos** |
| `revisions/` | **0 arquivos** |
| `delivery/` | **0 arquivos** |
| `STATE.md:12-14` | *"Capítulos escritos: none. Capítulos avaliados: none. Genesis Score: pendente."* |
| capítulos 1, 2, 3, 4, 6 | escritos em **24 minutos** (2026-04-21 22:03 → 22:27) |
| capítulo 7 | 2026-08-31 00:01 |

Sete capítulos, zero avaliações. O estado diz que não há capítulos. O arquivo é `STATE.md`, não o
`STATE.yaml` do orquestrador; a "Fase 2.5 — Calibração RAG" não existe em nenhum dos três pipelines.

**Como o capítulo 7 foi produzido de verdade** (`.write-ch07-prompt.md` + `capture_chapter.py`):
um brief escrito à mão, concreto para este livro ("the dog on the motorway", "Yusuf singing at the gas
station", "Hana and Sami reappear in Chapter 17"), enviado a `codex --json`, com um script Python
que captura a `agent_message` e grava se tiver > 500 palavras. **Sem orquestrador, sem disruptor,
sem avaliador, sem portão.** E os capítulos 1–6 carregam as *craft notes* do escritor **dentro do arquivo
de prosa** (cauda de `chapter-01.md`), o que o spec V4 proíbe (`book-writer.md:297`: vai para
`chapter-N-report.md`) e o próprio brief do capítulo 7 precisa avisar para ignorar.

Isso é o dado mais importante da revisão: **a prosa boa que existe saiu de um brief humano específico +
uma chamada de modelo**, não do loop de 11 agentes. O valor está nos artefatos de fundação
(`foundation.md`, `outline.md`, `voice-dna.md`) e no brief — não no portão.

**Severidade: bloqueia o objetivo** (como evidência de que o mecanismo prometido não é o mecanismo usado).

---

## 4. Inconsistências por arquivo

Severidade: **B** = bloqueia o objetivo · **D** = degrada · **C** = cosmético.

### `agents/book-orchestrator.md`

| # | linha | achado | sev |
|---|---|---|---|
| 4.1 | 83 vs 349 | diagrama: *"auto-loop max 3"*; Step G: *"max 5 iterations"*. **Corrigido neste branch (→ 5).** | D |
| 4.2 | 343 vs `book-evaluator.md:3,229` | orquestrador pede *"5-reader simulation (… Devoted)"*; avaliador se descreve como *"4-reader"* e diz que o Devoted é opcional por gênero. **Corrigido neste branch.** | D |
| 4.3 | 209 + 461-464 | `dimension_7.name` deve ser "set during foundation", mas nenhuma fase escreve esse campo; o avaliador (`:154-155`) lê o campo e **não tem default**. Dimensão 7 pode nunca ser avaliada. **Corrigido neste branch** (Phase 2 passa a gravar; default `market`). | D |
| 4.4 | 120 | diretório do projeto fixo em `~/Desktop/livros/{slug}/`. **Corrigido neste branch** (`./livros/{slug}/` ou o que o usuário nomear). | D |
| 4.5 | 333 | Step E usa `grep -oiP` (PCRE) — não existe no `grep` BSD do macOS; o passo quebra em Mac. **Corrigido neste branch** (classes POSIX). | D |
| 4.6 | 331 | Step E manda **substituir travessões por sed** automaticamente na prosa — edição destrutiva sem revisão, dentro de diálogo. **Corrigido neste branch** (lista para o editor, não substitui). | D |
| 4.7 | 6 | `maxTurns: 200`. Aritmética para o livro de 20 capítulos que o README precifica: setup 6 dispatches + 20 × (5 passos + 0,25 entity) ≈ 111 sem nenhum polish; com a média de 1,5 ciclos que o README assume (`README.md:242`) +60 → ~171; fases 4–6 +5–15 → **~180–190 dispatches**, antes de contar os Read/Write/Bash do próprio orquestrador (STATE.yaml a cada passo, ler cada eval, 5 comandos bash por capítulo). **O orçamento acaba no meio do livro.** Não alterado — é decisão de custo. | B |
| 4.8 | 5 (e em todos os agentes) | `model: opus` fixado; o README precifica com *"Claude Sonnet 4.6 (recommended)"* (`README.md:237`). O custo publicado não corresponde ao modelo configurado. | D |
| 4.9 | 352 vs 526 | ver §2 — "8.5 é o único PASS" vs "7.5 terminado é infinitamente melhor". Decisão de filosofia; não alterado. | B |
| 4.10 | 269, 276 | passa `{approach}` lido de um campo *Structural approach* do outline que o template do arquiteto **não tinha** (ver 4.14). **Corrigido no arquiteto.** | D |

### `agents/book-evaluator.md`

| # | linha | achado | sev |
|---|---|---|---|
| 4.11 | 122 vs 172-175 | *"Each pattern found = -0.25"* vs escala por densidade (-0.125/-0.25/-0.50). **Corrigido neste branch.** | C |
| 4.12 | 433 e 435 | duas regras numeradas "10". **Corrigido (→ 11).** | C |
| 4.13 | 418-429 | as âncoras de calibração ("Characters 8.0 = Bernardi level", "Prose 9.0 = Kalanithi", "Emotion 9.0 = Frankl") são **todas de memoir/não-ficção** e são aplicadas como referência para todos os gêneros, apesar de o mesmo arquivo ter perfis por gênero. | D |
| 4.14 | 311, 125 | *"V3.2 benchmark proved…"*, *"7/10 bestsellers…"*: a base cita `evaluations/00-comparativo-v32-10-bestsellers.md` e `evaluations/eval-v33-outliers.md` (`knowledge/bestseller-dna.md:5`) — **nenhum dos dois existe no repositório** (busca recursiva por `comparativo`, `eval-v33`, `outliers`: zero). A calibração que sustenta os limiares não é verificável. | B |

### `agents/book-architect.md`

| # | linha | achado | sev |
|---|---|---|---|
| 4.15 | 302-330 vs 341-349 vs `book-writer.md:141-152` | **três taxonomias de estrutura**: o template do outline não tinha o campo; o quality check #8 lista **7** tipos (Chronological, Essayistic, Fragmented, In medias res, Parallel, Single-scene, Collage); o escritor executa **8** com nomes diferentes (…Reverse chronological, Spiral, Epistolary, Stream of consciousness); o orquestrador diz "8 types" (`:198`). Um nome que o escritor não reconhece é no-op silencioso. **Corrigido neste branch** (campo adicionado, lista unificada na do escritor). | D |
| 4.16 | 248 | `Sentence rhythm: [Short/staccato \| Mixed/varied \| Long/flowing \| Fragmented]` — rótulo estático aplicado ao livro inteiro. É exatamente o mecanismo que o **PR #14** (contribuidor externo, 05/07/2026, +4/−1) diagnosticou como causa de prosa picotada em cascata pesquisador → arquiteto → escritor. **Não alterado**: recomendo mesclar o PR como está, com crédito. | D |
| 4.17 | 351 | afirma que o avaliador "caps Originality at 7.5" para beat genérico; o avaliador (`:53-64`) não contém essa regra. | C |

### `agents/book-researcher.md`

| # | linha | achado | sev |
|---|---|---|---|
| 4.18 | 115-121 | as "Prose Rules (from top sellers analysis)" são **constantes pré-preenchidas no template** (Flesch ≤ 7, adverbs < 105/10K, "said" 90%+) — o pesquisador é instruído a emitir os mesmos números independentemente do gênero, da língua e do que pesquisou. Mesmo ponto do PR #14. | D |
| 4.19 | 29-34 | todas as queries de busca são em inglês; um livro em português é posicionado contra o mercado errado. Idem PR #14. | D |

### `agents/book-editor.md`

| # | linha | achado | sev |
|---|---|---|---|
| 4.20 | 32 | *"dialogue 25-35%"* flat, contra as faixas por gênero que o avaliador, o arquiteto e o dialogue-polish usam. **Corrigido neste branch.** | C |

### `agents/book-packager.md` × `README.md`

| # | linha | achado | sev |
|---|---|---|---|
| 4.21 | `README.md:143` *"Formatted ebook + print files"* vs `book-packager.md:163-211,260` | o packager escreve **especificações** de EPUB/POD em texto e um `manuscript-final.[format]` com placeholder; nenhum conversor (pandoc, calibre, epubcheck) é invocado em lugar nenhum do repo. Não existe geração de EPUB/PDF em código. | D |

### `README.md`

| # | linha | achado | sev |
|---|---|---|---|
| 4.22 | 283-306 e 321-341 | seções *Community* e *Documentation* duplicadas (a segunda sem a linha Coverage Plan). **Corrigido neste branch.** | C |
| 4.23 | 11, 278, 300 | *"Books Shipped 10+"*. `docs/book-gallery.md:20-31`: **1** manuscrito completo local (The Source Code), **2** "artifact sets" sem manuscrito, **7** "local manuscript/draft project". O próprio gallery oferece uma "more precise version" (`:44`) e recomenda a curta só para Twitter (`:47`). O README usa a curta. | D |
| 4.24 | 224-231 | os dois "real examples" descrevem ideias que **não são os livros**: Protocolo Não Encontrado não é "growing up between two cultures" (é saúde mental como burocracia que devolve erro — `examples/protocolo-nao-encontrado/genesis-score.md:139`); Age of Aquarius não é "chess players running an intelligence network" (é uma IA que decodifica tradições espirituais — `examples/age-of-aquarius/synopses.md:10`). | D |
| 4.25 | 298, 334 | o link *Architecture* aponta para `docs/book-genesis-codex.md` (pipeline B), enquanto o corpo do README descreve o pipeline A e `docs/architecture.md` descreve o C (24× `STATE.yaml`, 7× skills deprecated, 0× `book-orchestrator`). | D |
| 4.26 | 179 | *"a separate agent that never wrote any of them. No self-grading."* — verdadeiro só como contexto de execução; é o mesmo modelo, com prompts do mesmo autor. Ver §2. | B |
| 4.27 | 117-119 | *"Score < 7.0 → escalate"* — o orquestrador usa piso por gênero (literário/memoir 7.5). | C |

### `AGENTS.md` × `README.md` × instaladores

| # | achado | sev |
|---|---|---|
| 4.28 | `AGENTS.md:7-13,42` trata V4 como legado e manda usar `book-genesis-codex`; `README.md` inteiro documenta só o V4; `install.ps1:18` imprime *"V4/V5 legacy system + portable Codex edition"* e `:96` manda digitar `/book-genesis`. Três documentos, três canons. | B |
| 4.29 | `install.ps1:36-40` exclui `skills/deprecated/` mas instala `skills/optional/` — `continuity-guardian` e `entity-tracker` são instalados **duas vezes**, como skill (576 e 568 linhas) e como agente (97 e 163 linhas), com o mesmo nome. As versões "superadas" são 3–6× mais detalhadas que as "atuais" (`deprecated/hook-craft` 527 vs `agents/hook-craft.md` 95). Não está claro se detalhe foi perdido ou compactado de propósito. | D |
| 4.30 | `install.ps1:72-87` — *"Pipeline verified"* verifica só que 11 arquivos `.md` existem; não verifica `knowledge/` nem que skills resolvem. O README (`:51`) descreve como verificação completa. | C |

### `skills/`

| # | achado | sev |
|---|---|---|
| 4.31 | `skills/book-genesis/references/` e `skills/book-genesis-codex/references/` são cópias (dois `legacy-v4-book-genesis.md` de 49 KB) **que já divergiram**: `book-genesis` tem `prompts/literary-barrier-loop.md` e manifesto de 8 fases; `codex` tem 7. O runner só lê o do codex. | D |
| 4.32 | `book-genesis-codex/SKILL.md:87-94` e `book-genesis/SKILL.md:110-118` referenciam `launch-strategy`, `content-strategy`, `imagegen` — não existem em `skills/`. | C |
| 4.33 | `book-genesis-codex` manifesto produz `artifacts/06-emotional-curve.md`; o arquiteto V4 (`:158-160`) proíbe curvas emocionais numéricas em favor de âncoras. Filosofias opostas para o mesmo conceito, instaladas juntas. | D |

### `docs/genesis-score.md` ("Complete Specification")

| # | linha | achado | sev |
|---|---|---|---|
| 4.34 | 227-236 vs `book-evaluator.md:326-335` | CVI-Launch com inputs **completamente diferentes** do avaliador; idem CVI-Legacy (`:261-267` vs `:349-353`). | B |
| 4.35 | 234 | *"Zero platform = score capped at 6.0"*. Para o público-alvo declarado ("qualquer merdão"), o CVI-Launch fica **matematicamente incapaz** de chegar a 9.0 sob esta definição. | B |
| 4.36 | 249 vs `book-orchestrator.md:377` | gate CVI-Launch ≥ **7.0** vs ≥ **9.0**. | B |
| 4.37 | 3-5 | *"~75 calibrations… Accuracy: 85% average"* — o que "acurácia de uma nota" significa não é definido, e os arquivos de calibração não estão no repo (4.14). | D |
| 4.38 | 25 vs `book-evaluator.md:53-64` | Originalidade "list 3 unique elements or ≤ 7.0" vs genre-adjusted (commercial precisa de 1). | C |

### `knowledge/bestseller-dna.md`

| # | linha | achado | sev |
|---|---|---|---|
| 4.39 | 251-263 | **bibliografia real e boa** (Archer & Jockers, Reagan et al., Blatt, Zak, Green & Brock, Berger). Isso é um ponto forte. | — |
| 4.40 | 5 | validação citada em dois arquivos inexistentes (4.14). | B |
| 4.41 | 30 | Literary Fiction "sweet spot ~98,000, range 80,000–95,000" — o ponto ótimo está fora da própria faixa. | C |
| 4.42 | 175, 183-185 | *"5 reviews = +270% em vendas"*, *"Memoir +54% YoY"* — sem fonte rastreável à bibliografia. | D |
| 4.43 | 91 | "25-35% diálogo" — a origem da constante estagnada do editor (4.20). | C |

### Exemplos, casos, showcase

| # | achado | sev |
|---|---|---|
| 4.44 | `examples/protocolo-nao-encontrado/genesis-score.md` é público sob MIT e contém detalhes clínicos e familiares do autor (tentativa de suicídio no cap. 4, ECT, valores, relação com a mãe, ex-namorada). É o memoir do próprio autor. **Decisão dele**, mas deve ser consciente. | — |
| 4.45 | `SHOWCASE.md:66` *"Full manuscripts are intentionally not included"* — coerente. Mas então "10+ books shipped" no README não tem evidência pública além de capas (`docs/book-gallery.md`). | D |

### GitHub

| # | achado | sev |
|---|---|---|
| 4.46 | **PR #14** (nakamuraos, 2026-07-05): contribuidor externo diagnosticou a cascata rhythm-label → prosa picotada, validou fim a fim num thriller em vietnamita, mudança de +4/−1 linhas. **Aberto há dois meses, sem revisão.** É a única contribuição externa substantiva do projeto. | D |
| 4.47 | PR #2 (README revamp) aberto desde 21/05; PR #15 e #18 abertos. Issue #16 "Missing agents" (bug) corrigida em 29/07 pelo PR #17. | C |
| 4.48 | 36 forks, 113 estrelas (API, 02/09). Dos 36 forks, atividade própria ≈ 0 (dois têm 1 estrela). | — |

### Fora do repositório

| # | achado | sev |
|---|---|---|
| 4.49 | `studio/` no clone do Desktop: monorepo pnpm com 13 pacotes, **118 arquivos de teste**, releases 0.1.0–0.1.4 construídos — **não rastreado pelo git** (`git ls-files studio` = 0). `book-genesis-cli/`: 0 commits. O "Book Genesis Studio, 272 testes, 92,6%" que aparecia no currículo do autor **não existe em nenhum repositório**. O repo público tem 12 testes. Currículo, dossiê e site foram corrigidos hoje. | B |
| 4.50 | `book-genesis/CLAUDE.md` (clone do Desktop, não rastreado) contém as regras *Anti-Inflação de Scores* e *Anti-Echo-Chamber* — as regras de honestidade mais importantes do projeto **não são distribuídas** para quem instala. | D |

---

## 5. O que está bem feito

- **A autoconsciência do avaliador é rara.** `book-evaluator.md:405-433`: default 7.0 com marcação "INSUFFICIENT DATA", +0.5 por ciclo, piso em vez de média, "your bias is maximum", BIAS CHECK obrigatório no fim. Poucos sistemas escrevem isso sobre si mesmos.
- **O adversarial-audit do pipeline B** (`references/prompts/adversarial-audit.md`) é curto, afiado e correto: *"The writing system is biased toward approving itself."* Sete passes concretos (existence test, over-explanation, human mess, failure audit, agent pitch test).
- **O escritor** tem instrução de ofício real, não genérica: frase feia obrigatória, caos habitado vs. mediado, disfarces de exposição, direitos de observação e conhecimento, transições variadas.
- **O disruptor** mira um fingerprint real do Claude (Simile Surgery, `book-disruptor.md:41-59`) com exemplo antes/depois.
- **O entity-tracker** com `knowledge: learned_chapter + source` (`:49-58`) ataca o bug de continuidade nº 1 de ficção por IA de um jeito que quase ninguém faz.
- **O runner é honesto** (`AGENTS.md:50`: "does not call a model or write literary output"), testado (12/12), sem dependências, com fail-closed no avanço de fase.
- **O instalador verifica** que os 11 agentes resolvem (corrigido após a issue #16 real).
- **A base de conhecimento tem bibliografia de verdade** (4.39).
- **O capítulo 1 do agenda-2030 é boa prosa** — e o brief manual do capítulo 7 é melhor que qualquer agente por ser específico a este livro.
- **Os textos de gate do `agent-registry.yaml`** são honestos: *"No bestseller claim without evidence and launch math"*, *"Niche approval never claimed as real-world validation"*.

---

## 6. Correções aplicadas neste branch (`review/consistencia-2026-09`)

Só o que não envolve decisão de produto. Cada uma é uma linha de `git diff`:

1. `README.md` — removidas as seções *Community* e *Documentation* duplicadas (4.22).
2. `agents/book-orchestrator.md` — diagrama "max 3" → "max 5" (4.1); "5-reader" → "4-reader + Devoted por gênero" (4.2); Phase 2 grava `dimension_7.name` com default `market` (4.3); diretório padrão `./livros/{slug}/` (4.4); Step E sem `-P` e sem `sed` destrutivo (4.5, 4.6).
3. `agents/book-evaluator.md` — peso do anti-AI referenciando a escala por densidade (4.11); numeração da regra 11 (4.12).
4. `agents/book-editor.md` — diálogo por faixa de gênero (4.20).
5. `agents/book-architect.md` — campo *Structural approach* no template do outline e taxonomia unificada com a do escritor (4.15).

Não commitado ainda: fica no branch para revisão por `git diff master`.

---

## 7. Decisões que são do autor (não apliquei)

1. **Qual pipeline é o produto.** A, B ou C. Os outros dois vão para `legacy/` com aviso, e README, AGENTS.md
   e instalador passam a apontar para **um só**. Enquanto três coexistem, "qualquer pessoa" não roda nada.
2. **Uma rubrica.** 7 dimensões com piso (A) ou 10 com média ponderada (B). Não as duas. E **um** portão de CVI.
3. **Validação humana cega.** É a única coisa que transforma "8.5 interno" em claim. Desenho mínimo: 10–20
   leitores, capítulos do sistema misturados com capítulos publicados do mesmo gênero, sem saber qual é qual,
   pergunta única: *viraria a página?* Publicar o resultado, seja qual for. O `SHOWCASE.md:59` já reconhece
   que isso falta.
4. **Mesclar o PR #14** como está, com crédito ao contribuidor. Dois meses de fila é o sinal errado para
   um projeto que pede contribuições no README.
5. **"10+ books shipped"** → a "versão precisa" que o próprio `book-gallery.md:44` já escreveu.
6. **Corrigir as duas descrições de exemplo** do README (4.24) para o que os livros são.
7. **`maxTurns`** do orquestrador (4.7) — ou subir, ou reduzir o pipeline por capítulo.
8. **Commitar `studio/`** (ou decidir que não é parte do projeto). Hoje é trabalho invisível e o currículo
   não pode citá-lo.
9. **Distribuir as regras anti-inflação** do `CLAUDE.md` local (4.50) — colocá-las dentro do
   `book-evaluator.md` ou num `CLAUDE.md` versionado.
10. **O exemplo do memoir** (4.44) — manter público é escolha legítima; que seja consciente.
11. **Filosofia do portão** (4.9): "8.5 ou nada" e "7.5 terminado vence" não podem ser as duas instruções
    do mesmo orquestrador.

---

## 8. Sobre o objetivo

"Qualquer pessoa criativa com uma ideia boa gera um livro de nível best-seller."

O que o repositório **prova hoje**: que um brief humano específico + fundação bem construída + uma chamada
de modelo produzem prosa competente (agenda-2030, cap. 1). Que o sistema sabe **nomear** os defeitos típicos
de prosa de IA com precisão incomum. Que existe uma base bibliográfica real por trás dos critérios.

O que o repositório **não prova**: que o portão de 8.5 distingue bom de medíocre (§2); que o loop de 11
agentes foi usado no último livro (§3); que qualquer saída foi lida por um humano que não é o autor
(§2, `SHOWCASE.md:59`); que "10+ livros" existem além de capas (4.23, 4.45).

O caminho mais curto até o objetivo **não é mais um agente**. É: escolher um pipeline, uma rubrica, e
colocar um leitor cego no fim. Se o teste cego passar, o README pode dizer o que diz hoje. Se não passar,
o projeto descobre onde a prosa falha de verdade — o que vale mais do que 113 estrelas.
