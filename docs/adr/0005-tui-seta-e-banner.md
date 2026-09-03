# ADR 0005 — Menu com seta, banner, passo a passo explicado

**Status:** aceito em 03/09/2026 pelo autor (Felipe). Refina o `setup` do ADR 0004.
**Pedido dele:** "quero algo totalmente bonito, bem feito, fácil e profissional... seta pra
cima, seta pra baixo, tudo bonitinho... que nem quando a gente instala o openclaw."

## 1. Decisão

`book-genesis setup` ganha três coisas, só com biblioteca padrão (sem dependência nova):

1. **Banner** — caixa ASCII com o nome do produto, no início do assistente.
2. **Explicação em linguagem simples** — antes de qualquer pergunta, três linhas dizendo o
   que é "escritor" e "juiz" e por que família diferente é mais forte.
3. **Menu com seta** — `runner/tui.py`: `Up`/`Down` move, `Enter` confirma, dígito pula direto
   pro item, `Ctrl+C`/`Esc` cancela. Implementado com `msvcrt` (Windows) e `termios`/`tty`
   (resto), ambos da biblioteca padrão.

## 2. Por que ASCII puro, não caixa Unicode

Tentativa inicial usou `╭─╮│╰─╯`. Travou com `UnicodeEncodeError: 'charmap' codec can't
encode` — o console desta máquina abre com `cp1252` e não tem esses glifos na tabela. A cor
ANSI (`\x1b[36m` etc.) não corre esse risco: são só bytes ASCII, o terminal que decide como
colorir. Banner e marcadores (`>`, `*`) viraram ASCII puro; a cor carrega o "bonito".

## 3. Por que a lógica antiga não quebrou

`run_setup` ganhou um parâmetro `choose` opcional. Sem ele, cai em `text_choose(ask, say)` —
exatamente o comportamento de digitar um número que já existia, byte a byte. Os 135 testes
que já existiam nunca precisaram mudar: nenhum toca terminal de verdade, todos usam
`text_choose` por trás. `interactive_choose` (o seletor de seta de verdade) só entra quando
`runner/cli.py` detecta `stdin` e `stdout` como terminal real (`supports_interactive()`) —
nunca é o caminho em teste automatizado, CI, ou quando a entrada vem de um pipe.

## 4. O que ficou provado e o que não

Provado por teste: a matemática de navegação (`apply_key` — sobe, desce, dá a volta nas
pontas, pulo por dígito) e o formato do banner (largura igual em toda linha, nome presente).
Provado rodando o caminho real: nenhum crash, banner e explicação aparecem certos, detecção
de Claude/Codex funciona, sem processo nem arquivo esquecido depois do teste.

**Não provado por mim:** a sensação real de apertar seta no terminal, e a cor de verdade.
As ferramentas desta sessão não têm um terminal de verdade (`isatty` dá falso nos dois
lados), então esse caminho nunca roda por aqui — só quando o Felipe roda `book-genesis setup`
no terminal dele mesmo.

## 5. Reversão

Tudo no branch `arch/runner-orchestrates`, commit próprio. Reverter devolve o menu por
número, sem banner.
