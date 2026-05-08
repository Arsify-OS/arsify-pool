# Regrow Up World - Phase 2 Development Plan

**Date:** 2026-05-04  
**Project:** Regrow Up World (Upshalter Odyssey)  
**Current Version:** v6.6 Full-Stack Offline Edition  
**Live URL:** https://regrow.upshalter.com  
**Workspace:** /workspace/Upshalter-Odyssey-RegrowUp.html

---

## 1. PHASE 1 COMPLETION STATUS ✅

### Implemented Features (Phase 1)
Based on code analysis, the following features are **COMPLETE**:

#### ✅ Material Info Cards (TASK_002)
- **Location:** Lines 5164-5200+
- **Implementation:** `showMaterialInfo(itemId)` method
- **Features:**
  - Educational facts system with `EDUCATIONAL_FACTS` data structure
  - Processing steps visualization
  - CO₂ impact display
  - Energy saved metrics
  - Water saved metrics
  - Modal-based UI presentation

#### ✅ Impact Visualization (TASK_003)
- **Location:** Lines 5045-5143
- **Implementation:** `showImpactStats()` and `shareImpact()` methods
- **Features:**
  - Real-time impact calculation via `calculateImpactEquivalents()`
  - Trees planted → Oxygen person-years conversion
  - CO₂ saved → Car km avoided equivalents
  - Plastic bottles → Fleece jackets conversion
  - Metal recycling metrics
  - Glass recycling metrics
  - Share functionality with clipboard fallback

#### ✅ Educational Dialogues (TASK_004)
- **Location:** Lines 4940-4954
- **Implementation:** `_gotchiSayEducational(key)` method
- **Features:**
  - Context-aware educational messages
  - Gotchi speech bubble system with cooldown management
  - Extended duration (4000ms) for educational content
  - Random selection from dialogue arrays
  - Integration with `GOTCHI_DIALOGUES.educational` data

---

## 2. CURRENT ARCHITECTURE OVERVIEW

### Core Systems Identified

#### Game Engine
- **Main Class:** `Game` (starts ~line 4700)
- **State Management:** `loadGameState()` / `saveGameState()` (lines 5239, 5401)
- **Grid System:** 6x6 match-3 grid with tile types (organic, recyclable, special, grime)
- **Match Detection:** Cascade system with bloom streak mechanics

#### Manager Classes
1. **EconomyManager** (line 2997) - Artisan tier, gallery, sanctuary system
2. **FCTManager** (line 4162) - Floating combat text / score popups
3. **AuthManager** (line 4409) - User authentication (v6.3)
4. **LeaderboardManager** (line 4605) - Competitive features (v6.3)
5. **ASMRSoundEngine** (line 2044) - Procedural audio generation

#### Feature Systems
- **Gotchi Evolution:** Stage-based progression (seedling → sprout → sapling → robot-tree → guardian)
- **Hunger System:** Time-based decay with feeding mechanics
- **Powerups:** Compost Blast, Wind Sweep
- **Daily Challenges:** v6.3 feature with modifiers
- **Achievements:** Tracking system with stats
- **World Map:** Level selection interface

### Data Flow
```
User Action → Game.method() → State Update → saveGameState() → localStorage
                            ↓
                    UI Update (DOM manipulation)
                            ↓
                    Sound/Particle Effects
```

---

## 3. PENDING BACKEND INTEGRATION (v6.3/v6.4)

### TODO Items Found

#### 🔴 HIGH PRIORITY - Backend API Integration

1. **Level Data API** (Line 1922)
   ```javascript
   // TODO (v6.3): swap dengan fetch('/api/levels') dari Supabase.
   ```
   - Current: Hardcoded `LEVEL_DATA` array
   - Target: Dynamic level loading from Supabase
   - Impact: Enables server-side level management

2. **EcoPass Bonus Multiplier** (Line 1923)
   ```javascript
   // TODO (v6.4): eco_pass_bonus_multiplier
   ```
   - Current: Not implemented
   - Target: Premium subscription bonus system
   - Impact: Monetization feature

3. **Gotchi Evolution Stages API** (Line 4024)
   ```javascript
   // TODO (v6.4): EVOLUTION_STAGES akan diambil dari /api/gotchi/stages setelah backend live
   ```
   - Current: Hardcoded `EVOLUTION_STAGES` array
   - Target: Dynamic evolution data from API
   - Impact: Enables server-side gotchi customization

#### Backend Hooks Identified (Comments in Code)

- **Line 5012:** `POST /api/impact/update { userId, matches: total }`
- **Line 5023:** `POST /api/trees/plant { userId, tree_count }`
- **Line 5093:** `GET /api/impact/:userId` (NGO API integration)
- **Lines 3962-3963:** Cloud sync endpoints for game state

---

## 4. PHASE 2 FEATURE PRIORITIES

### Recommended Development Track

Based on the existing architecture and Phase 1 completion, Phase 2 should focus on:

### 🎯 TRACK A: Enhanced Gameplay Mechanics

#### A1. Advanced Match Mechanics
**Priority:** HIGH  
**Effort:** Medium (3-5 days)

**Features:**
- **Special Tile Combos:** Bomb + Rainbow interactions
- **Chain Reaction System:** Multi-cascade scoring bonuses
- **Material Synergy:** Bonus points for matching specific material combinations
- **Timed Challenges:** Speed-based level modifiers

**Implementation Points:**
- Extend `_processMatches()` method
- Add combo detection logic
- Create new particle effects for special combos
- Update scoring system with multipliers

**Files to Modify:**
- Main game logic (~line 5500+)
- Particle system integration
- Sound engine (add new combo sounds)

---

#### A2. Gotchi Interaction System
**Priority:** HIGH  
**Effort:** Medium (4-6 days)

**Features:**
- **Feeding Mini-game:** Interactive feeding with material preferences
- **Gotchi Moods:** Dynamic emotional states based on gameplay
- **Skill System:** Gotchi abilities that affect gameplay (e.g., "Lucky Match" - higher special tile spawn rate)
- **Customization:** Unlockable gotchi accessories/skins

**Implementation Points:**
- Extend gotchi state management
- Create feeding UI modal
- Add mood calculation algorithm
- Implement skill effect modifiers

**Technical Approach:**
```javascript
// New GotchiManager class
class GotchiManager {
    constructor(game) {
        this.game = game;
        this.mood = 'neutral'; // happy, excited, hungry, sad
        this.skills = [];
        this.accessories = [];
    }
    
    updateMood() {
        // Calculate based on hunger, recent matches, evolution stage
    }
    
    applySkillEffects() {
        // Modify game parameters based on active skills
    }
}
```

---

#### A3. Quest & Mission System
**Priority:** MEDIUM  
**Effort:** High (5-7 days)

**Features:**
- **Daily Quests:** "Match 50 organic materials today"
- **Weekly Challenges:** "Plant 5 trees this week"
- **Achievement Milestones:** "Reach 100 total matches"
- **Reward System:** Coins, special tiles, gotchi accessories

**Implementation Points:**
- Create `QuestManager` class
- Design quest data structure
- Build quest UI screen
- Implement progress tracking
- Add reward distribution logic

**Data Structure:**
```javascript
const QUEST_TEMPLATES = {
    daily: [
        { id: 'match_organic_50', type: 'match', material: 'organic', target: 50, reward: { coins: 100 } },
        { id: 'complete_3_levels', type: 'level', target: 3, reward: { coins: 150 } }
    ],
    weekly: [
        { id: 'plant_5_trees', type: 'impact', target: 5, reward: { coins: 500, item: 'gotchi_hat' } }
    ]
};
```

---

### 🎯 TRACK B: Social & Competitive Features

#### B1. Multiplayer Challenge Mode
**Priority:** MEDIUM  
**Effort:** High (7-10 days)

**Features:**
- **Async PvP:** Challenge friends to beat your score on a specific level
- **Live Leaderboards:** Real-time ranking updates
- **Ghost Replay:** Watch top players' match sequences
- **Tournaments:** Weekly competitive events

**Backend Requirements:**
- Supabase real-time subscriptions
- Challenge state management
- Replay data storage

---

#### B2. Guild/Team System
**Priority:** LOW  
**Effort:** High (8-12 days)

**Features:**
- **Team Creation:** Form eco-guilds with friends
- **Collective Goals:** Team-based tree planting targets
- **Guild Buffs:** Shared bonuses for active members
- **Guild Chat:** In-game messaging

---

### 🎯 TRACK C: Content Expansion

#### C1. New Material Types
**Priority:** MEDIUM  
**Effort:** Low (2-3 days)

**New Materials:**
- **E-Waste** (🖥️): Electronics recycling theme
- **Textile** (👕): Clothing upcycling
- **Compost** (🍂): Organic waste transformation
- **Water** (💧): Water conservation theme

**Implementation:**
- Add to tile type system
- Create educational facts
- Design visual assets (SVG)
- Add sound profiles

---

#### C2. Biome/Environment System
**Priority:** MEDIUM  
**Effort:** Medium (4-6 days)

**Features:**
- **Forest Biome:** Current default
- **Ocean Biome:** Marine plastic focus
- **Urban Biome:** City recycling theme
- **Desert Biome:** Water conservation focus

**Visual Changes:**
- Background gradients
- Tile color palettes
- Gotchi variants per biome
- Ambient particle effects

---

### 🎯 TRACK D: Backend Integration (v6.4)

#### D1. Supabase API Integration
**Priority:** HIGH (Prerequisite for cloud features)  
**Effort:** Medium (4-5 days)

**Endpoints to Implement:**
1. `GET /api/levels` - Dynamic level data
2. `GET /api/gotchi/stages` - Evolution stages
3. `POST /api/game/state/:userId` - Cloud save
4. `GET /api/game/state/:userId` - Cloud load
5. `POST /api/impact/update` - Impact tracking
6. `GET /api/leaderboard/:levelId` - Rankings

**Implementation Strategy:**
```javascript
class APIClient {
    constructor(supabaseUrl, supabaseKey) {
        this.baseUrl = supabaseUrl;
        this.headers = {
            'apikey': supabaseKey,
            'Content-Type': 'application/json'
        };
    }
    
    async getLevels() {
        const res = await fetch(`${this.baseUrl}/rest/v1/levels`, {
            headers: this.headers
        });
        return res.json();
    }
    
    async saveGameState(userId, state) {
        await fetch(`${this.baseUrl}/rest/v1/game_states`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({ user_id: userId, state })
        });
    }
}
```

---

## 5. RECOMMENDED PHASE 2 ROADMAP

### Sprint 1 (Week 1-2): Core Gameplay Enhancement
- **A1:** Advanced Match Mechanics
- **A2:** Gotchi Interaction System (Part 1 - Feeding & Moods)
- **C1:** New Material Types (E-Waste, Textile)

**Deliverables:**
- Special tile combo system working
- Gotchi feeding mini-game functional
- 2 new material types integrated

---

### Sprint 2 (Week 3-4): Content & Progression
- **A2:** Gotchi Interaction System (Part 2 - Skills & Customization)
- **A3:** Quest & Mission System
- **C2:** Biome System (Forest + Ocean)

**Deliverables:**
- Quest UI screen complete
- Daily/weekly quest tracking
- 2 biomes with visual themes

---

### Sprint 3 (Week 5-6): Backend & Social
- **D1:** Supabase API Integration
- **B1:** Multiplayer Challenge Mode (Part 1 - Async PvP)

**Deliverables:**
- Cloud save/load working
- Dynamic level loading from API
- Challenge system MVP

---

### Sprint 4 (Week 7-8): Polish & Launch
- **B1:** Multiplayer Challenge Mode (Part 2 - Tournaments)
- Bug fixes and optimization
- Performance testing
- Production deployment

---

## 6. TECHNICAL CONSIDERATIONS

### Performance Optimization
- **Current File Size:** 348KB (7069 lines)
- **Recommendation:** Consider code splitting for Phase 2
  - Separate managers into modules
  - Lazy-load biome assets
  - Implement service worker for offline play

### Mobile Optimization
- Touch gesture improvements for combo mechanics
- Haptic feedback for special matches
- Battery-efficient particle rendering

### Accessibility
- Screen reader support for educational content
- Keyboard navigation for all features
- High contrast mode option

---

## 7. METRICS & SUCCESS CRITERIA

### Phase 2 KPIs
- **Engagement:** Average session time > 15 minutes
- **Retention:** Day 7 retention > 40%
- **Social:** 20% of players send challenges
- **Monetization:** 5% EcoPass conversion rate
- **Impact:** 10,000 virtual trees planted

### Analytics Events to Track
```javascript
// New events for Phase 2
logEvent('combo_special_triggered', { combo_type, score_bonus });
logEvent('gotchi_fed', { material_type, hunger_restored });
logEvent('quest_completed', { quest_id, reward_type });
logEvent('challenge_sent', { recipient_id, level_id });
logEvent('biome_unlocked', { biome_name });
```

---

## 8. NEXT STEPS

### Immediate Actions (Today)
1. ✅ **DONE:** Analyze Phase 1 completion
2. ✅ **DONE:** Document current architecture
3. ⏳ **NEXT:** Review this plan with team
4. ⏳ **NEXT:** Prioritize features based on business goals

### This Week
1. Set up development branch for Phase 2
2. Create detailed technical specs for Sprint 1 features
3. Design UI mockups for new screens (Quest, Feeding)
4. Set up Supabase project and schema

### Development Workflow
```bash
# Branch strategy
main (production) → develop (staging) → feature/phase2-* (development)

# Example feature branches
feature/phase2-combo-system
feature/phase2-gotchi-feeding
feature/phase2-quest-system
```

---

## 9. RISK ASSESSMENT

### Technical Risks
- **File Size Growth:** Single-file architecture may become unwieldy
  - **Mitigation:** Plan modular refactor for Phase 3
- **State Management Complexity:** More features = more state
  - **Mitigation:** Consider state management library (Zustand/Jotai)
- **Backend Dependency:** Supabase integration critical path
  - **Mitigation:** Build with offline-first approach, sync when available

### Product Risks
- **Feature Creep:** Too many features may dilute core gameplay
  - **Mitigation:** Strict prioritization, MVP approach per feature
- **User Confusion:** New mechanics need clear onboarding
  - **Mitigation:** Extend tutorial system, add contextual hints

---

## 10. RESOURCES NEEDED

### Development
- **Frontend Developer:** 1 FTE (full-time equivalent)
- **Backend Developer:** 0.5 FTE (Supabase setup)
- **Game Designer:** 0.3 FTE (balancing, quest design)

### Design
- **UI/UX Designer:** 0.5 FTE (new screens, biome themes)
- **Illustrator:** 0.2 FTE (gotchi accessories, new materials)

### Testing
- **QA Tester:** 0.3 FTE (regression, new feature testing)
- **Beta Testers:** 20-50 community members

---

## CONCLUSION

Phase 1 has successfully established the educational foundation with Material Info Cards, Impact Visualization, and Educational Dialogues. Phase 2 should focus on **deepening gameplay engagement** through enhanced mechanics, gotchi interactions, and quest systems, while simultaneously building the **backend infrastructure** needed for social features and cloud persistence.

**Recommended Start:** Sprint 1 - Track A (Gameplay Enhancement)  
**Critical Path:** Backend integration must complete by Sprint 3  
**Success Metric:** 40% increase in average session time

---

**Document Status:** DRAFT v1.0  
**Next Review:** After team discussion  
**Owner:** GameDev Agent (Hermes)
