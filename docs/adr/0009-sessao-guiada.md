# ADR 0009 — A sessão guiada: ideia, acompanhar, concordar, livro com nota

Status: aceito, 2026-09-04.

## Contexto

O Book Genesis vai ser open source para leigos e vibecoders. O Felipe descreveu a
experiência-alvo: "o cara dá a ideia, vai acompanhando, vai concordando, igual ao que temos
no Claude Code, só que do jeito que ele quiser: com Codex, com agy, com o que ele tiver lá."
Antes, isso eram skills só do Claude Code (orquestrador com três checkpoints humanos). Hoje o
runner é autônomo por padrão (ADR 0002) e o `new` imprime linhas de log. Não é a experiência
de "acompanhar e concordar".

## Decisão

1. **`book-genesis` (sem argumentos) e `book-genesis new` num terminal abrem a sessão
   guiada.** Cabeçalho com a ideia e quem escreve/julga; trilha de estágios (Intake,
   Foundation, Architecture, Drafting, Audit, Score, Package) com o estágio ativo girando e o
   tempo de cada um; a última meia dúzia de eventos do pipeline embaixo (escritor, disruptor,
   juiz disse X, editor ciclo 2...).
2. **Três pontos de concordância**, cada um mostrando o artefato inteiro e perguntando uma
   coisa só: o brief (depois do Intake), o outline (depois da Architecture) e o capítulo 1
   lido às cegas (veredito do painel, o que os leitores lembraram, o trecho de abertura).
   `Enter` concorda. Texto livre vira **notas do autor** (`work/author-notes.md`), que
   entram no prompt da fase e no brief de todo capítulo seguinte; a fase (ou o capítulo 1)
   roda de novo com elas, no máximo duas vezes por ponto. `q` para; `book-genesis resume`
   continua de onde parou.
3. **Autonomia continua sendo o modo sem terminal.** `--yes`, stdin/stdout sem TTY ou CI:
   nenhuma pergunta, comportamento idêntico ao de hoje (ADR 0002). `--human` (pausa até
   `approve`) continua existindo. `--plain` desliga a interface viva e imprime linhas.
4. **A nota é o Genesis Score, calculado só do que leitores cegos fizeram.** Nunca uma
   autoavaliação do escritor (a revisão de 02/09 mostrou que o portão 8.5 antigo não media
   nada). Quatro componentes, pesos fixos: painel de leitores que viraria a página no cap. 1
   (40%), capítulos aceitos no primeiro rascunho (30%), capítulos aceitos no fim (20%),
   capítulos em que o leitor lembrou algo específico (10%). Sai de 0 a 10 com uma casa,
   com os quatro números ao lado para ninguém confundir com mágica. Vai para o
   `RUN_REPORT.md` e para a tela.
5. **Interface com `rich`.** É a primeira dependência do runner (14.x, puro Python, funciona
   no Windows Terminal, no conhost e em pipes). Sem terminal ou sem `rich`, a `PlainView`
   imprime o mesmo conteúdo em linhas. Toda a sessão fala com uma `View` injetável: os
   testes rodam a sessão inteira com o adaptador falso e uma `RecordingView`, sem rede.
6. **O `runner/cli.py` fica como camada de comandos.** `runner/app.py` é o novo ponto de
   entrada: `new`/`resume` vão para a sessão, o resto para o `cli.py` como está. Motivo
   prático: `cli.py`, `book.py`, `chapter.py`, `roles.py` e `adapters.py` têm edições não
   commitadas de outra sessão (ADR 0006); a sessão nova só depende das funções públicas
   deles (`run_phase`, `run_book`, `build_role_adapters`) e não os toca. Quando aquele
   trabalho pousar, o `new`/`resume` do `cli.py` podem ser removidos.

## O console do Windows (medido, não suposto)

A primeira gravação da sessão **quebrou com `UnicodeEncodeError`**: o `rich` desenha painel
com caractere de caixa Unicode e o console do Windows em cp1252 não consegue escrever. Um
vibecoder no Windows veria um traceback no lugar do livro. É o mesmo defeito da ADR 0005,
que na época foi resolvido só para o banner.

Medido em 04/09/2026 nesta máquina:

| Onde a saída vai | `sys.stdout.encoding` | O que a sessão desenha |
|---|---|---|
| console de verdade (`isatty` true) | `utf-8` | Unicode: `╭─╮`, `✔`, spinner |
| cano (pipe, log, CI) | `cp1252` | ASCII: `+-|`, `+`, `>` |

Decisões que saem disso:

1. `force_utf8()` pede UTF-8 ao stream antes de qualquer decisão — **é o que faz a versão
   bonita funcionar**; sem ele o primeiro `✔` derruba a execução.
2. `unicode_safe()` testa de verdade se a codificação carrega `─╭║`; só então usa Unicode.
   Stream sem codificação (captura em memória) é considerado capaz.
3. Mensagem vinda de fora (erro de provedor, caminho com `[draft]`) vira `Text`, nunca
   markup do rich: impressa como markup, o `[draft]` sumia junto com o resto da linha.
4. Sem widget ao vivo (cano, log), cada etapa concluída imprime **uma linha**, não a trilha
   inteira: reimprimir as sete etapas a cada uma empilhava sete cópias no log.
5. O `# Título` do próprio artefato é removido antes de renderizar: o painel já tem título e
   o rich desenha um H1 como uma moldura pesada, dando moldura dentro de moldura.

Cada um desses tem teste de regressão, o do cp1252 rodando contra um stream que **de fato**
levanta `UnicodeEncodeError`.

## Provedores

"Conectar com a porra toda", por caminho:

| O que a pessoa tem | Como entra | Estado |
|---|---|---|
| Claude Code, Codex | adaptadores nativos, sondados (ADR 0007) | pronto |
| OpenRouter, DeepSeek, OpenAI, Anthropic, Gemini API, Groq, Together, Ollama, LM Studio | chave no `setup`, lista viva | pronto |
| Antigravity CLI (`agy`) | bridge por stdin stream-json (ADR 0008) | desenho pronto, verificação presa na cota |
| opencode | `bridge_opencode.py` (outra sessão) | existe, não verificado por mim |
| Hermes | `hermes chat -Q --query-file - -m {model}` (prompt por stdin, silencioso) | a sondar |
| nada | `--manual`: prompts em arquivo, resposta colada | pronto |

## Consequências

- Uma sessão real custa o mesmo que hoje em chamadas; os checkpoints só param o relógio.
- Notas do autor mudam o que o modelo recebe, não o que o runner faz: o contrato de
  arquivos das fases e o brief continuam determinísticos.
- A nota não sobe porque o escritor jurou que está bom; sobe quando leitores cegos viram a
  página. Um 9 significa "3 de 3 leitores viraram a página e quase nenhum capítulo
  precisou de revisão", e a tela diz isso.
