# ADR 0008 — Família única e a segunda família grátis

Status: aceito, 2026-09-04.

## Contexto

O público é leigo e vibecoder, com **uma** assinatura: só Claude, só ChatGPT, ou só Google.
O portão do Book Genesis é um juiz cego de outra família (ADR 0001); com uma família só, o
juiz compartilha o gosto do escritor, e um modelo julgando a própria prosa se prefere
(autopreferência). A pergunta do Felipe: "e se o cara tiver só Claude? só OpenAI? e o
Antigravity?"

Pesquisa (04/09/2026):

- **Gemini CLI parou de servir contas individuais em 18/06/2026**; o sucessor é o
  Antigravity CLI (`agy`, em Go). `agy -p` roda headless, `--model` recusa id desconhecido com
  exit 1, `--output-format json` devolve `{status, response, error}`, e com
  `--input-format stream-json` o prompt entra por stdin (uma linha
  `{"event":"user","message":{"content":...}}`) e a resposta sai no evento
  `{"event":"result","result":{"status","response"}}`. Na máquina do Felipe (agy 1.1.26,
  `agy models` lista gemini-3.8/3.7/3.6-flash, 3.1-pro, claude-sonnet-4-6,
  claude-opus-4-6-thinking, gpt-oss-120b) a chamada voltou
  `Individual quota reached... upgrade your subscription. Resets in 3h`. Cota grátis
  individual é de dezenas de chamadas por dia; um livro precisa de centenas.
- **API do Gemini** (chave do Google AI Studio, conta Google, sem cartão): endpoint compatível
  com OpenAI em `https://generativelanguage.googleapis.com/v1beta/openai`, `/models` funciona,
  e a página de preços marca os modelos Flash (3.8, 3.7, 3.6, 3.5, lite) como gratuitos. A
  chave que o Felipe tinha colado (`AQ.`...) é exatamente isso: `/models` respondeu 200 com 55
  ids e `gemini-3.8-flash` respondeu "OK" em 1,2 s.

## Decisão

1. **Família única, juiz irmão.** Quando o mesmo provedor escreve e julga, o juiz nunca é o
   modelo que escreveu: Opus escreve e Sonnet julga (já era o preset), gpt-5.5 escreve e
   gpt-5.4 julga (`SIBLING_JUDGE`). No quick start, se o irmão for recusado, o juiz cai para o
   mesmo modelo e diz isso; nada de beco sem saída para leigo. A nota de família única passa a
   ser honesta sobre o limite e a apontar a saída de um minuto.
2. **Gemini API é "a segunda família grátis".** Entra no menu com esse rótulo, padrão
   `gemini-3.8-flash` (gratuito, funciona para todo mundo; o 3.1 Pro aparece na lista viva
   marcado como o mais forte, para quem paga). `GEMINI_API_KEY` no ambiente é detectada; o
   quick start monta "Claude escreve, Gemini julga" sem perguntar nada. Chave detectada no
   ambiente nunca é pedida de novo.
3. **Antigravity fica para depois, com o desenho pronto.** O `bridge_gemini.py` atual (da outra
   sessão) passa o prompt por argumento de linha de comando, que estoura o limite de 32 mil
   caracteres do Windows em prompt de capítulo; a versão robusta usa stdin stream-json e lê
   `result.response`. Não foi escrita hoje porque o caminho de sucesso não pôde ser verificado
   (cota esgotada). Vale para quem paga Google AI Pro/Ultra; para conta grátis, a cota não
   cobre um livro.

## Consequências

- Quem só tem Claude: Opus 5 escreve, Sonnet 5 julga, painel de três leitores em Sonnet 5.
  Funciona de ponta a ponta; o portão é mais fraco e o wizard diz isso e diz o conserto.
- Quem só tem ChatGPT: gpt-5.5 escreve, gpt-5.4 julga (ou 5.5, com aviso). Mesma nota.
- Quem tem qualquer um dos dois **mais uma conta Google**: duas famílias de graça em um
  minuto. É o caminho recomendado para leigo.
- O nome interno do provedor é `gemini-api`, para não colidir com o adaptador genérico
  `gemini` (agy) declarado em `runner/config/adapters.yaml`. Naquele arquivo, a detecção
  genérica olha o primeiro token do template (`python`), então `gemini` e `muse-spark`
  aparecem como "instalados" em qualquer máquina, e `plan_roles` pode escolher `gemini` como
  juiz automático de quem só tem Claude e não rodou o `setup`. Isso é da outra sessão e fica
  apontado, não corrigido aqui.
