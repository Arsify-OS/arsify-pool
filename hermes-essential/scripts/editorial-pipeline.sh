#!/bin/bash
# HERMES EDITORIAL PIPELINE (LINKS + SENATOR DRAFTS VERSION)
# 1. Collect Links -> 2. Collect Senator Drafts -> 3. Fetch Content -> 4. Policy Brief -> 5. Notify Curator

LINKS_DIR="/root/.hermes/editorial-links"
DRAFTS_DIR="/root/.hermes/editorial-drafts"
COLLECTED_LINKS="/tmp/collected_links.txt"
AI_SCRIPT="/root/.hermes/skills/devops/hermes-editorial/scripts/editorial_ai.py"
PROCESSED_LINKS="$LINKS_DIR/processed"
PROCESSED_DRAFTS="$DRAFTS_DIR/processed"

# Create processed dirs if not exists
mkdir -p "$PROCESSED_LINKS" "$PROCESSED_DRAFTS"

# Step 1: Collect all links from senator files
echo "📰 [1/5] Collecting links from Senators..."
> $COLLECTED_LINKS

if [ -z "$(ls -A $LINKS_DIR/senator-*.txt 2>/dev/null)" ]; then
  echo "⚠️ No senator link files found in $LINKS_DIR"
  # Don't exit, maybe only drafts exist
else
  cat $LINKS_DIR/senator-*.txt 2>/dev/null | grep -E '^https?://' | sort -u > $COLLECTED_LINKS
  LINK_COUNT=$(wc -l < $COLLECTED_LINKS)
  echo "   Found $LINK_COUNT unique links"
fi

# Step 2: Check for senator drafts
echo "📝 [2/5] Checking for senator editorial drafts..."
DRAFT_COUNT=$(ls -1 $DRAFTS_DIR/senator-*-draft.md 2>/dev/null | wc -l)
if [ "$DRAFT_COUNT" -eq "0" ]; then
  echo "   ⚠️ No senator drafts found in $DRAFTS_DIR"
else
  echo "   Found $DRAFT_COUNT draft(s)"
fi

# Step 3: Process links + drafts with AI
echo "🧠 [3/5] Creating Policy Brief with LLM..."
python3 $AI_SCRIPT $COLLECTED_LINKS $DRAFTS_DIR

# Step 4: Move processed files to archive
echo "🗄️ [4/5] Archiving processed files..."
mv $LINKS_DIR/senator-*.txt $PROCESSED_LINKS/ 2>/dev/null
mv $DRAFTS_DIR/senator-*-draft.md $PROCESSED_DRAFTS/ 2>/dev/null

echo "✅ Pipeline complete! Policy Brief sent to Curator."
