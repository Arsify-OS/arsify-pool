---
name: research-paper-arxiv-workflow
description: Workflow for creating multi-agent orchestration research papers with arXiv reference integration
---

# Research Paper Workflow with arXiv Integration

Extends the core scientific paper methodology for multi-agent orchestration systems, adding steps to integrate arXiv references into the paper's Related Work and References sections.

## Prerequisites
- `multi-agent-orchestration` skill loaded
- `arxiv` skill loaded
- Phase 0-2 data collected (see `references/phase0-implementation.md`, `references/phase1-implementation.md`, `references/phase2-implementation.md`)

## Steps

### 1. Collect Phase Data
Gather all phase-specific data and reports:
```bash
mkdir -p /root/multi-agent-orchestration-paper/{data,references,figures}
cp -r /usr/local/lib/hermes-shared-memory/experimental-data/* /root/multi-agent-orchestration-paper/data/
cp /usr/local/lib/hermes-shared-memory/SCIENTIFIC_PAPER.txt /root/multi-agent-orchestration-paper/references/Phase0_Paper.txt
cp /usr/local/lib/hermes-orchestrator/FASE2_COMPLETE.md /root/multi-agent-orchestration-paper/references/Phase2_Report.md
```

### 2. Search arXiv for References
Use the `arxiv` skill to find relevant papers:
```bash
# Search for multi-agent orchestration, shared memory, task routing
curl -s "https://export.arxiv.org/api/query?search_query=all:multi-agent+orchestration+shared+memory&max_results=5&sortBy=relevance" | python3 -c "
import sys, xml.etree.ElementTree as ET
ns = {'a': 'http://www.w3.org/2005/Atom'}
root = ET.parse(sys.stdin).getroot()
for i, entry in enumerate(root.findall('a:entry', ns)):
    title = entry.find('a:title', ns).text.strip().replace('\n', ' ')
    arxiv_id = entry.find('a:id', ns).text.strip().split('/abs/')[-1]
    authors = ', '.join(a.find('a:name', ns).text for a in entry.findall('a:author', ns))
    print(f'[{arxiv_id}] {title} | Authors: {authors}')
"
```

If curl is blocked, use `execute_code` with the terminal tool as a workaround.

### 3. Create Initial Paper
Draft the paper with 10 sections (Abstract, Introduction, Related Work, Architecture, Layers 1-3, Evaluation, Discussion, Conclusion, References) using `references/scientific-paper-methodology.md` as a guide.

### 4. Patch Paper with New References
Add new arXiv references to the Related Work section and References section using the `patch` tool:
- Update Related Work citations (e.g., add [11] to Section 2.1)
- Add new reference entries to Section 10 (References)
- Update paper statistics (e.g., Reference count from 10 to 19)

### 5. Validate
- Verify all citations in Related Work map to References section
- Check that arXiv IDs are correct and PDF links are valid
- Update README.md with new reference count

## Example Patch
To add a new reference [11] to Section 2.1:
```patch
### 2.1 Multi-Agent Memory Systems
Traditional multi-agent systems (MAS) employ localized memory models where each agent maintains private state [1]. Recent work by [2, 17, 18] introduced shared memory pools and knowledge graph constructions, but focused primarily on read-only knowledge bases without real-time synchronization. Our approach extends this by implementing read-write shared knowledge with access tracking, statistical validation, and integration with real-time event coordination.
```

## Deliverables
- `paper.md`: Complete research paper (~3,500 words)
- `README.md`: Folder structure and statistics
- `data/`: Experimental data from Phases 0-2
- `references/`: Phase reports and arXiv reference list
