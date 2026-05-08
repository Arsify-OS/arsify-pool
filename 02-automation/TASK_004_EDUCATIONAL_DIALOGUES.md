# TASK_004: Educational Gotchi Dialogues

**Started:** 2026-05-03 23:47 UTC  
**Status:** IN PROGRESS  
**Priority:** MEDIUM  
**Estimated Time:** 30 minutes

---

## Objective

Expand Gotchi dialogues to include educational content about recycling, circular economy, and environmental impact. Make learning seamless and contextual during gameplay.

---

## Implementation Plan

### Phase 1: Find Current Dialogues (5 min)
- [ ] Locate GOTCHI_DIALOGUES object
- [ ] Understand current dialogue structure
- [ ] Identify trigger points

### Phase 2: Add Educational Dialogues (15 min)
- [ ] Add material-specific facts (when collecting)
- [ ] Add crafting tips (when using SULAM/CIPTA)
- [ ] Add milestone celebrations (achievements)
- [ ] Add random educational tips

### Phase 3: Add Trigger Points (5 min)
- [ ] Hook into material collection
- [ ] Hook into crafting events
- [ ] Hook into achievement unlocks

### Phase 4: Testing (5 min)
- [ ] Test dialogue triggers
- [ ] Verify educational content accuracy
- [ ] Check mobile display

---

## Educational Dialogue Content

### Material Collection Dialogues

**Organic Materials:**
- "Did you know? Food waste in landfills produces methane, a greenhouse gas 25x more potent than CO₂!"
- "Composting turns waste into nutrient-rich soil. Nature's recycling! 🌱"
- "Fun fact: 1/3 of all food produced globally is wasted. Let's change that!"

**HDPE Plastic:**
- "HDPE plastic (#2) is one of the most recyclable plastics. Look for the symbol!"
- "Recycling 1 ton of HDPE saves enough energy to power a home for 6 months! ⚡"
- "HDPE can become new bottles, toys, or even outdoor furniture!"

**LDPE Plastic:**
- "LDPE (#4) is used in bags and films. Many stores have drop-off bins for these!"
- "Plastic bags can be recycled into composite lumber for decks and benches!"
- "Tip: Collect plastic bags in one bag before recycling. It's easier to handle!"

**Metal:**
- "Aluminum can be recycled infinitely without losing quality! ♻️"
- "Recycling 1 aluminum can saves enough energy to run a TV for 3 hours!"
- "Fun fact: 75% of all aluminum ever produced is still in use today!"

**Glass:**
- "Glass can be recycled forever without losing purity. True circular economy! 🫙"
- "Recycled glass melts at lower temperatures, saving energy!"
- "Tip: Separate glass by color (clear, green, brown) for better recycling!"

### Crafting Dialogues

**SULAM (Refining):**
- "Refining raw materials is the first step in the circular economy chain!"
- "Clean materials = better quality output. Always rinse before recycling!"
- "Industrial recycling uses similar processes. You're learning real skills!"

**CIPTA (Crafting):**
- "Eco-bricks are real! They're used in construction worldwide. 🧱"
- "Solar panels can last 25+ years and save tons of CO₂!"
- "Bio-fuel from organic waste? Yes! It's called anaerobic digestion."

**ARTISAN (High-tier):**
- "Vertical gardens reduce urban heat and improve air quality!"
- "Solar water heaters can reduce energy bills by 50-80%!"
- "Circular hubs are real recycling centers. You're building one virtually!"

### Achievement Dialogues

**First Tree Planted:**
- "Your first tree! 🌳 One tree absorbs ~21kg of CO₂ per year. Keep going!"

**100 Matches:**
- "100 matches! You're getting the hang of waste sorting. Every match counts!"

**First Craft:**
- "Your first craft! This is what circular economy is all about - waste becomes resource!"

**Daily Streak:**
- "Daily streak! Consistency is key in both gaming and real-world recycling habits!"

### Random Educational Tips

- "Contamination is the enemy of recycling. One dirty item can ruin a whole batch!"
- "Reduce, Reuse, Recycle - in that order! Prevention is better than recycling."
- "Recycling 1 ton of paper saves 17 trees, 7,000 gallons of water, and 3 cubic yards of landfill space!"
- "E-waste contains valuable metals like gold and silver. Always recycle electronics!"
- "Composting at home? Keep it balanced: 2 parts brown (dry) to 1 part green (wet)!"

---

## Code Implementation

### Step 1: Expand GOTCHI_DIALOGUES

Find GOTCHI_DIALOGUES object and add educational section:

```javascript
const GOTCHI_DIALOGUES = {
    // ... existing dialogues ...
    
    // ═══ EDUCATIONAL DIALOGUES [TASK_004] ═══════════════════════════════════
    educational: {
        // Material collection
        organic_collected: [
            "Did you know? Food waste in landfills produces methane, a greenhouse gas 25x more potent than CO₂!",
            "Composting turns waste into nutrient-rich soil. Nature's recycling! 🌱",
            "Fun fact: 1/3 of all food produced globally is wasted. Let's change that!"
        ],
        plastic_hdpe_collected: [
            "HDPE plastic (#2) is one of the most recyclable plastics. Look for the symbol!",
            "Recycling 1 ton of HDPE saves enough energy to power a home for 6 months! ⚡",
            "HDPE can become new bottles, toys, or even outdoor furniture!"
        ],
        plastic_ldpe_collected: [
            "LDPE (#4) is used in bags and films. Many stores have drop-off bins for these!",
            "Plastic bags can be recycled into composite lumber for decks and benches!",
            "Tip: Collect plastic bags in one bag before recycling. It's easier to handle!"
        ],
        metal_collected: [
            "Aluminum can be recycled infinitely without losing quality! ♻️",
            "Recycling 1 aluminum can saves enough energy to run a TV for 3 hours!",
            "Fun fact: 75% of all aluminum ever produced is still in use today!"
        ],
        glass_collected: [
            "Glass can be recycled forever without losing purity. True circular economy! 🫙",
            "Recycled glass melts at lower temperatures, saving energy!",
            "Tip: Separate glass by color (clear, green, brown) for better recycling!"
        ],
        
        // Crafting
        sulam_used: [
            "Refining raw materials is the first step in the circular economy chain!",
            "Clean materials = better quality output. Always rinse before recycling!",
            "Industrial recycling uses similar processes. You're learning real skills!"
        ],
        cipta_used: [
            "Eco-bricks are real! They're used in construction worldwide. 🧱",
            "Solar panels can last 25+ years and save tons of CO₂!",
            "Bio-fuel from organic waste? Yes! It's called anaerobic digestion."
        ],
        artisan_used: [
            "Vertical gardens reduce urban heat and improve air quality!",
            "Solar water heaters can reduce energy bills by 50-80%!",
            "Circular hubs are real recycling centers. You're building one virtually!"
        ],
        
        // Achievements
        first_tree: "Your first tree! 🌳 One tree absorbs ~21kg of CO₂ per year. Keep going!",
        matches_100: "100 matches! You're getting the hang of waste sorting. Every match counts!",
        first_craft: "Your first craft! This is what circular economy is all about - waste becomes resource!",
        daily_streak: "Daily streak! Consistency is key in both gaming and real-world recycling habits!",
        
        // Random tips
        random_tips: [
            "Contamination is the enemy of recycling. One dirty item can ruin a whole batch!",
            "Reduce, Reuse, Recycle - in that order! Prevention is better than recycling.",
            "Recycling 1 ton of paper saves 17 trees, 7,000 gallons of water, and 3 cubic yards of landfill space!",
            "E-waste contains valuable metals like gold and silver. Always recycle electronics!",
            "Composting at home? Keep it balanced: 2 parts brown (dry) to 1 part green (wet)!"
        ]
    }
};
```

### Step 2: Add Helper Function

```javascript
// Show educational dialogue (random from array or single string)
function showEducationalDialogue(key) {
    const content = GOTCHI_DIALOGUES.educational[key];
    if (!content) return;
    
    let message;
    if (Array.isArray(content)) {
        // Pick random from array
        message = content[Math.floor(Math.random() * content.length)];
    } else {
        message = content;
    }
    
    showGotchiDialogue(message);
}
```

### Step 3: Add Trigger Points

**In EconomyManager.collectFromMatch():**
```javascript
collectFromMatch(tileType) {
    // ... existing code ...
    
    // Educational dialogue (10% chance)
    if (Math.random() < 0.1) {
        const eduKey = itemId + '_collected';
        showEducationalDialogue(eduKey);
    }
}
```

**In EconomyManager.refine() and craft():**
```javascript
refine(recipeId) {
    // ... existing code ...
    
    // Educational dialogue (20% chance)
    if (Math.random() < 0.2) {
        showEducationalDialogue('sulam_used');
    }
}

craft(recipeId) {
    // ... existing code ...
    
    // Educational dialogue (20% chance)
    if (Math.random() < 0.2) {
        const recipe = MASTER_RECIPES[recipeId];
        if (recipe.type === 'cipta') {
            showEducationalDialogue('cipta_used');
        } else if (recipe.type === 'artisan') {
            showEducationalDialogue('artisan_used');
        }
    }
}
```

**In achievement unlock:**
```javascript
// When first tree is planted
if (trees >= 1 && !this.achievements.first_tree) {
    showEducationalDialogue('first_tree');
}

// When 100 matches reached
if (this.collectionStats.totalMatches >= 100 && !this.achievements.matches_100) {
    showEducationalDialogue('matches_100');
}
```

---

## Testing Checklist

- [ ] Collect organic material → educational dialogue appears (10% chance)
- [ ] Collect plastic → HDPE/LDPE facts appear
- [ ] Use SULAM → refining tips appear (20% chance)
- [ ] Use CIPTA → crafting facts appear
- [ ] Plant first tree → achievement dialogue
- [ ] Reach 100 matches → milestone dialogue
- [ ] Dialogues don't interrupt gameplay
- [ ] Mobile display works

---

## Success Metrics

- Educational dialogues appear at appropriate times
- Content is accurate and engaging
- Doesn't overwhelm user (low trigger rates)
- Complements gameplay without interrupting

---

## Notes

- Keep trigger rates low (10-20%) to avoid spam
- Use arrays for variety (multiple messages per event)
- Focus on actionable tips users can apply in real life
- Balance education with entertainment
