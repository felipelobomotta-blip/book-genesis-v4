# ADR 0003 — Um CLI próprio: a pessoa escolhe o provedor, liga a própria chave, dá a ideia

**Status:** aceito em 02/09/2026 pelo autor (Felipe). Complementa o ADR 0002.
**Frase dele:** "o cara entra, configura tudo bonitinho e começa a usar, dá a ideia, literalmente
como funciona aqui ou no codex."

## 1. Contexto

O ADR 0002 fez o runner descobrir o que está instalado e cair no que existe. Isso resolve o caso de
quem já tem Claude Code ou Codex, mas decide pela pessoa, e deixa de fora quem tem só uma chave de
API (OpenRouter, DeepSeek, Anthropic, OpenAI, um servidor local). E o ponto de entrada ainda é
`python runner/cli.py ...`, não um programa.

## 2. Decisões

1. **A escolha é da pessoa; a detecção é o padrão.** `setup` grava o que ela escolheu em
   `~/.book-genesis/config.yaml`. Quando esse arquivo existe, ele vence `runner/config/models.yaml`.
   Quando não existe, vale o ADR 0002 (detecção e fallback). `doctor` só mostra o resultado.
2. **Provedores por API, sem dependências.** Dois adaptadores HTTP com a biblioteca padrão:
   `openai` (qualquer endpoint compatível com `/chat/completions`: OpenRouter, DeepSeek, OpenAI,
   Groq, Together, Ollama e LM Studio locais) e `anthropic` (`/v1/messages`). Um provedor é uma
   entrada `provider_<nome>` no config com `type`, `base_url` e a chave.
3. **A chave nunca aparece.** Ela vem de uma variável de ambiente (`api_key_env`) ou de
   `api_key` no config do usuário, lida por entrada oculta no `setup`. Nunca é impressa, nunca vai
   para o repositório, nunca entra em prompt. `doctor` diz "chave: definida" ou "faltando".
4. **`setup` é um assistente de terminal.** Pergunta como rodar os modelos principais (escritor,
   editor, arquiteto) e quem julga (juiz e painel), oferecendo os CLIs instalados, os provedores
   conhecidos com URL pré-preenchida, "outro compatível com OpenAI" e o modo manual. Sugere família
   diferente para o juiz. Pergunta os modelos com um padrão por provedor. Grava e mostra o resumo.
5. **`new` é o fluxo inteiro.** Pergunta a ideia, o idioma e a pasta; roda intake, fundação,
   arquitetura e o livro, com progresso na tela a cada passo (escritor, disruptor, juiz, editor) e
   um relatório no fim. `resume <pasta>` continua de onde parou. `book-genesis` sem argumentos
   abre `new` (ou `setup`, se ainda não houver config).
6. **Comando instalável.** `pyproject.toml` com o script `book-genesis` apontando para
   `runner.cli:main`; `pip install -e .` a partir do clone. Os templates continuam no clone.

## 3. Costuras sob teste

| costura | comportamento verificado |
|---|---|
| `OpenAICompatibleAdapter` / `AnthropicAdapter` com transporte falso | URL, cabeçalho de autenticação presente, corpo com modelo e mensagem; resposta extraída; erro HTTP vira `AdapterError` sem a chave no texto |
| `runner.userconfig` | config do usuário vence o padrão do repositório; provedor resolve chave por env ou arquivo; chave ausente é erro que diz o que fazer |
| `runner.setup.run_setup(ask, secret)` | respostas roteirizadas geram o config; a chave não aparece no resumo |
| `runner.cli new` com `--fake-responses` | pergunta ideia e idioma, cria o projeto, roda fases e capítulos, imprime progresso |
| `run_chapter(progress=...)` / `run_book(progress=...)` | cada passo e cada capítulo reportados na ordem |
| `pyproject.toml` | o comando `book-genesis` existe |

## 4. Fora do escopo

Empacotar os templates dentro da wheel (por ora o clone é obrigatório); interface gráfica;
faturamento; testes com leitores humanos.
