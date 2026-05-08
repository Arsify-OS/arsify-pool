---
name: rapid-feature-iteration
description: Use when implementing multiple small features rapidly with task docs, progress tracking, and continuous deployment.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [rapid-development, iteration, documentation, deployment, task-tracking]
    related_skills: [writing-plans, test-driven-development, requesting-code-review]
---

# Rapid Feature Iteration

## Overview

Implement multiple small features in rapid succession (3-10 minutes each) with comprehensive task documentation, progress tracking, and continuous deployment. This workflow prioritizes velocity while maintaining quality through structured documentation and immediate deployment validation.

**Key characteristics:**
- Small, focused features (not large multi-day projects)
- Task documentation written DURING implementation (not before)
- Continuous deployment after each feature
- Progress tracking with summaries
- Velocity measurement and reporting

**Not the same as:** Traditional planning (writing-plans) which creates detailed specs before implementation. This skill is for implementing features rapidly while documenting as you go.

## When to Use

**Use when:**
- Implementing 3+ related features in one session
- Features are small enough to complete in 3-10 minutes each
- Continuous deployment is available (auto-deploy, file watcher)
- User wants progress tracking and summaries
- Working on educational content, UI enhancements, or incremental improvements

**Don't use when:**
- Single large feature requiring detailed upfront planning
- Complex architecture changes needing design review
- Features with unclear requirements (plan first)
- No deployment mechanism available

## Workflow Structure

### Phase 1: Analysis (if needed)
- Understand existing codebase
- Identify integration points
- Document architecture
- Create task list

### Phase 2: Rapid Implementation Loop

For each feature:

1. **Create Task Document** (1 min)
   - Objective, scope, estimated time
   - Implementation plan (phases)
   - Code locations and changes
   - Testing checklist

2. **Implement Feature** (3-8 min)
   - Make focused changes
   - Add code incrementally
   - Use patch operations for surgical edits
   - Verify syntax as you go

3. **Deploy Immediately** (30 sec)
   - Run deployment script
   - Verify deployment success
   - Note file size changes

4. **Document Completion** (1 min)
   - Create completion summary
   - Record actual time taken
   - Note code changes (+lines, file size)
   - Update progress log

5. **Move to Next Feature**

### Phase 3: Phase Summary

After completing 3-4 features:
- Create phase completion document
- Calculate velocity metrics
- Provide testing checklist
- Recommend next steps

## Task Document Template

```markdown
# TASK_NNN: [Feature Name]

**Started:** YYYY-MM-DD HH:MM UTC  
**Status:** IN PROGRESS  
**Priority:** HIGH/MEDIUM/LOW  
**Estimated Time:** X minutes/hours

---

## Objective

[One paragraph describing what this builds and why]

---

## Implementation Plan

### Phase 1: [Component Name] (X min)
- [ ] Specific action
- [ ] Specific action
- [ ] Specific action

### Phase 2: [Component Name] (X min)
- [ ] Specific action
- [ ] Specific action

### Phase 3: Testing (X min)
- [ ] Test case
- [ ] Test case

---

## Code Implementation

### Step 1: [Action]

[Code block or description]

### Step 2: [Action]

[Code block or description]

---

## Testing Checklist

- [ ] Test case 1
- [ ] Test case 2
- [ ] Mobile responsive
- [ ] No console errors

---

## Success Metrics

- Quantitative metric
- Qualitative metric

---

## Next Steps After Completion

1. Optional enhancement
2. Related feature
3. Future improvement
```

## Completion Summary Template

```markdown
# TASK_NNN: [Feature Name] - COMPLETE ✅

**Started:** YYYY-MM-DD HH:MM UTC  
**Completed:** YYYY-MM-DD HH:MM UTC  
**Duration:** X minutes  
**Status:** SUCCESS

---

## What Was Built

✅ Component 1
   - Detail
   - Detail

✅ Component 2
   - Detail
   - Detail

✅ Code Implementation
   - Function name (X lines)
   - Function name (X lines)
   - CSS styling (X lines)
   - Total: +XXX lines of code

---

## Deployment

✅ Deployed to: [URL]
✅ File size: XXX KB (XXXX lines)
✅ No breaking changes
✅ Auto-deploy active

---

## Testing Checklist

Manual testing needed:
[ ] Test case 1
[ ] Test case 2
[ ] Test case 3

---

## Next Steps

TASK_NNN+1: [Next Feature] (X time)
- Scope item
- Scope item
```

## Progress Log Updates

After each task, update a central progress log:

```markdown
### YYYY-MM-DD HH:MM - TASK_NNN Started
**Objective:** [Brief description]

### YYYY-MM-DD HH:MM - TASK_NNN Complete ✅
**Duration:** X minutes  
**Changes:**
- Change summary
- Code added: +XXX lines
- File size: XXX KB → YYY KB
- Deployed to production
```

## Phase Summary Template

After completing 3-4 tasks:

```markdown
# PHASE N COMPLETE ✅

**Total Duration:** XX minutes (Tasks N-M)
**Summary:**
- TASK_N: [Name] (X min) - +XXX lines
- TASK_N+1: [Name] (X min) - +XXX lines
- TASK_N+2: [Name] (X min) - +XXX lines
- Total code added: +XXX lines
- File size: XXX KB → YYY KB (+X%)
- All features deployed and live

---

## Velocity Analysis

Task Breakdown:
- TASK_N: X min (+XXX lines) = XX lines/min
- TASK_N+1: X min (+XXX lines) = XX lines/min
- TASK_N+2: X min (+XXX lines) = XX lines/min

Average: X.X min/task
Total: XX min for complete Phase N

Efficiency vs Estimates:
- TASK_N: Estimated X hours → Actual X min (XXx faster)
- TASK_N+1: Estimated X hours → Actual X min (XXx faster)

---

## Testing Checklist

[ ] Test feature 1
[ ] Test feature 2
[ ] Test feature 3
[ ] Mobile responsive
[ ] No breaking changes

---

## Recommendation

[Next action: continue to next phase, user testing, or polish]
```

## Velocity Tracking

Track and report these metrics:

**Per Task:**
- Estimated time vs actual time
- Lines of code added
- Code rate (lines/min)
- File size change

**Per Phase:**
- Total tasks completed
- Total time spent
- Average time per task
- Total lines added
- Efficiency vs estimates (Xx faster)

**Report format:**
```
Velocity: 4 tasks in 18 minutes = 4.5 min/task average
Code rate: 31 lines/min average
Efficiency: 10-30x faster than estimated
```

## Deployment Integration

After each feature:

```bash
# Run deployment script
bash deploy.sh

# Verify success
# Note timestamp and file size
```

**Document in completion summary:**
```markdown
✅ Deployed to: https://example.com
✅ File size: 354 KB (7069 lines)
✅ Deployment time: YYYY-MM-DD HH:MM UTC
```

## Common Patterns

### Pattern 1: Educational Content Addition

**Sequence:**
1. Create data structure (facts, tips, dialogues)
2. Create display function (modal, cards, bubbles)
3. Add CSS styling
4. Add trigger points (onclick, events)
5. Deploy and test

**Time:** 3-5 minutes per feature

### Pattern 2: UI Enhancement

**Sequence:**
1. Create calculation/data function
2. Update display function with new UI
3. Add CSS styling
4. Add user interaction (buttons, share)
5. Deploy and test

**Time:** 3-4 minutes per feature

### Pattern 3: Contextual Triggers

**Sequence:**
1. Expand data structure (dialogues, messages)
2. Create helper function
3. Add trigger points in existing functions
4. Deploy and test

**Time:** 3 minutes per feature

## File Organization

Create these files during the session:

```
project-root/
├── TASK_001_[NAME].md          # Task document
├── TASK_001_COMPLETE.md        # Completion summary
├── TASK_001_SUMMARY.txt        # Terminal-friendly summary
├── TASK_002_[NAME].md
├── TASK_002_COMPLETE.md
├── TASK_002_SUMMARY.txt
├── ...
├── PHASE_N_COMPLETE.txt        # Phase summary
├── QUICK_SUMMARY.txt           # Quick reference
└── progress_log.md             # Central progress log
```

## Communication Style

**During implementation:**
- Brief status updates ("Bagus! Sekarang saya...")
- Show progress ("Sempurna! Deployment berhasil.")
- Minimal explanation (code speaks for itself)

**In summaries:**
- Structured with clear sections
- Metrics and statistics
- Testing checklists
- Next steps recommendations

**Terminal output:**
- Plain text, no markdown
- Box drawing characters for structure
- Emoji for status (✅ ⏳ ❌)
- Concise and scannable

## Common Pitfalls

1. **Writing detailed plans before starting**
   - Pitfall: Spending 30 minutes planning a 5-minute feature
   - Fix: Write task doc as you implement, not before

2. **Skipping deployment after each feature**
   - Pitfall: Accumulating changes, harder to debug
   - Fix: Deploy immediately after each feature

3. **Not tracking velocity**
   - Pitfall: No sense of progress or efficiency
   - Fix: Record time and lines for every task

4. **Verbose explanations during implementation**
   - Pitfall: Slows down flow, user just wants results
   - Fix: Brief status updates, detailed docs in summaries

5. **Missing completion summaries**
   - Pitfall: Hard to review what was accomplished
   - Fix: Create summary immediately after each task

6. **Not updating progress log**
   - Pitfall: Lose track of session timeline
   - Fix: Update progress log after every task completion

7. **Forgetting phase summaries**
   - Pitfall: No big-picture view of accomplishments
   - Fix: Create phase summary after 3-4 tasks

## Verification Checklist

After each task:
- [ ] Task document created with clear objective
- [ ] Feature implemented and code added
- [ ] Deployment successful
- [ ] Completion summary created with metrics
- [ ] Progress log updated
- [ ] Next task identified

After each phase:
- [ ] Phase summary created
- [ ] Velocity metrics calculated
- [ ] Testing checklist provided
- [ ] Recommendation for next action

## Example Session Flow

```
23:33 - TASK_001 Started (Analysis)
23:41 - TASK_001 Complete (8 min, 52KB docs)

23:37 - TASK_002 Started (Material Info Cards)
23:41 - TASK_002 Complete (4 min, +273 lines)
        Deployed to production

23:43 - TASK_003 Started (Impact Visualization)
23:46 - TASK_003 Complete (3 min, +185 lines)
        Deployed to production

23:47 - TASK_004 Started (Educational Dialogues)
23:50 - TASK_004 Complete (3 min, +100 lines)
        Deployed to production

23:51 - PHASE 1 COMPLETE
        Total: 18 minutes, 4 tasks, +558 lines
        Velocity: 4.5 min/task, 31 lines/min
        Efficiency: 10-30x faster than estimated
```

**Full session details:** See `references/regrow-up-world-session.md` for complete breakdown including code patterns, communication style, and reusable techniques.

## Success Metrics

**Quantitative:**
- Tasks completed per session
- Average time per task
- Lines of code per minute
- Efficiency vs estimates
- Deployment success rate

**Qualitative:**
- Clear documentation trail
- User can review progress easily
- Features work on first deployment
- No breaking changes
- Smooth handoff for testing

## Remember

```
Small features (3-10 min each)
Document as you go (not before)
Deploy immediately after each
Track velocity and metrics
Create summaries for review
Keep communication brief during work
Detailed docs in summaries
```

**Rapid iteration = velocity + quality through structure.**
