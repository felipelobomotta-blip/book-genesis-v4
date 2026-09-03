# ADR 0002 — Autonomia por padrão: painel de leitores no lugar do humano; roda com o que estiver instalado

**Status:** aceito em 02/09/2026 pelo autor (Felipe). Substitui a decisão 11 do ADR 0001.
**Princípio declarado por ele:** "Não precisa de humano. Se um humano faz, a gente faz."

## 1. Contexto

O ADR 0001 colocou um checkpoint humano depois do capítulo 1 e deixou o juiz fixo no `codex`.
Duas consequências contra o objetivo do produto ("qualquer pessoa criativa, só com a ideia"):
o runner para e espera alguém; e quem só tem Claude Code, ou só tem Codex, ou usa outra
ferramenta, recebe um erro no meio do capítulo.

## 2. Decisões

1. **Sem humano no loop por padrão.** O checkpoint depois do capítulo 1 sai. Quem quiser
   mantê-lo usa `--human`. O comando `approve` continua existindo para esse modo.
2. **O que o humano fazia, um painel faz.** No capítulo 1 (e em qualquer capítulo pedido com
   `panel`), a prosa é lida às cegas por vários leitores-modelo: famílias diferentes quando
   disponíveis, personas diferentes sempre (o leitor que compra o gênero, o hostil que não queria
   ler, o casual que dá dez páginas num aeroporto). Cada um responde o mesmo bloco do `book-judge`.
   O painel agrega: `turn_page` por maioria; flags citadas por pelo menos dois leitores (ou por um,
   quando o painel tem dois); `stopped_at` mais citado; `remember` em união. O resultado é um
   `Verdict` como qualquer outro, e o loop de edição trata igual.
3. **O runner descobre o que está instalado.** `doctor` mostra os adaptadores encontrados e o plano
   de papéis. Se o adaptador configurado para um papel não existe, o papel cai no primeiro que
   existe. O juiz prefere uma família diferente da do escritor; quando só há uma família, o juiz
   usa um modelo diferente do escritor e o runner escreve um aviso de **família única** no
   `RUN_REPORT.md` e na tela. Família única é modo degradado declarado, não falha.
4. **Adaptador genérico.** `runner/config/adapters.yaml` declara qualquer CLI por um template de
   comando (`{model}` é substituído; prompt no stdin; resposta no stdout). Cobre opencode, ollama,
   Hermes, DeepSeek por CLI, e o que aparecer.
5. **Adaptador manual.** Para quem só tem um chat (Antigravity, DeepSeek na web): o runner grava o
   prompt em `work/manual/<hash>-<papel>.prompt.md` e para com exit 5. A pessoa cola a resposta em
   `work/manual/<hash>-<papel>.response.md` e repete o mesmo comando; o runner encontra a resposta
   pelo hash do prompt e continua. Os prompts são determinísticos, então o hash é estável.
6. **O `RUN_REPORT.md` é o lugar do humano.** Tudo o que antes seria dito a uma pessoa no
   checkpoint vai para o relatório: capítulo, ciclos, veredito de cada leitor, avisos.

## 3. O que isto não muda

Um painel de modelos não é validação externa. O README passa a dizer "cada capítulo foi lido às
cegas por N leitores-modelo de M famílias" e nunca "validado por leitores". O protocolo de teste
cego com pessoas continua existindo como estudo separado, opcional, fora do runner.

## 4. Costuras sob teste

| costura | comportamento verificado |
|---|---|
| `runner.roles.plan_roles(available)` | duas famílias → mapa padrão; só claude → juiz no claude com modelo diferente do escritor e aviso de família única; só codex → tudo no codex; nada → erro que nomeia o que instalar |
| `runner.panel.aggregate(verdicts)` | maioria, flags por citação dupla, `stopped_at` mais citado, união de `remember` |
| `runner.panel.PanelJudge.judge(...)` | cada membro recebe a prosa e a própria persona; devolve um `Verdict` agregado |
| `runner.chapter.run_chapter(..., human_checkpoint=False)` | capítulo 2 roda sem aprovação por padrão; com `human_checkpoint=True` levanta `AwaitingHuman` |
| `runner.book.run_book(...)` | com painel, o capítulo 1 é julgado pelo painel; sem `--human` o livro segue |
| `runner.adapters.GenericCliAdapter` | monta o comando a partir do template; lê stdout |
| `runner.adapters.ManualAdapter` | primeira chamada grava o prompt e levanta `AwaitingManual`; com resposta no disco, devolve o texto |
| CLI `doctor`, `panel`, `--human`, exit 5 | por caminho, com `--fake-responses` |

## 5. Reversão

Tudo no branch `arch/runner-orchestrates`, em commit próprio. Reverter o commit devolve o
checkpoint humano e o juiz fixo.
