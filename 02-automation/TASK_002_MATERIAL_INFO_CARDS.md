# TASK_002: Material Info Cards Implementation

**Started:** 2026-05-03 23:37 UTC  
**Status:** IN PROGRESS  
**Priority:** HIGH  
**Estimated Time:** 1-2 hours

---

## Objective

Add educational content to the game by implementing clickable material info cards that show:
- Real-world recycling facts
- Environmental impact data
- Processing information
- Recycling tips

---

## Implementation Plan

### Phase 1: Data Structure (15 min)
- [ ] Create EDUCATIONAL_FACTS object with data for all 6 raw materials
- [ ] Add facts for secondary materials (ingots, flakes, etc.)
- [ ] Include: realWorldFact, waterSaved, energySaved, recyclingTip

### Phase 2: Modal Component (20 min)
- [ ] Create showMaterialInfo(itemId) function
- [ ] Design modal layout with educational sections
- [ ] Add styling for edu-card, edu-fact, edu-impact, edu-tips

### Phase 3: Integration (15 min)
- [ ] Add onclick handlers to inventory items
- [ ] Add onclick handlers to SULAM/CIPTA recipe displays
- [ ] Test on MyShalter screen

### Phase 4: Testing (10 min)
- [ ] Test all 6 raw materials
- [ ] Test on mobile viewport
- [ ] Verify modal closes properly

---

## Educational Content Database

### Raw Materials

**organic_wet (🍃💧 Wet Organic)**
- Real-world fact: "Composting 1 ton of food waste prevents 50kg of methane emissions"
- Water saved: 0 liters (composting doesn't use water)
- Energy saved: 0.5 kWh per kg (avoided landfill transport)
- Recycling tip: "Separate food scraps from packaging. Keep meat/dairy separate from plant waste."

**organic_dry (🍂 Dry Organic)**
- Real-world fact: "Dry leaves and paper can be composted in 3-6 months, creating nutrient-rich soil"
- Water saved: 0 liters
- Energy saved: 1.2 kWh per kg (avoided incineration)
- Recycling tip: "Shred paper and cardboard before composting to speed up decomposition."

**plastic_hdpe (🧴 HDPE Plastic)**
- Real-world fact: "Recycling 1 ton of HDPE saves 5,774 kWh of energy - enough to power a home for 6 months"
- Water saved: 11,000 liters per ton
- Energy saved: 5.774 kWh per kg
- Recycling tip: "Look for #2 symbol. Rinse bottles before recycling. Caps can be recycled too!"

**plastic_ldpe (🛍️ LDPE Plastic)**
- Real-world fact: "LDPE bags can be recycled into composite lumber for outdoor furniture"
- Water saved: 9,500 liters per ton
- Energy saved: 4.2 kWh per kg
- Recycling tip: "Collect plastic bags in one bag. Many stores have drop-off bins for film plastics."

**metal_scrap (🔩 Metal Scrap)**
- Real-world fact: "Recycling aluminum saves 95% of the energy needed to make new aluminum from ore"
- Water saved: 40,000 liters per ton
- Energy saved: 14.0 kWh per kg
- Recycling tip: "Separate ferrous (magnetic) from non-ferrous metals. Remove non-metal attachments."

**glass_waste (🍾 Glass Waste)**
- Real-world fact: "Glass can be recycled infinitely without losing quality or purity"
- Water saved: 50 liters per ton
- Energy saved: 0.3 kWh per kg
- Recycling tip: "Separate by color (clear, green, brown). Remove caps and rinse containers."

---

## Code Implementation

### Step 1: Add Educational Facts Database

Insert after MASTER_ITEMS definition (around line 2627):

```javascript
// Educational facts database
const EDUCATIONAL_FACTS = {
  // Raw materials
  organic_wet: {
    realWorldFact: "Composting 1 ton of food waste prevents 50kg of methane emissions",
    waterSaved: 0,
    energySaved: 0.5,
    recyclingTip: "Separate food scraps from packaging. Keep meat/dairy separate from plant waste.",
    processingSteps: ["Collection", "Sorting", "Composting (3-6 months)", "Soil amendment"]
  },
  organic_dry: {
    realWorldFact: "Dry leaves and paper can be composted in 3-6 months, creating nutrient-rich soil",
    waterSaved: 0,
    energySaved: 1.2,
    recyclingTip: "Shred paper and cardboard before composting to speed up decomposition.",
    processingSteps: ["Collection", "Shredding", "Composting", "Mulch/Soil"]
  },
  plastic_hdpe: {
    realWorldFact: "Recycling 1 ton of HDPE saves 5,774 kWh of energy - enough to power a home for 6 months",
    waterSaved: 11000,
    energySaved: 5.774,
    recyclingTip: "Look for #2 symbol. Rinse bottles before recycling. Caps can be recycled too!",
    processingSteps: ["Collection", "Sorting", "Washing", "Shredding", "Melting", "Pelletizing", "New products"]
  },
  plastic_ldpe: {
    realWorldFact: "LDPE bags can be recycled into composite lumber for outdoor furniture",
    waterSaved: 9500,
    energySaved: 4.2,
    recyclingTip: "Collect plastic bags in one bag. Many stores have drop-off bins for film plastics.",
    processingSteps: ["Collection", "Sorting", "Cleaning", "Shredding", "Extrusion", "Composite products"]
  },
  metal_scrap: {
    realWorldFact: "Recycling aluminum saves 95% of the energy needed to make new aluminum from ore",
    waterSaved: 40000,
    energySaved: 14.0,
    recyclingTip: "Separate ferrous (magnetic) from non-ferrous metals. Remove non-metal attachments.",
    processingSteps: ["Collection", "Sorting (magnetic)", "Shredding", "Melting", "Casting", "New products"]
  },
  glass_waste: {
    realWorldFact: "Glass can be recycled infinitely without losing quality or purity",
    waterSaved: 50,
    energySaved: 0.3,
    recyclingTip: "Separate by color (clear, green, brown). Remove caps and rinse containers.",
    processingSteps: ["Collection", "Color sorting", "Crushing", "Melting (1500°C)", "Molding", "New containers"]
  },
  
  // Secondary materials
  compost: {
    realWorldFact: "Compost improves soil health, reducing need for chemical fertilizers by up to 50%",
    waterSaved: 0,
    energySaved: 0,
    recyclingTip: "Use compost in gardens, potted plants, or donate to community gardens.",
    processingSteps: ["Ready to use"]
  },
  plastic_flake: {
    realWorldFact: "Plastic flakes are the intermediate step - they can become bottles, clothing, or furniture",
    waterSaved: 0,
    energySaved: 0,
    recyclingTip: "This is industrial material - support products made from recycled plastic!",
    processingSteps: ["Pelletizing", "Manufacturing"]
  },
  metal_ingot: {
    realWorldFact: "Metal ingots can be remelted and reformed unlimited times without quality loss",
    waterSaved: 0,
    energySaved: 0,
    recyclingTip: "Recycled metal is used in cars, buildings, electronics, and packaging.",
    processingSteps: ["Alloying", "Casting", "Manufacturing"]
  },
  glass_cullet: {
    realWorldFact: "Using cullet (recycled glass) reduces furnace energy by 2-3% for every 10% cullet used",
    waterSaved: 0,
    energySaved: 0,
    recyclingTip: "Cullet melts at lower temperature than raw materials, saving energy.",
    processingSteps: ["Melting", "Forming", "New containers"]
  }
};
```

### Step 2: Create Modal Function

Insert after showModal() function (around line 1200):

```javascript
// Show educational material info card
function showMaterialInfo(itemId) {
  const item = MASTER_ITEMS[itemId];
  if (!item) return;
  
  const facts = EDUCATIONAL_FACTS[itemId];
  if (!facts) {
    showModal(`${item.icon} ${item.label}`, `<p>${item.desc}</p><p><em>Educational content coming soon!</em></p>`);
    return;
  }
  
  const processingStepsHTML = facts.processingSteps.map((step, i) => 
    `<span class="process-step">${i + 1}. ${step}</span>`
  ).join(' → ');
  
  const impactHTML = `
    <div class="edu-impact">
      <div class="impact-item">
        <span class="impact-icon">🌍</span>
        <span class="impact-label">CO₂ Impact:</span>
        <span class="impact-value">${item.co2_factor} kg saved per unit</span>
      </div>
      ${facts.energySaved > 0 ? `
      <div class="impact-item">
        <span class="impact-icon">⚡</span>
        <span class="impact-label">Energy Saved:</span>
        <span class="impact-value">${facts.energySaved} kWh per kg</span>
      </div>
      ` : ''}
      ${facts.waterSaved > 0 ? `
      <div class="impact-item">
        <span class="impact-icon">💧</span>
        <span class="impact-label">Water Saved:</span>
        <span class="impact-value">${facts.waterSaved.toLocaleString()} L per ton</span>
      </div>
      ` : ''}
    </div>
  `;
  
  const content = `
    <div class="edu-card">
      <p class="edu-desc">${item.desc}</p>
      
      <div class="edu-section">
        <div class="edu-section-title">💡 Did You Know?</div>
        <div class="edu-fact">${facts.realWorldFact}</div>
      </div>
      
      <div class="edu-section">
        <div class="edu-section-title">🌍 Environmental Impact</div>
        ${impactHTML}
      </div>
      
      <div class="edu-section">
        <div class="edu-section-title">♻️ Processing Steps</div>
        <div class="edu-process">${processingStepsHTML}</div>
      </div>
      
      <div class="edu-section">
        <div class="edu-section-title">💚 Recycling Tips</div>
        <div class="edu-tips">${facts.recyclingTip}</div>
      </div>
    </div>
  `;
  
  showModal(`${item.icon} ${item.label}`, content);
}
```

### Step 3: Add CSS Styling

Insert in <style> section (around line 400-500):

```css
/* Educational card styles */
.edu-card {
  text-align: left;
  font-size: 14px;
  line-height: 1.6;
}

.edu-desc {
  color: #666;
  margin-bottom: 20px;
  font-style: italic;
}

.edu-section {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #4CAF50;
}

.edu-section-title {
  font-weight: bold;
  font-size: 16px;
  margin-bottom: 10px;
  color: #2c5f2d;
}

.edu-fact {
  background: #fff3cd;
  padding: 12px;
  border-radius: 6px;
  border-left: 3px solid #ffc107;
  font-size: 15px;
  line-height: 1.5;
}

.edu-impact {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.impact-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: white;
  border-radius: 6px;
}

.impact-icon {
  font-size: 20px;
}

.impact-label {
  font-weight: 600;
  color: #555;
  min-width: 100px;
}

.impact-value {
  color: #4CAF50;
  font-weight: bold;
}

.edu-process {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  font-size: 13px;
  line-height: 2;
}

.process-step {
  background: white;
  padding: 6px 12px;
  border-radius: 20px;
  border: 2px solid #4CAF50;
  color: #2c5f2d;
  font-weight: 500;
}

.edu-tips {
  background: #d4edda;
  padding: 12px;
  border-radius: 6px;
  border-left: 3px solid #28a745;
  color: #155724;
  font-size: 14px;
}

/* Mobile responsive */
@media (max-width: 600px) {
  .edu-card {
    font-size: 13px;
  }
  
  .edu-section {
    padding: 12px;
  }
  
  .impact-label {
    min-width: 80px;
    font-size: 12px;
  }
  
  .process-step {
    font-size: 11px;
    padding: 4px 8px;
  }
}
```

### Step 4: Add Click Handlers to Inventory

Find the inventory rendering code (around line 4500-4600) and modify to add onclick:

```javascript
// In renderInventory() or similar function
// Change from:
html += `<div class="inv-item">${item.icon} ${item.label} x${qty}</div>`;

// To:
html += `<div class="inv-item" onclick="showMaterialInfo('${itemId}')" style="cursor:pointer;">
  ${item.icon} ${item.label} x${qty}
</div>`;
```

---

## Testing Checklist

- [ ] Click organic_wet in inventory → modal shows with compost facts
- [ ] Click plastic_hdpe → shows HDPE energy savings
- [ ] Click metal_scrap → shows 95% energy savings fact
- [ ] Modal displays properly on mobile (320px width)
- [ ] All 6 raw materials have complete data
- [ ] Modal close button works
- [ ] No console errors

---

## Next Steps After Completion

1. Add achievement: "Curious Learner" (read 5 material info cards)
2. Track which materials user has learned about
3. Add quiz questions for educational quests (TASK_004)
4. Expand to secondary/product materials

---

## Notes

- Keep facts accurate and sourced
- Use simple language (target: 12-year-old reading level)
- Focus on actionable tips users can apply in real life
- Avoid overwhelming with too much data
