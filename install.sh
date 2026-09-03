#!/usr/bin/env bash
set -euo pipefail

# Book Genesis installer for macOS/Linux.
# Installs full skill folders, including supporting references, to ~/.claude/.

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$REPO_DIR/skills"
KNOWLEDGE_DIR="$REPO_DIR/knowledge"
AGENTS_DIR="$REPO_DIR/agents"
TARGET_SKILLS="$HOME/.claude/skills"
TARGET_KNOWLEDGE="$HOME/.claude/knowledge"
TARGET_AGENTS="$HOME/.claude/agents"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo -e "${BLUE}Book Genesis${NC}"
echo -e "${YELLOW}Copies the agent templates and knowledge base to ~/.claude (optional: the runner reads them from this clone)${NC}"
echo ""
echo -e "${YELLOW}Installing skills, supporting references, agents, and knowledge base${NC}"
echo ""

if [ ! -d "$SKILLS_DIR" ]; then
  echo -e "${RED}Error: skills/ directory not found. Run this script from the repository root.${NC}"
  exit 1
fi

mkdir -p "$TARGET_SKILLS" "$TARGET_KNOWLEDGE" "$TARGET_AGENTS"

# Skills live at skills/<name>/ AND in grouping folders like skills/optional/<name>/.
# Discover SKILL.md at any depth so nested groups are not silently skipped.
# skills/deprecated/ is intentionally excluded — those are superseded by agents/.
count=0
while IFS= read -r skill_file; do
  skill_dir=$(dirname "$skill_file")
  skill_name=$(basename "$skill_dir")
  case "$skill_dir" in
    */deprecated/*) continue ;;
  esac
  rm -rf "$TARGET_SKILLS/$skill_name"
  mkdir -p "$TARGET_SKILLS/$skill_name"
  cp -R "$skill_dir/." "$TARGET_SKILLS/$skill_name/"
  echo -e "  ${GREEN}+${NC} $skill_name"
  count=$((count + 1))
done < <(find "$SKILLS_DIR" -maxdepth 3 -name SKILL.md -type f | sort)

kb_count=0
if [ -d "$KNOWLEDGE_DIR" ]; then
  for kb_file in "$KNOWLEDGE_DIR"/*.md; do
    if [ -f "$kb_file" ]; then
      cp "$kb_file" "$TARGET_KNOWLEDGE/"
      echo -e "  ${GREEN}+${NC} knowledge/$(basename "$kb_file")"
      kb_count=$((kb_count + 1))
    fi
  done
fi

agent_count=0
if [ -d "$AGENTS_DIR" ]; then
  for agent_file in "$AGENTS_DIR"/*.md; do
    if [ -f "$agent_file" ]; then
      cp "$agent_file" "$TARGET_AGENTS/"
      echo -e "  ${GREEN}+${NC} agent/$(basename "$agent_file")"
      agent_count=$((agent_count + 1))
    fi
  done
fi

# Verify every template the runner reads is present (runner/chapter.py, runner/phases.py).
# A missing one fails the runner closed, so fail loudly here instead.
PIPELINE_AGENTS="book-researcher book-architect entity-tracker continuity-guardian book-writer book-disruptor book-judge book-evaluator book-editor book-packager"
missing=""
for agent in $PIPELINE_AGENTS; do
  if [ ! -f "$TARGET_AGENTS/$agent.md" ]; then
    missing="$missing $agent"
  fi
done

echo ""
if [ -n "$missing" ]; then
  echo -e "${RED}Pipeline incomplete.${NC} Templates the runner needs are not installed:"
  for agent in $missing; do
    echo -e "  ${RED}-${NC} $agent"
  done
  echo ""
  echo "The runner fails closed when it reaches one of these."
  exit 1
fi
echo -e "${GREEN}Pipeline verified.${NC} All 10 runner templates resolve."

echo ""
echo -e "${GREEN}Done.${NC} $count skills + $agent_count agents + $kb_count knowledge files installed"
echo ""
echo -e "Skills:    ${BLUE}$TARGET_SKILLS${NC}"
echo -e "Agents:    ${BLUE}$TARGET_AGENTS${NC}"
echo -e "Knowledge: ${BLUE}$TARGET_KNOWLEDGE${NC}"
echo ""
echo "Start a book from this folder:  python runner/cli.py init my-book --idea \"...\" --language en"
echo "Then:  run-phase (x3), book, approve, book.  Details: docs/runner.md"
echo ""
