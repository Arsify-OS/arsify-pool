# Regrow Up World - Integration Points for Circular Economy Mechanics

**Analysis Date:** 2026-05-03  
**Target:** Identify where to inject new circular economy features without breaking existing gameplay

---

## 1. Material Lifecycle Chain Integration Points

### Current State
Game already has a 3-tier economy system (v6.4-6.5):
- **Tier 1 (Raw):** 6 material types collected from match-3
- **Tier 2 (Secondary):** SULAM refining system
- **Tier 3 (Product):** CIPTA crafting system
- **Tier 4 (Artisan):** High-value products (v6.5)

### Integration Opportunities

#### A. Expand Material Granularity
**Location:** `MASTER_ITEMS` object (lines ~2523-2627)

**Current:** 6 raw materials (organic_wet, organic_dry, plastic_hdpe, plastic_ldpe, metal_scrap, glass_waste)

**Enhancement Opportunity:**
- Add contamination levels (clean vs dirty materials)
- Add material quality grades (A/B/C grade affects output yield)
- Add regional material variants (different biomes = different materials)

**Implementation:**
```javascript
// Add to MASTER_ITEMS
organic_wet_contaminated: {
  id: 'organic_wet_contaminated',
  tier: 'raw',
  label: 'Contaminated Wet Organic',
  icon: '🍃💧',
  desc: 'Needs cleaning before processing',
  co2_factor: 0.04,  // Lower value due to contamination
  sell_direct: 1,
  requires_cleaning: true,
}
```

**Hook Point:** `EconomyManager.collectFromMatch()` (line ~2800-2850)
- Currently maps match-3 tiles → raw materials
- Can add logic: "10% chance of contaminated material"

---

#### B. Add Pre-Processing Step (Cleaning/Sorting)
**Location:** New tab in MyShalter screen

**Current Flow:** Raw → SULAM → CIPTA → ARTISAN

**Enhanced Flow:** Raw → **CLEAN** → SULAM → CIPTA → ARTISAN

**UI Integration Point:** 
- Add new tab in `eco-tabs-container` (line ~1536-1546)
- Insert between "📦 Inventory" and "⚗️ Refine"

```html
<button class="eco-tab" onclick="ecoSwitchTab('eco-clean-panel',this)">
  🧹 Clean
</button>
```

**Game Mechanic:**
- Mini-game: Sort materials by type (drag-and-drop)
- Reward: Higher yield in SULAM refining (e.g., 3 clean inputs → 3 outputs instead of 2)
- Educational: Teach importance of waste segregation

---

#### C. Material Degradation Over Time
**Location:** `saveGameState()` and `loadGameState()` functions

**Concept:** Raw materials degrade if not processed within X days
- Organic materials degrade faster (3 days)
- Plastics/metals degrade slower (7 days)

**Implementation:**
```javascript
// Add to game state
inventory_timestamps: {
  organic_wet: 1714771200000,  // Unix timestamp when collected
  plastic_hdpe: 1714857600000,
}

// Check on load
function checkMaterialDegradation(state) {
  const now = Date.now();
  for (const [itemId, timestamp] of Object.entries(state.inventory_timestamps)) {
    const item = MASTER_ITEMS[itemId];
    const ageInDays = (now - timestamp) / (1000 * 60 * 60 * 24);
    
    if (item.tier === 'raw' && item.id.startsWith('organic_') && ageInDays > 3) {
      // Degrade 50% of organic materials
      state.inventory[itemId] = Math.floor(state.inventory[itemId] * 0.5);
      showGotchiDialogue('Some organics composted naturally! 🌱');
    }
  }
}
```

**Hook Point:** `loadGameState()` (line ~5500-5600)

---

## 2. Processing Facility System Hooks

### Current State
Processing happens instantly via button clicks in MyShalter tabs (SULAM/CIPTA/ARTISAN).

### Enhancement Opportunities

#### A. Time-Based Processing (Facility Queue)
**Location:** New `FacilityManager` class

**Concept:** 
- Refining/crafting takes real time (e.g., 30 minutes for compost pellet)
- Multiple facility slots (start with 1, unlock more with upgrades)
- Can speed up with Regro tokens (monetization hook)

**Implementation:**
```javascript
class FacilityManager {
  constructor() {
    this.slots = [
      { id: 1, recipeId: null, startTime: null, duration: 0 },
      { id: 2, recipeId: null, startTime: null, duration: 0 },  // Locked initially
    ];
  }
  
  startProcessing(slotId, recipeId) {
    const recipe = MASTER_RECIPES[recipeId];
    const slot = this.slots.find(s => s.id === slotId);
    
    // Deduct inputs from inventory
    // Set slot.startTime = Date.now()
    // Set slot.duration = recipe.processing_time_minutes * 60 * 1000
    
    // Show notification when complete (via background timer)
  }
  
  checkCompletion() {
    // Called every 30 seconds
    // If slot.startTime + slot.duration < Date.now(), add output to inventory
  }
}
```

**UI Integration:**
- Add "Processing Queue" panel in MyShalter
- Show progress bars for active slots
- Push notification when processing completes (if service worker enabled)

**Hook Point:** 
- Initialize in main game init (line ~6400)
- Update in game loop or setInterval

---

#### B. Facility Upgrades
**Location:** New "🏭 Facilities" tab in MyShalter

**Concept:**
- Upgrade SULAM facility → faster refining, higher yield
- Upgrade CIPTA facility → unlock advanced recipes
- Upgrade ARTISAN workshop → reduce KARSA cost

**Data Model:**
```javascript
// Add to game state
facilities: {
  sulam: { level: 1, speed_bonus: 0, yield_bonus: 0 },
  cipta: { level: 1, speed_bonus: 0, yield_bonus: 0 },
  artisan: { level: 1, karsa_discount: 0 },
}

// Upgrade costs
FACILITY_UPGRADES: {
  sulam_level_2: {
    cost: { regroTokens: 500, eco_brick: 5 },
    bonus: { speed: 0.2, yield: 0.1 },  // 20% faster, 10% more output
  },
}
```

**UI Integration:**
- Add upgrade button in each economy tab
- Show current level & next level benefits
- Require both tokens + materials (creates demand for economy loop)

---

#### C. Facility Breakdowns & Maintenance
**Location:** Random event system (new)

**Concept:**
- 5% chance per day that a facility breaks down
- Requires repair materials (metal_ingot, plastic_flake)
- Educational: Teach importance of maintenance in circular economy

**Implementation:**
```javascript
function checkFacilityHealth() {
  const state = loadGameState();
  const now = Date.now();
  const lastCheck = state.lastFacilityCheck || 0;
  
  if (now - lastCheck > 24 * 60 * 60 * 1000) {  // 24 hours
    if (Math.random() < 0.05) {
      state.facilities.sulam.broken = true;
      showModal('Facility Breakdown!', 'Your SULAM facility needs repair. Bring 2 metal ingots to fix it.');
    }
    state.lastFacilityCheck = now;
    saveGameState(state);
  }
}
```

**Hook Point:** Daily checkin flow (line ~5800-5900)

---

## 3. Educational Content Injection Points

### Current State
Game has gotchi dialogues (`GOTCHI_DIALOGUES` object, line ~3756-3786) that provide contextual feedback.

### Enhancement Opportunities

#### A. Material Info Cards
**Location:** Inventory panel (line ~1547-1549)

**Current:** Simple list of items with icons & quantities

**Enhancement:**
- Click on item → show modal with:
  - Real-world facts (e.g., "1 ton of recycled plastic saves 5,774 kWh of energy")
  - Processing steps (visual flowchart)
  - Environmental impact (CO₂ saved, water saved)
  - Local recycling tips (if geolocation enabled)

**Implementation:**
```javascript
function showMaterialInfo(itemId) {
  const item = MASTER_ITEMS[itemId];
  const facts = EDUCATIONAL_FACTS[itemId];  // New data structure
  
  showModal(
    `${item.icon} ${item.label}`,
    `
    <div class="edu-card">
      <p>${item.desc}</p>
      <div class="edu-fact">💡 ${facts.realWorldFact}</div>
      <div class="edu-impact">
        🌍 CO₂ Saved: ${item.co2_factor} kg per unit<br>
        💧 Water Saved: ${facts.waterSaved} liters
      </div>
      <div class="edu-tips">${facts.recyclingTip}</div>
    </div>
    `
  );
}
```

**Hook Point:** Add `onclick` handler to inventory items (line ~1549)

---

#### B. Tutorial Quests (Guided Learning)
**Location:** Daily Quest system (line ~2900-3100)

**Current:** 5 quest types (collect X, refine Y, craft Z, sell items, play levels)

**Enhancement:** Add "Educational Quest" type
- Quest: "Learn about HDPE plastic"
- Task: Read material info card + answer quiz question
- Reward: 50 Regro tokens + unlock HDPE-specific recipe

**Implementation:**
```javascript
// Add to MASTER_QUESTS
{
  id: 'edu_hdpe',
  type: 'educational',
  label: 'Plastic Detective',
  desc: 'Learn about HDPE plastic and its recycling process',
  icon: '🧴',
  tasks: [
    { type: 'read_info', itemId: 'plastic_hdpe' },
    { type: 'quiz', question: 'What does HDPE stand for?', answer: 'High-Density Polyethylene' },
  ],
  reward: { regroTokens: 50, unlock_recipe: 'sulam_plastic_advanced' },
}
```

**Hook Point:** Quest panel (line ~1542, eco-quest-panel)

---

#### C. Impact Visualization (Real-World Equivalents)
**Location:** Impact screen (line ~1460-1482)

**Current:** Shows trees planted, CO₂ saved (abstract numbers)

**Enhancement:** Convert to relatable equivalents
- "Your 2.5 trees = 1 year of oxygen for 1 person"
- "Your 15kg CO₂ saved = 60km of car driving avoided"
- "Your 50 plastic bottles recycled = 1 fleece jacket made"

**Implementation:**
```javascript
function calculateImpactEquivalents(state) {
  const trees = state.treesPlanted;
  const co2 = state.totalCO2Saved;
  const plasticBottles = state.inventory.plastic_hdpe + state.inventory.plastic_ldpe;
  
  return {
    oxygenYears: (trees * 0.4).toFixed(1),  // 1 tree = 0.4 person-years of O₂
    carKmAvoided: (co2 * 4).toFixed(0),     // 1kg CO₂ = 4km driving
    fleeceJackets: Math.floor(plasticBottles / 50),
  };
}
```

**Hook Point:** Impact screen render (line ~1470-1476)

---

#### D. Gotchi as Educational Guide
**Location:** `GOTCHI_DIALOGUES` expansion

**Current:** Gotchi gives gameplay feedback ("Nice match!", "I'm thirsty...")

**Enhancement:** Add educational dialogue triggers
- After collecting contaminated material: "Did you know? Contaminated recyclables can ruin entire batches! Always rinse before recycling."
- After crafting solar panel: "Fun fact: Solar panels can last 25+ years and save tons of CO₂!"
- After facility breakdown: "Just like real recycling centers, our facilities need regular maintenance to run efficiently."

**Implementation:**
```javascript
// Add to GOTCHI_DIALOGUES
educational: {
  contamination: "Did you know? Contaminated recyclables can ruin entire batches! Always rinse before recycling.",
  solar_panel: "Fun fact: Solar panels can last 25+ years and save tons of CO₂!",
  facility_maintenance: "Just like real recycling centers, our facilities need regular maintenance to run efficiently.",
}

// Trigger in relevant game events
function onCraftComplete(recipeId) {
  if (recipeId === 'cipta_solar') {
    showGotchiDialogue(GOTCHI_DIALOGUES.educational.solar_panel);
  }
}
```

**Hook Point:** Craft completion handler (line ~3000-3100)

---

## 4. UI/UX Modification Areas

### A. MyShalter Screen Reorganization
**Current Layout:** 4-card grid + 8 tabs below (line ~1487-1546)

**Proposed Enhancement:**
```
┌─────────────────────────────────────┐
│  MyShalter Header                   │
├─────────────────────────────────────┤
│  📊 Dashboard (new)                 │
│  - Total CO₂ saved (lifetime)       │
│  - Active processing jobs           │
│  - Daily quest progress             │
├─────────────────────────────────────┤
│  Tabs: 📦 Inventory | 🧹 Clean |    │
│        ⚗️ Refine | 🔨 Craft |       │
│        🏭 Facilities | 💰 Market |   │
│        🎯 Quests | 🖼️ Gallery       │
└─────────────────────────────────────┘
```

**Changes:**
- Remove 4-card grid (redundant with tabs)
- Add dashboard panel showing key metrics
- Add "🧹 Clean" tab for pre-processing
- Add "🏭 Facilities" tab for upgrades

**Hook Point:** Line ~1487-1546 (full rewrite of myshalter-screen)

---

### B. In-Game Material Flow Visualization
**Location:** New overlay during match-3 gameplay

**Concept:** 
- When player matches tiles, show brief animation of material flowing into inventory
- Visual: Tile icon → shrinks → flies to top-right inventory counter
- Educational: Reinforces connection between gameplay and economy

**Implementation:**
```javascript
function animateMaterialCollection(tileElement, itemId) {
  const icon = MASTER_ITEMS[itemId].icon;
  const inventoryIcon = document.querySelector('#inventory-counter');
  
  // Create flying icon
  const flyingIcon = document.createElement('div');
  flyingIcon.textContent = icon;
  flyingIcon.className = 'flying-material-icon';
  
  // Animate from tile position to inventory
  const startPos = tileElement.getBoundingClientRect();
  const endPos = inventoryIcon.getBoundingClientRect();
  
  flyingIcon.style.left = startPos.left + 'px';
  flyingIcon.style.top = startPos.top + 'px';
  document.body.appendChild(flyingIcon);
  
  // CSS animation or GSAP tween
  flyingIcon.animate([
    { transform: 'translate(0, 0) scale(1)', opacity: 1 },
    { transform: `translate(${endPos.left - startPos.left}px, ${endPos.top - startPos.top}px) scale(0.3)`, opacity: 0.8 }
  ], { duration: 800, easing: 'ease-out' });
  
  setTimeout(() => flyingIcon.remove(), 800);
}
```

**Hook Point:** `EconomyManager.collectFromMatch()` (line ~2800-2850)

---

### C. Processing Facility Visual Representation
**Location:** New screen or MyShalter background

**Concept:**
- Show 3D isometric view of player's facilities
- Facilities animate when processing (smoke from SULAM, sparks from CIPTA)
- Click on facility → open upgrade/queue panel

**Implementation:**
- Use CSS 3D transforms or Canvas/SVG
- Similar to "Sanctuary" screen (line ~1700-1744) but for facilities
- Update visual state based on `facilities` object in game state

**Hook Point:** New screen between MyShalter and Sanctuary

---

### D. Material Lifecycle Flowchart (Help Screen)
**Location:** New "📚 Learn" button in main menu

**Concept:**
- Interactive flowchart showing full material lifecycle
- Click on any node → see details + educational facts
- Highlight player's current progress (grayed out = not unlocked yet)

**Implementation:**
```html
<div id="learn-screen" class="screen">
  <div class="flowchart-container">
    <svg viewBox="0 0 800 600">
      <!-- Nodes for each material/recipe -->
      <g id="node-organic-wet" class="flowchart-node unlocked">
        <circle cx="100" cy="100" r="30" fill="#A8E6CF"/>
        <text x="100" y="105">🍃</text>
      </g>
      <!-- Arrows showing flow -->
      <path d="M130,100 L200,100" stroke="#78C2AD" stroke-width="3"/>
      <!-- ... more nodes ... -->
    </svg>
  </div>
</div>
```

**Hook Point:** Add button in main menu (line ~1330-1370)

---

## Summary of Integration Points

### High Priority (Phase 1)
1. **Material Info Cards** - Low effort, high educational value
2. **Impact Visualization** - Enhance existing impact screen
3. **Educational Gotchi Dialogues** - Expand existing system
4. **Processing Queue UI** - Foundation for time-based mechanics

### Medium Priority (Phase 2)
5. **Cleaning/Sorting Mini-Game** - New gameplay mechanic
6. **Facility Upgrades** - Progression system
7. **Material Degradation** - Adds urgency to economy loop
8. **Tutorial Quests** - Guided learning

### Low Priority (Phase 3)
9. **Facility Visual Representation** - Polish/immersion
10. **Material Flow Animation** - Visual feedback
11. **Lifecycle Flowchart** - Reference tool
12. **Facility Breakdowns** - Advanced mechanic

### Non-Breaking Integration Strategy
- All enhancements are **additive** (no removal of existing features)
- New tabs/screens don't interfere with current navigation
- Economy enhancements are **optional** (players can ignore and play as before)
- Educational content is **contextual** (doesn't interrupt core gameplay)
- Time-based mechanics have **instant complete** option (Regro token monetization)

### Backend API Requirements
Most features work offline-first, but these need backend support:
- Educational content CMS (update facts without app update)
- Processing queue sync (cross-device)
- Facility upgrade purchases (if using real IAP)
- Educational quest completion tracking (for analytics)
