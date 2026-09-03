# ADR 0004 — Onboarding no padrão de OpenClaw, Hermes e opencode

**Status:** aceito em 03/09/2026 pelo autor (Felipe). Revisa a decisão 4 do ADR 0003.
**Pedido dele:** "veja como o pessoal faz quando instala o openclaw cli ou hermes e tome como base."
"Seria legal principalmente na hora de escolher modelos, conectar por oauth, conectar apis."

## 1. O que os três fazem igual

Olhei a documentação de onboarding do OpenClaw e do opencode, e o `hermes setup`, `hermes doctor`
e `hermes model` instalados nesta máquina. O padrão comum, que o nosso `setup` de texto livre
não tinha:

1. **Detecta antes de perguntar.** Uma passada só de leitura: CLIs instalados, variáveis de
   ambiente com chave, servidores locais que respondem (Ollama, LM Studio).
2. **Oferece um caminho de uma tecla.** "Quick start" reaproveita o que foi detectado.
3. **Prova com uma chamada real antes de salvar.** OpenClaw "testa os candidatos com
   completions reais até um funcionar"; uma configuração que nunca foi chamada é um chute.
4. **Menu numerado**, com os provedores mais comuns primeiro e "outro" no fim.
5. **Modelos vêm da lista viva do provedor** (`hermes model --refresh` busca `/v1/models`).
6. **OAuth de assinatura é delegado ao CLI da própria empresa.** OpenClaw usa o login do
   Codex para a assinatura da OpenAI; ninguém reimplementa o OAuth da Anthropic ou da OpenAI.
7. **Re-executar não apaga nada.** Com config existente: manter, mudar ou resetar; a
   re-execução vira uma passada de verificação.

## 2. Decisões

1. `book-genesis setup` segue exatamente os sete pontos acima (`runner/onboarding.py`,
   `runner/setup.py`).
2. OAuth aparece no menu como "Claude subscription (OAuth through the Claude Code CLI)" e
   "ChatGPT / Codex subscription (OAuth through the Codex CLI)". Se o CLI não está instalado,
   o assistente diz como instalar e logar; ele não finge fazer o OAuth.
3. Chaves de API continuam entrando por entrada oculta ou variável de ambiente (ADR 0003).
4. A verificação real é obrigatória no caminho normal; falhou, nada é salvo, e a mensagem
   diz o motivo sem a chave. Só o modo manual pula a verificação.
5. `doctor` continua sendo diagnóstico, e passa a existir `--live` no futuro se for útil; hoje
   a chamada real fica no `setup`.

## 3. Costuras sob teste

`detect_environment` (CLIs, chaves, servidores, ordem), `quick_plan` (duas famílias separam
escrita e julgamento; uma família avisa), `verify_candidate` (ok, falha sem chave, vazio),
`list_models` (OpenAI-compatível e Anthropic, falhas viram lista vazia), e `run_setup` com IO
roteirizado: quick start de uma tecla que verifica antes de salvar; verificação falhando não
salva; custom por número com chave oculta; modelos em lista numerada; lista fixa para o
Claude Code com ajuda de OAuth quando ausente; re-execução com manter/mudar/resetar.

## 4. Fontes

- OpenClaw, Onboarding (CLI): https://docs.openclaw.ai/start/wizard
- OpenClaw, CLI setup reference: https://docs.openclaw.ai/start/wizard-cli-reference
- opencode docs (`/connect`, provedores, TUI): https://opencode.ai/docs/
- `hermes setup --help`, `hermes doctor --help`, `hermes model --help` na máquina do autor.
