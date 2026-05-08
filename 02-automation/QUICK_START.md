# Phase 2 Quick Start Guide

**For:** Development Team  
**Date:** 2026-05-04  
**Version:** 1.0

---

## 🚀 Getting Started

### 1. Environment Setup
```bash
cd /workspace
# Verify game file exists
ls -la Upshalter-Odyssey-RegrowUp.html
# Should show: 348K file
```

### 2. Branch Strategy
```bash
# Create development branch
git checkout -b develop

# Create feature branches
git checkout -b feature/phase2-combo-system
git checkout -b feature/phase2-gotchi-feeding
git checkout -b feature/phase2-new-materials
```

### 3. Development Workflow
```bash
# Start development server (if needed)
python3 -m http.server 8080
# Access at http://localhost:8080

# Test changes
# Open in browser: http://localhost:8080/Upshalter-Odyssey-RegrowUp.html

# Check for errors
# Open DevTools → Console tab
```

---

## 📋 Sprint 1 Tasks (Current Focus)

### Priority Order
1. **Combo Detection System** (12 hours)
2. **Gotchi Feeding** (18 hours)
3. **New Materials** (14 hours)

### Quick Reference

#### Combo System Files to Modify
- **Main Logic:** Line ~5500 in Game class
- **Add Methods:**
  - `_detectCombos(matchGroups)`
  - `_processCombos(combos)`
  - `_showComboEffect(combo)`

#### Feeding System Files to Modify
- **New Class:** Add FeedingManager class
- **Integration:** Game constructor (line ~4700)
- **UI:** Add modal HTML in initUI()

#### New Materials Files to Modify
- **MASTER_ITEMS:** Line ~1800
- **EDUCATIONAL_FACTS:** Line ~2500
- **ASMRSoundEngine:** Line ~2044

---

## 🎯 Key Code Locations

| Feature | File Location | Lines |
|---------|--------------|-------|
| Game Class | Upshalter-Odyssey-RegrowUp.html | ~4700 |
| EconomyManager | Upshalter-Odyssey-RegrowUp.html | 2997 |
| ASMRSoundEngine | Upshalter-Odyssey-RegrowUp.html | 2044 |
| Material Info | Upshalter-Odyssey-RegrowUp.html | 5164 |
| Impact Viz | Upshalter-Odyssey-RegrowUp.html | 5045 |
| Educational Dialogues | Upshalter-Odyssey-RegrowUp.html | 4940 |

---

## 🛠️ Common Tasks

### Add New Sound Effect
```javascript
// In ASMRSoundEngine class
playNewMaterialTap(volume = 0.5) {
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    
    // Add your sound generation here
    const osc = this._node('sine', 440);
    const gain = this._gain(0);
    gain.gain.setValueAtTime(volume, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.3);
    
    osc.connect(gain);
    gain.connect(this.masterGain);
    osc.start(t); osc.stop(t + 0.3);
}
```

### Add New Material Type
```javascript
// In MASTER_ITEMS (around line 1800)
MASTER_ITEMS['newtype'] = {
    id: 'newtype',
    label: 'New Type',
    icon: '📦',
    type: 'newtype',
    desc: 'Description here',
    co2_factor: 2.5,
    rarity: 'common'
};
```

### Add Educational Fact
```javascript
// In EDUCATIONAL_FACTS (around line 2500)
EDUCATIONAL_FACTS.newtype = {
    processingSteps: ['Step 1', 'Step 2'],
    energySaved: 50,
    waterSaved: 1000,
    funFact: 'Interesting fact!'
};
```

---

## 🧪 Testing Checklist

### Before Each Commit
- [ ] No console errors
- [ ] Sound works on click
- [ ] Touch works on mobile
- [ ] State persists after refresh
- [ ] No memory leaks (check DevTools → Memory)

### Feature-Specific Tests

**Combo System:**
- [ ] Bomb + Rainbow triggers combo
- [ ] Score bonus calculated correctly
- [ ] Visual effect appears
- [ ] Sound plays

**Feeding System:**
- [ ] Modal opens correctly
- [ ] Food selection works
- [ ] Hunger restores
- [ ] Mood changes
- [ ] State saves

**New Materials:**
- [ ] Material appears in grid
- [ ] Matches work correctly
- [ ] Educational facts display
- [ ] Sound plays on tap

---

## 📊 Progress Tracking

### Daily Standup Questions
1. What did you complete yesterday?
2. What are you working on today?
3. Any blockers?

### Weekly Demo Checklist
- [ ] Feature works end-to-end
- [ ] No critical bugs
- [ ] Mobile tested
- [ ] Performance acceptable

---

## 🎨 Design Resources

### Color Palette
- **Primary Green:** #7ec87a
- **Organic Green:** #8ac926
- **Recyclable Blue:** #4fc3f7
- **Special Yellow:** #ffd54f
- **Grime Brown:** #8d6e63

### Gotchi Evolution Stages
1. Seedling → Sprout → Sapling → Robot-Tree → Guardian

### Sound Themes
- **Organic:** Wet, earthy, alive (brown/pink noise)
- **Recyclable:** Crisp, hollow, dry (white noise)
- **Special:** Bright, resonant, magical (sine waves)
- **Grime:** Dull, heavy, reluctant (brown noise)

---

## 📚 Documentation

| Document | Purpose | Location |
|----------|---------|----------|
| Phase 2 Analysis | Overview & roadmap | PHASE2_ANALYSIS.md |
| Implementation Spec | Technical details | PHASE2_IMPLEMENTATION_SPEC.md |
| Sprint 1 Tasks | Task breakdown | SPRINT1_TASKS.md |
| This Guide | Quick reference | QUICK_START.md |

---

## 🆘 Troubleshooting

### Common Issues

**Issue:** Game not loading
- **Fix:** Check file path, verify no syntax errors

**Issue:** Sound not working
- **Fix:** Check AudioContext, verify user interaction first

**Issue:** State not persisting
- **Fix:** Check localStorage, verify save/load methods

**Issue:** Touch not working
- **Fix:** Verify event listeners, check mobile CSS

---

## 📞 Support

**Project:** Regrow Up World  
**Live URL:** https://regrow.upsalter.com  
**Workspace:** /workspace  
**Main File:** Upshalter-Odyssey-RegrowUp.html  

**Documentation:** See PHASE2_ANALYSIS.md for full details

---

**Quick Start Complete!**  
Start with Sprint 1 Task 1.1: Combo Detection System
