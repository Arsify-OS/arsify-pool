# TASK_003: Impact Visualization Enhancement

**Started:** 2026-05-03 23:43 UTC  
**Status:** IN PROGRESS  
**Priority:** HIGH  
**Estimated Time:** 1 hour

---

## Objective

Enhance the impact screen to show real-world equivalents that users can relate to, making environmental impact more tangible and shareable.

---

## Implementation Plan

### Phase 1: Equivalents Calculator (15 min)
- [ ] Create calculateImpactEquivalents() function
- [ ] Add conversion formulas for:
  - Trees → Oxygen years for people
  - CO₂ → Car kilometers avoided
  - Plastic bottles → Fleece jackets
  - Metal → Aluminum cans recycled
  - Glass → Bottles saved from landfill

### Phase 2: Update Impact Screen UI (20 min)
- [ ] Find current impact screen rendering
- [ ] Add equivalents display section
- [ ] Design visual cards for each equivalent
- [ ] Add icons and formatting

### Phase 3: Share Impact Feature (15 min)
- [ ] Add "Share Impact" button
- [ ] Generate shareable text with equivalents
- [ ] Copy to clipboard functionality
- [ ] Show success message

### Phase 4: Testing (10 min)
- [ ] Test equivalents calculations
- [ ] Test share functionality
- [ ] Verify mobile display

---

## Real-World Equivalents Formulas

### Trees Planted
- 1 tree = 0.4 person-years of oxygen
- 1 tree = 21 kg CO₂ absorbed per year
- Formula: `oxygenYears = trees * 0.4`

### CO₂ Saved
- 1 kg CO₂ = 4 km of car driving
- 1 kg CO₂ = 0.25 kg of coal not burned
- Formula: `carKmAvoided = co2 * 4`

### Plastic Bottles
- 50 bottles = 1 fleece jacket
- 25 bottles = 1 square foot of carpet
- Formula: `fleeceJackets = Math.floor(bottles / 50)`

### Metal Recycled
- 1 kg aluminum = 40 cans
- Recycling 1 can saves enough energy to run TV for 3 hours
- Formula: `aluminumCans = metalKg * 40`

### Glass Recycled
- 1 kg glass = ~3 bottles
- Glass recycling saves 30% energy vs new glass
- Formula: `bottlesSaved = glassKg * 3`

---

## UI Design

### Impact Screen Layout

```
┌─────────────────────────────────────┐
│  🌍 Your Environmental Impact       │
├─────────────────────────────────────┤
│                                     │
│  🌳 Trees Planted: 2.5              │
│  → Oxygen for 1 person for 1 year  │
│                                     │
│  💨 CO₂ Saved: 15 kg                │
│  → 60 km of car driving avoided    │
│                                     │
│  🧴 Plastic Recycled: 120 bottles   │
│  → 2 fleece jackets made           │
│                                     │
│  ⚙️ Metal Recycled: 5 kg            │
│  → 200 aluminum cans recycled      │
│                                     │
│  🫙 Glass Recycled: 8 kg            │
│  → 24 bottles saved from landfill  │
│                                     │
├─────────────────────────────────────┤
│  [📤 Share Your Impact]             │
└─────────────────────────────────────┘
```

### Share Text Format

```
🌱 My Regrow Up World Impact:

🌳 Planted 2.5 trees = Oxygen for 1 person for 1 year
💨 Saved 15kg CO₂ = 60km of car driving avoided
🧴 Recycled 120 plastic bottles = 2 fleece jackets
⚙️ Recycled 5kg metal = 200 aluminum cans
🫙 Recycled 8kg glass = 24 bottles saved

Join me in making a difference! 🌍
Play: https://regrow.upshalter.com
```

---

## Code Implementation

### Step 1: Add Equivalents Calculator

Insert after EconomyManager class (around line 3500):

```javascript
// ══════════════════════════════════════════════════════════════════════════════
// IMPACT EQUIVALENTS CALCULATOR [TASK_003]
// ══════════════════════════════════════════════════════════════════════════════
function calculateImpactEquivalents(game) {
    const trees = game.collectionStats.totalMatches / CONFIG.MATCHES_PER_TREE;
    const co2 = window.economyManager ? window.economyManager.totalCO2Saved : 0;
    
    // Calculate material quantities
    const inv = window.economyManager ? window.economyManager.inventory : {};
    const plasticBottles = (inv.plastic_hdpe || 0) + (inv.plastic_ldpe || 0);
    const metalKg = (inv.metal_scrap || 0) * 0.5; // Assume 0.5kg per unit
    const glassKg = (inv.glass_waste || 0) * 0.3; // Assume 0.3kg per unit
    
    return {
        // Trees
        trees: trees.toFixed(1),
        oxygenYears: (trees * 0.4).toFixed(1),
        
        // CO₂
        co2Kg: co2.toFixed(1),
        carKmAvoided: Math.floor(co2 * 4),
        coalKgAvoided: (co2 * 0.25).toFixed(1),
        
        // Plastic
        plasticBottles: plasticBottles,
        fleeceJackets: Math.floor(plasticBottles / 50),
        carpetSqFt: Math.floor(plasticBottles / 25),
        
        // Metal
        metalKg: metalKg.toFixed(1),
        aluminumCans: Math.floor(metalKg * 40),
        tvHours: Math.floor(metalKg * 40 * 3), // 3 hours per can
        
        // Glass
        glassKg: glassKg.toFixed(1),
        bottlesSaved: Math.floor(glassKg * 3),
    };
}
```

### Step 2: Update Impact Screen Rendering

Find showImpactStats() function and enhance it:

```javascript
showImpactStats() {
    const equiv = calculateImpactEquivalents(this);
    
    this.showModal('🌍 Your Impact',
        `<div class="impact-stats">
            <div class="impact-section">
                <div class="impact-main">🌳 Trees Planted: ${equiv.trees}</div>
                <div class="impact-equiv">→ Oxygen for ${equiv.oxygenYears} person-years</div>
            </div>
            
            <div class="impact-section">
                <div class="impact-main">💨 CO₂ Saved: ${equiv.co2Kg} kg</div>
                <div class="impact-equiv">→ ${equiv.carKmAvoided} km of car driving avoided</div>
            </div>
            
            ${equiv.plasticBottles > 0 ? `
            <div class="impact-section">
                <div class="impact-main">🧴 Plastic Recycled: ${equiv.plasticBottles} bottles</div>
                <div class="impact-equiv">→ ${equiv.fleeceJackets} fleece jackets made</div>
            </div>
            ` : ''}
            
            ${equiv.aluminumCans > 0 ? `
            <div class="impact-section">
                <div class="impact-main">⚙️ Metal Recycled: ${equiv.metalKg} kg</div>
                <div class="impact-equiv">→ ${equiv.aluminumCans} aluminum cans recycled</div>
            </div>
            ` : ''}
            
            ${equiv.bottlesSaved > 0 ? `
            <div class="impact-section">
                <div class="impact-main">🫙 Glass Recycled: ${equiv.glassKg} kg</div>
                <div class="impact-equiv">→ ${equiv.bottlesSaved} bottles saved from landfill</div>
            </div>
            ` : ''}
            
            <div class="impact-share">
                <button class="btn-primary" onclick="game.shareImpact()">📤 Share Your Impact</button>
            </div>
        </div>`,
        () => {}, null
    );
}
```

### Step 3: Add Share Impact Function

```javascript
shareImpact() {
    const equiv = calculateImpactEquivalents(this);
    
    let shareText = '🌱 My Regrow Up World Impact:\n\n';
    shareText += `🌳 Planted ${equiv.trees} trees = Oxygen for ${equiv.oxygenYears} person-years\n`;
    shareText += `💨 Saved ${equiv.co2Kg}kg CO₂ = ${equiv.carKmAvoided}km of car driving avoided\n`;
    
    if (equiv.plasticBottles > 0) {
        shareText += `🧴 Recycled ${equiv.plasticBottles} plastic bottles = ${equiv.fleeceJackets} fleece jackets\n`;
    }
    if (equiv.aluminumCans > 0) {
        shareText += `⚙️ Recycled ${equiv.metalKg}kg metal = ${equiv.aluminumCans} aluminum cans\n`;
    }
    if (equiv.bottlesSaved > 0) {
        shareText += `🫙 Recycled ${equiv.glassKg}kg glass = ${equiv.bottlesSaved} bottles saved\n`;
    }
    
    shareText += '\nJoin me in making a difference! 🌍\n';
    shareText += 'Play: https://regrow.upshalter.com';
    
    // Copy to clipboard
    if (navigator.clipboard) {
        navigator.clipboard.writeText(shareText).then(() => {
            this.showModal('📋 Copied!', 'Paste it anywhere to spread the word. 🌱', () => {}, null);
        }).catch(() => {
            // Fallback for older browsers
            this._fallbackCopyToClipboard(shareText);
        });
    } else {
        this._fallbackCopyToClipboard(shareText);
    }
}

_fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.select();
    try {
        document.execCommand('copy');
        this.showModal('📋 Copied!', 'Paste it anywhere to spread the word. 🌱', () => {}, null);
    } catch (err) {
        this.showModal('❌ Copy Failed', 'Please copy manually: ' + text, () => {}, null);
    }
    document.body.removeChild(textArea);
}
```

### Step 4: Add CSS Styling

```css
/* ═══════════════════════════════════════════════════════════════════════════
   IMPACT STATS STYLES [TASK_003]
   ═══════════════════════════════════════════════════════════════════════════ */
.impact-stats {
    text-align: left;
    font-size: 14px;
}

.impact-section {
    margin-bottom: 20px;
    padding: 15px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    color: white;
}

.impact-main {
    font-size: 16px;
    font-weight: bold;
    margin-bottom: 8px;
}

.impact-equiv {
    font-size: 14px;
    opacity: 0.9;
    padding-left: 20px;
    font-style: italic;
}

.impact-share {
    margin-top: 20px;
    text-align: center;
}

.impact-share button {
    width: 100%;
    padding: 12px;
    font-size: 16px;
}

/* Mobile responsive */
@media (max-width: 600px) {
    .impact-section {
        padding: 12px;
    }
    
    .impact-main {
        font-size: 14px;
    }
    
    .impact-equiv {
        font-size: 12px;
    }
}
```

---

## Testing Checklist

- [ ] Trees calculation correct (matches / MATCHES_PER_TREE)
- [ ] CO₂ calculation pulls from economyManager
- [ ] Plastic bottles count = HDPE + LDPE
- [ ] Metal/glass calculations use correct weight assumptions
- [ ] Share button copies to clipboard
- [ ] Share text format is readable
- [ ] Modal displays properly on mobile
- [ ] All equivalents show correct units

---

## Success Metrics

- Users understand their impact better (qualitative)
- Share feature usage (track clipboard copy events)
- Increased engagement with impact screen
- Social media shares (if trackable)

---

## Next Steps After Completion

1. Add achievement: "Impact Champion" (share impact 5 times)
2. Add more equivalents (energy saved, water saved)
3. Add visual progress bars for each metric
4. Add comparison to average user
5. Add historical impact tracking (daily/weekly/monthly)

---

## Notes

- Keep equivalents simple and relatable
- Use round numbers when possible
- Avoid overwhelming with too many metrics
- Focus on positive framing ("saved" not "prevented")
