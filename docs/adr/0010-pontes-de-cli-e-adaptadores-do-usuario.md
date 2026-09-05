# ADR 0010 — Pontes de CLI e adaptadores declarados pelo usuário

Status: aceito, 2026-09-04.

## Contexto

"Conecte com a porra toda." O público é vibecoder: ele já tem os CLIs dele instalados e
logados, e talvez uma API por fora. Antes da ADR 0009 o caminho nativo cobria Claude Code e
Codex, e as APIs cobriam OpenRouter, DeepSeek, OpenAI, Anthropic, Gemini API, Groq, Together,
Ollama e LM Studio. Faltavam dois CLIs que o Felipe tem instalados agora: o **Antigravity
CLI** (`agy`, sucessor do Gemini CLI, que morreu para conta individual em 18/06/2026) e o
**Hermes**.

Duas travas atrapalhavam:

1. **Prompt de capítulo não cabe em linha de comando.** O Windows corta em 32 mil
   caracteres. O `bridge_gemini.py` existente passa o prompt como argumento, então quebra
   exatamente no uso real. Toda ponte nova manda o prompt por stdin.
2. **Declarar um CLI exigia editar o repositório.** `runner/config/adapters.yaml` é
   versionado: quem adicionasse o CLI dele levava conflito em todo `git pull`.

## Medições (04/09/2026, na máquina do Felipe)

| CLI | Comando que funciona | Resposta |
|---|---|---|
| `agy` 1.1.26 | `agy --input-format stream-json --output-format stream-json`, evento `{"event":"user","message":{"content":...}}` no stdin | `{"event":"result","result":{"status":"SUCCESS","response":"OK\n"}}` |
| `hermes` | `hermes chat -Q --query-file -`, prompt no stdin | stdout abre com `Warning: Unknown toolsets: bfl`, depois a resposta; `session_id` vai para stderr |

Duas armadilhas medidas, não supostas:

- O `agy` devolve **exit 0 com `status: ERROR`** quando a cota estoura
  (`Individual quota reached... Resets in 3h17m45s`, visto às 10:11 e já liberado às 13:30).
  Confiar no código de saída entregaria um capítulo vazio; quem decide é o `status`.
- O `hermes` escreve aviso no **stdout**, junto com a prosa. Sem filtrar, o aviso entraria no
  livro.

## Decisão

1. **`runner/bridge_antigravity.py`** e **`runner/bridge_hermes.py`**: prompt sempre por
   stdin, resposta limpa no stdout, erro no stderr com o motivo e saída não-zero, que é o
   contrato que o `GenericCliAdapter` já espera.
2. **`~/.book-genesis/adapters.yaml`** (ou `BOOK_GENESIS_ADAPTERS`) é lido **por cima** do
   `runner/config/adapters.yaml`. Mesmo padrão de `models.yaml` versus
   `~/.book-genesis/config.yaml` da ADR 0003: padrão do repositório, pessoa por cima, sem
   fork e sem conflito no update.
3. **As duas pontes não entram no `adapters.yaml` do repositório.** Quem tem o CLI declara em
   duas linhas. Motivo abaixo.

## Consequência que fica apontada, não resolvida

`available_adapters()` em `runner/roles.py` decide se um adaptador genérico existe olhando o
**primeiro token do template**. Como todo template começa com `python`, qualquer entrada do
`adapters.yaml` aparece como "instalada" em qualquer máquina, e `plan_roles` pode escolher
`gemini` como juiz automático de quem só tem Claude e nunca rodou o `setup`. Já estava assim
com `gemini` e `muse-spark`; declarar `agy` e `hermes` no repositório pioraria o problema, por
isso elas ficam de fora até a checagem olhar o executável de verdade (o `agy`/`hermes` dentro
do template, não o `python`). `roles.py` está com edições de outra sessão e não foi tocado.

## Provas

Chamadas reais pelo caminho de produção (`build_adapter` → `GenericCliAdapter` → ponte → CLI):

```
OK    agy gemini-3.8-flash-low            4.4s  'OK'
OK    agy (default model)                 5.2s  'OK'
OK    hermes (default model)             11.3s  'OK'
OK    refused model fails loudly: agy status=ERROR: invalid model selection...
```

Modelos do `agy` nesta conta (`agy models`): `gemini-3.8-flash-high/medium/low`,
`gemini-3.7-flash-*`, `gemini-3.6-flash-*`, `gemini-3.1-pro-high/low`, `claude-sonnet-4-6`,
`claude-opus-4-6-thinking`, `gpt-oss-120b-medium`. Vale lembrar que a cota grátis individual
do Antigravity é de dezenas de chamadas por dia; um livro inteiro precisa de centenas.
