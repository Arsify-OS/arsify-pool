# Regrow Up World - Game Architecture Analysis

**Analysis Date:** 2026-05-03  
**Game Version:** v6.5 (Artisan & Gallery)  
**File:** Upshalter-Odyssey-RegrowUp.html (6512 lines, 332KB)

---

## 1. Current Game Structure

### File Organization
Single-file HTML architecture with embedded resources:
- **Lines 1-1249:** CSS styling (variables, animations, screens, components)
- **Lines 1250-1744:** HTML structure (screens, overlays, modals, game grid)
- **Lines 1745-1860:** Sound system (script block 1/4)
- **Lines 1861-2496:** Level definitions (script block 2/4)
- **Lines 2497-3621:** Economy engine (script block 3/4)
- **Lines 3622-6512:** Core game engine (script block 4/4)

### Core Systems

#### A. Screen Management
Multi-screen SPA architecture:
- `#main-menu` - Entry point with gotchi, currency display
- `#game-screen` - Match-3 gameplay grid
- `#impact-screen` - Post-level results & environmental impact
- `#myshalter-screen` - Economy hub (COLLECT/CRAFT/CONNECT/SHARE)
- `#world-map-screen` - Level selection (biomes, progression)
- `#leaderboard-screen` - Global & friends rankings
- `#sanctuary-screen` - Gotchi care & item buffs

Screens use `.screen.active` pattern with fade-in animations.

#### B. Game Engine Components

**FCTManager** (Floating Combat Text)
- Object pool pattern (20 pre-allocated DOM elements)
- Spawns score popups, combo text, achievement notifications

**EconomyManager** (v6.4-6.5)
- 6 granular tile types: `organic_wet`, `organic_dry`, `plastic_hdpe`, `plastic_ldpe`, `metal_scrap`, `glass_waste`
- 3-tier material lifecycle:
  - **Raw** → **Secondary** (SULAM/Refine)
  - **Secondary** → **Product** (CIPTA/Craft)
  - **Product** → **Artisan** (Tier 4, v6.5)
- KARSA energy system (regenerates per match/combo)
- Daily quests (5 types, 3 per day)
- Eco-Market (sell items for Regro tokens)

**AuthManager** (v6.3)
- Supabase integration (signup/login/guest)
- Cloud save sync (offline-first, last-write-wins)
- Username + avatar selection

**Match-3 Core**
- 6x6 grid (`CONFIG.GRID_SIZE`)
- 4 base tile types: `organic`, `recyclable`, `special`, `grime`
- Special tiles: `bomb` (match-4), `rainbow` (match-5)
- Cascade detection & combo multipliers
- Bloom mode (4+ consecutive matches)

---

## 2. Data Models

### Game State Schema (v6.5)

```javascript
{
  // Meta
  saveVersion: '6.5',
  userId: null,              // Supabase user ID
  cloudSyncAt: null,         // Last cloud sync timestamp
  
  // Progression
  currentLevel: 1,
  levelsCompleted: 0,
  highScore: 0,
  regroTokens: 0,            // Premium currency
  
  // Match-3 Stats
  totalMatches: 0,
  maxCascade: 0,
  bomb: 0,                   // Bomb tiles used
  rainbow: 0,                // Rainbow tiles used
  grime: 0,                  // Grime tiles matched
  
  // Gotchi (Virtual Pet)
  gotchiStage: 1,            // 1-5 evolution stages
  gotchiHunger: 100,         // 0-100, decays over time
  gotchiLastFed: timestamp,
  
  // Environmental Impact
  totalMatches: 0,           // Used for tree calculation
  treesPlanted: 0.000,       // Float, 100 matches = 1 tree
  
  // Economy (v6.4+)
  inventory: {
    organic_wet: 0,
    plastic_hdpe: 0,
    // ... all 15 item types
  },
  karsa: 10,                 // Current energy
  karsaMax: 30,              // Max capacity
  
  // Social (v6.3)
  dailyStreak: 0,
  lastCheckin: null,
  achievements: [],          // Array of unlocked achievement IDs
  cloudSynced: 0,            // Count of cloud syncs
  leaderboardTop3: 0,        // Times in top 3
  
  // Daily Challenge (v6.3)
  dailyChallengeCompleted: false,
  dailyChallengeDate: null,
  
  // Sanctuary (v6.5)
  sanctuaryItems: [],        // Placed items with buffs
}
```

### Master Data Structures

**MASTER_ITEMS** (15 items across 4 tiers)
```javascript
{
  id: string,
  tier: 'raw' | 'secondary' | 'product' | 'artisan',
  label: string,
  icon: emoji,
  desc: string,
  co2_factor: float,         // kg CO₂ saved per unit
  sell_direct: int,          // Regro tokens if sold
}
```

**MASTER_RECIPES** (10 recipes)
```javascript
{
  id: string,
  type: 'sulam' | 'cipta' | 'artisan',
  label: string,
  icon: emoji,
  karsa_cost: int,           // Energy required
  inputs: [{ id, qty }],
  output: { id, qty },
  desc: string,
  unlock_level: int,
}
```

**GAME_LEVELS** (window.GAME_LEVELS from levels.js)
```javascript
{
  id: int,
  initialMoves: int,
  targetScore: int,
  description: string,
  tileTypes: ['organic', 'recyclable', ...],
  tileWeights: { organic: 55, recyclable: 45 },
  difficulty: 'tutorial' | 'easy' | 'medium' | 'hard',
  pattern: 'simple' | 'cascade' | 'grime',
}
```

**CONFIG.EVOLUTION_STAGES** (Gotchi progression)
```javascript
[
  { stage: 1, name: 'Seedling',   threshold: 0,   nextAt: 20,  icon: '🌱' },
  { stage: 2, name: 'Sprout',     threshold: 20,  nextAt: 60,  icon: '🌿' },
  { stage: 3, name: 'Sapling',    threshold: 60,  nextAt: 150, icon: '🌳' },
  { stage: 4, name: 'Robot Tree', threshold: 150, nextAt: 300, icon: '🤖' },
  { stage: 5, name: 'Guardian',   threshold: 300, nextAt: null,icon: '✨' },
]
```

**CONFIG.ACHIEVEMENTS** (14 achievements)
- 8 original (v6.2): first_match, ten_matches, first_cascade, cascade_master, first_tree, bomb_user, rainbow_user, level_5
- 6 new (v6.3): speed_runner, grime_buster, hungry_helper, daily_devotee, cloud_saver, social_climber

---

## 3. Game Loop Flow

### Initialization Sequence
1. Load `window.GAME_LEVELS` from levels.js
2. Initialize managers: `FCTManager`, `EconomyManager`, `AuthManager`
3. Load save state from localStorage (`UPSHALTER_SAVE_v6.5`)
4. Render main menu with gotchi & currency
5. Check daily streak & show daily challenge modal if available

### Match-3 Gameplay Loop
```
User Input (swap tiles)
  ↓
Validate move (adjacent tiles)
  ↓
Find matches (horizontal/vertical 3+)
  ↓
Mark special tiles (bomb on 4-match, rainbow on 5-match)
  ↓
Remove matched tiles + spawn floating text
  ↓
Update score, combo counter, bloom mode
  ↓
Collect materials (EconomyManager.collectFromMatch)
  ↓
Apply gravity (tiles fall down)
  ↓
Fill empty cells (new random tiles)
  ↓
Check for cascades (auto-matches from falling tiles)
  ↓
  If cascade → repeat from "Find matches"
  If no cascade → decrement moves
  ↓
Check win/lose conditions
  ↓
  If targetScore reached → show impact screen
  If moves = 0 → show game over modal
  Else → wait for next user input
```

### Post-Level Flow
```
Level Complete
  ↓
Calculate impact (organic collected, recyclable processed, trees planted)
  ↓
Update lifetime stats (totalMatches, treesPlanted)
  ↓
Check achievements (unlock new ones)
  ↓
Save game state (localStorage + cloud sync if authenticated)
  ↓
Show impact screen with stats & share button
  ↓
User clicks "Continue"
  ↓
Return to world map (next level unlocked)
```

### Economy Loop (v6.4+)
```
Match-3 → Collect raw materials (6 types)
  ↓
SULAM (Refine) → Convert raw → secondary (costs KARSA)
  ↓
CIPTA (Craft) → Convert secondary → product (costs KARSA)
  ↓
ARTISAN → Convert product → artisan tier (costs KARSA)
  ↓
Eco-Market → Sell any item → Regro tokens
  ↓
Daily Quests → Complete tasks → Regro tokens + KARSA
```

### KARSA Regeneration
- +1 KARSA per match-3
- +2 KARSA per match-4 (bomb)
- +3 KARSA per match-5 (rainbow)
- +1 KARSA per cascade
- Max capacity: 30 (upgradeable via sanctuary buffs)

---

## 4. State Management

### Storage Strategy
**Primary:** localStorage (`UPSHALTER_SAVE_v6.5`)
- Offline-first architecture
- Auto-save after every level completion
- Manual save on screen transitions

**Secondary:** Supabase Cloud Sync (v6.3)
- Triggered on: level complete, daily checkin, manual sync button
- Last-write-wins conflict resolution
- Endpoint: `POST /api/game/state/:userId`

### State Update Pattern
```javascript
// Read
const state = loadGameState();

// Modify
state.totalMatches += 1;
state.regroTokens += 50;

// Write
saveGameState(state);

// Cloud sync (if authenticated)
if (state.userId) {
  syncToCloud(state);
}
```

### Critical State Transitions
1. **Level Start:** Lock current level, reset moves/score, initialize grid
2. **Level Complete:** Update stats, unlock next level, trigger achievements
3. **Gotchi Evolution:** Check `totalMatches` threshold, update stage, show animation
4. **Daily Checkin:** Increment streak, award tokens, reset daily challenge
5. **Economy Transaction:** Validate inventory, deduct inputs, add outputs, update KARSA

---

## Summary

**Architecture Type:** Single-page application (SPA) with embedded resources  
**State Management:** localStorage + cloud sync (Supabase)  
**Core Loop:** Match-3 → Material Collection → Refine/Craft → Sell/Quest  
**Progression:** Linear level unlocking + gotchi evolution + achievement system  
**Monetization Hooks:** Regro tokens (premium currency), EcoPass teaser (v6.3)

**Key Strengths:**
- Offline-first design (works without backend)
- Modular script organization (sounds → levels → economy → game)
- Rich economy system (3-tier material lifecycle)
- Social features (leaderboard, cloud save, daily challenges)

**Technical Debt:**
- Single 332KB file (hard to maintain)
- No build system (manual minification)
- Inline styles & scripts (no separation of concerns)
- Backend API stubs (all marked `// BACKEND_HOOK`)
