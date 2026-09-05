# ADR 0007 — Modelos por versão: lista viva, sondagem real e cache

Status: aceito, 2026-09-04.

## Contexto

O seletor de modelos do `setup` mostrava `opus`, `sonnet`, `haiku` e `gpt-5.5` como se
fossem "os modelos". O Felipe pediu as versões reais — Sonnet 4.5 e 5, Opus 4.7, 4.8 e 5,
a família GPT inteira — e pesquisa antes de implementar.

A pesquisa (2026-09-03) encontrou três fontes que discordam entre si, e é isso que decide
o desenho:

1. **Documentação da Anthropic** (visão geral de modelos): família atual é Fable 5.1,
   Opus 5, Sonnet 5 e Haiku 4.5; Opus 4.8/4.7/4.6/4.5 e Sonnet 4.6/4.5 continuam
   disponíveis. Recomendação da própria doc: "comece pelo Opus 5"; Sonnet 5 é "a melhor
   combinação de velocidade e inteligência".
2. **Catálogo do OpenRouter** (ids reais para API): `anthropic/claude-opus-5`,
   `openai/gpt-5.5`, `gpt-5.5-pro`, `gpt-5.4`, `gpt-5.2`, `gpt-5.1`, `o3`, `o4-mini`,
   `deepseek/deepseek-v4-pro`, `google/gemini-3.x`, e por aí vai. Doc da OpenAI: 5.6
   (sol, terra, luna), 5.5, 5.4.
3. **Sondagem na máquina dele** (uma chamada real por id):
   - Claude Code aceitou `claude-opus-5`, `claude-sonnet-5`, `claude-haiku-4-5-20251001`,
     `claude-opus-4-8`, `claude-opus-4-7`, `claude-opus-4-1`, `claude-sonnet-4-5` e os
     aliases `opus`/`sonnet`/`haiku`; recusou `claude-fable-5-1` e os modelos aposentados
     (Sonnet 4 em 15/06/2026, Haiku 3.5 em 19/02/2026).
   - Codex aceitou **só** `gpt-5.5` e `gpt-5.4`; recusou `gpt-5.5-mini`, `gpt-5.5-codex`,
     `gpt-5`, `o3`, `o4-mini`.

Uma lista estática, por mais pesquisada, estaria errada em qualquer máquina que não a
dele — e ficaria velha na próxima semana.

## Decisão

Nenhuma lista de modelos é digitada no código como verdade.

- **Provedores por API** (OpenRouter, DeepSeek, OpenAI, Anthropic, locais): `/models` ao
  vivo, filtrado por `chat_models_only` (fora embeddings, voz, imagem, moderação, variantes
  `:batch`, snapshots datados que têm gêmeo sem data), ordenado por `sort_models` (versão
  mais nova primeiro, base antes da variante).
- **CLIs por assinatura** (Claude Code, Codex): `CLI_CANDIDATES` traz os ids das
  documentações como **entrada** de uma sondagem real — `probe_models`, uma chamada
  minúscula por id, quatro em paralelo, ~1 minuto. Só o que respondeu é mostrado. O
  resultado fica em `~/.book-genesis/models-cache.json` por 7 dias; apagar o arquivo força
  nova sondagem. Se a sondagem não achar nada (offline), o wizard cai nos aliases para não
  travar.
- **Etiqueta por tier** (`tag_model`), pela convenção de nomes que todo provedor usa:
  mini/nano/haiku/flash/lite/luna = mais barato; opus/fable/pro/ultra/sol/o-série = o mais
  forte; o resto = equilíbrio. Token inteiro, para "gemini" não virar "mini".
- **Recomendado pré-selecionado** conforme a doc do provedor: escritor `claude-opus-5`,
  juiz `claude-sonnet-5`; no Codex, `gpt-5.5` (o padrão do próprio CLI).
- **"Change it" preserva provedores e chaves já salvos**; só "Reset" apaga, e avisa antes.
  Motivo: em 2026-09-03 uma reexecução do wizard apagou as chaves da OpenAI e da DeepSeek
  que o Felipe tinha colado. Isso não pode repetir.

## Consequências

- A primeira sondagem custa cerca de um minuto por CLI, depois cache de uma semana.
- Todo id mostrado para um CLI foi aceito **naquela máquina** — não há mais "modelo que
  aparece na lista e falha na hora".
- `CLI_CANDIDATES` vai ficar desatualizado, e tudo bem: é só entrada da sondagem. Quando
  um provedor lançar modelo novo, adiciona-se o id à lista de candidatos; a sondagem decide.
- Um id que a sondagem recusa hoje pode ser aceito amanhã (Fable 5.1 no Claude Code, por
  exemplo). Apagar o cache resolve; um `setup --refresh-models` fica para quando o `cli.py`
  estiver livre de edições concorrentes.
