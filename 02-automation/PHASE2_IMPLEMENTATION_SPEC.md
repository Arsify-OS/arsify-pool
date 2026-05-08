# Phase 2 Implementation Specification

## Sprint 1: Advanced Match Mechanics & Gotchi Feeding

### Feature 1: Special Tile Combos System

**Technical Design:**

```javascript
// Add to CONFIG object (line ~1900)
CONFIG.COMBO_MULTIPLIERS = {
    'bomb_rainbow': 2.5,      // Bomb + Rainbow combo
    'rainbow_rainbow': 3.0,    // Double rainbow
    'bomb_bomb': 2.0,         // Double bomb
    'material_synergy': 1.5    // 3+ of same material in one match
};

// New combo detection in Game class
class Game {
    // ... existing code ...
    
    _detectCombos(matchGroups) {
        const combos = [];
        
        // Check for bomb + rainbow in same match
        matchGroups.forEach(group => {
            const hasBomb = group.some(tile => tile.type === 'bomb');
            const hasRainbow = group.some(tile => tile.type === 'rainbow');
            
            if (hasBomb && hasRainbow) {
                combos.push({
                    type: 'bomb_rainbow',
                    tiles: group,
                    multiplier: CONFIG.COMBO_MULTIPLIERS.bomb_rainbow
                });
            }
        });
        
        return combos;
    }
    
    _processCombos(combos) {
        combos.forEach(combo => {
            // Visual feedback
            this._showComboEffect(combo);
            
            // Score bonus
            const baseScore = combo.tiles.length * CONFIG.SCORE_PER_TILE;
            const bonus = Math.floor(baseScore * (combo.multiplier - 1));
            this.score += bonus;
            
            // Floating text
            this.fct.spawnAtElement(
                document.getElementById('grid'),
                `COMBO! +${bonus}`,
                'combo'
            );
            
            // Sound effect
            window.soundManager?.playCombo?.(combo.type);
        });
    }
}
```

**UI Elements to Add:**
- Combo notification overlay
- Combo multiplier display in game header
- Combo history in stats screen

---

### Feature 2: Gotchi Feeding Mini-game

**Technical Design:**

```javascript
// New FeedingManager class
class FeedingManager {
    constructor(game) {
        this.game = game;
        this.feedingActive = false;
        this.selectedFood = null;
        this.foodPreferences = {
            'organic': ['organic', 'special'],    // Gotchi prefers organic & special
            'recyclable': ['recyclable', 'special'],
            'special': ['special', 'organic'],
            'grime': ['grime', 'recyclable']
        };
    }
    
    startFeeding() {
        this.feedingActive = true;
        this._showFeedingUI();
    }
    
    _showFeedingUI() {
        const modalHTML = `
            <div class="feeding-modal">
                <h3>🍽️ Feed Your Gotchi</h3>
                <p>Select a material to feed:</p>
                <div class="food-options">
                    ${Object.entries(MASTER_ITEMS).map(([id, item]) => `
                        <button class="food-option ${item.type}" 
                                onclick="window.feedingManager.selectFood('${id}')">
                            ${item.icon} ${item.label}
                        </button>
                    `).join('')}
                </div>
                <div class="feeding-preview">
                    <div id="gotchi-feeding-animation"></div>
                    <div id="hunger-restore-preview">+0 Hunger</div>
                </div>
                <div class="feeding-actions">
                    <button onclick="window.feedingManager.cancel()">Cancel</button>
                    <button id="btn-feed" disabled onclick="window.feedingManager.feed()">Feed!</button>
                </div>
            </div>
        `;
        
        this.game.showModal('Feed Gotchi', modalHTML, () => {}, null);
    }
    
    selectFood(foodId) {
        this.selectedFood = foodId;
        const item = MASTER_ITEMS[foodId];
        const gotchiType = this.game.gotchiType || 'organic';
        const preferences = this.foodPreferences[gotchiType];
        
        // Calculate hunger restore
        let baseRestore = 15;
        if (preferences.includes(item.type)) {
            baseRestore = 25; // Preferred food gives more
        }
        
        // Update UI
        document.getElementById('btn-feed').disabled = false;
        document.getElementById('hunger-restore-preview').textContent = 
            `+${baseRestore} Hunger`;
    }
    
    feed() {
        if (!this.selectedFood) return;
        
        const item = MASTER_ITEMS[this.selectedFood];
        const gotchiType = this.game.gotchiType || 'organic';
        const preferences = this.foodPreferences[gotchiType];
        
        // Calculate restore
        let restore = 15;
        if (preferences.includes(item.type)) {
            restore = 25;
            this.game._gotchiSay('happy');
        } else {
            this.game._gotchiSay('neutral');
        }
        
        // Apply restore
        this.game.gotchiHunger = Math.min(100, this.game.gotchiHunger + restore);
        this.game._updateHungerUI();
        
        // Animation
        this._playFeedingAnimation(item.icon);
        
        // Close modal
        this.game.hideModal();
        this.feedingActive = false;
        
        // Save state
        this.game.saveGameState();
    }
}
```

**UI Requirements:**
- Feeding modal with material selection grid
- Gotchi animation during feeding
- Hunger bar visual update
- Food preference indicators

---

### Feature 3: New Material Types (E-Waste & Textile)

**Technical Design:**

```javascript
// Add to MASTER_ITEMS (line ~1800)
MASTER_ITEMS['ewaste'] = {
    id: 'ewaste',
    label: 'E-Waste',
    icon: '🖥️',
    type: 'ewaste',
    desc: 'Electronic waste containing valuable metals and toxic materials.',
    co2_factor: 8.5,
    rarity: 'rare'
};

MASTER_ITEMS['textile'] = {
    id: 'textile',
    label: 'Textile',
    icon: '👕',
    type: 'textile',
    desc: 'Clothing and fabric waste that can be upcycled or recycled.',
    co2_factor: 3.2,
    rarity: 'uncommon'
};

// Add to EDUCATIONAL_FACTS
EDUCATIONAL_FACTS.ewaste = {
    processingSteps: [
        'Collection at e-waste centers',
        'Manual disassembly',
        'Component separation',
        'Metal extraction',
        'Safe disposal of toxins'
    ],
    energySaved: 95, // kWh per kg
    waterSaved: 5000, // L per ton
    funFact: 'Recycling 1 million laptops saves energy equal to 3,500 US homes for a year!'
};

EDUCATIONAL_FACTS.textile = {
    processingSteps: [
        'Sorting by material type',
        'Shredding into fibers',
        'Cleaning and carding',
        'Spinning into new yarn',
        'Weaving/knitting new fabric'
    ],
    energySaved: 60, // kWh per kg
    waterSaved: 7000, // L per ton
    funFact: 'It takes 2,700 liters of water to make one cotton t-shirt!'
};

// Add to tile type system
CONFIG.TILE_TYPES.push('ewaste', 'textile');

// Add sound profiles to ASMRSoundEngine
class ASMRSoundEngine {
    // ... existing code ...
    
    playEwasteTap(volume = 0.6) {
        // Digital glitch + metallic click
        const t = this.ctx.currentTime;
        
        // Digital glitch noise
        const glitch = this._noise(0.08, 'white');
        const gFilt = this._filter('bandpass', 3000, 5);
        const gGain = this._gain(0);
        gGain.gain.setValueAtTime(volume * 0.4, t);
        gGain.gain.exponentialRampToValueAtTime(0.001, t + 0.08);
        
        // Metallic click
        const click = this._node('square', 1200);
        const cGain = this._gain(0);
        cGain.gain.setValueAtTime(volume * 0.3, t);
        cGain.gain.exponentialRampToValueAtTime(0.001, t + 0.05);
        
        this._connect(glitch, gFilt, gGain);
        this._connect(click, cGain);
        
        glitch.start(t); glitch.stop(t + 0.08);
        click.start(t); click.stop(t + 0.05);
    }
    
    playTextileTap(volume = 0.55) {
        // Fabric rustle + soft thud
        const t = this.ctx.currentTime;
        
        // Fabric rustle (filtered pink noise)
        const rustle = this._noise(0.12, 'pink');
        const rFilt = this._filter('lowpass', 1200, 2);
        const rGain = this._gain(0);
        rGain.gain.setValueAtTime(volume * 0.5, t);
        rGain.gain.exponentialRampToValueAtTime(0.001, t + 0.12);
        
        // Soft thud
        const thud = this._node('sine', 180);
        const tGain = this._gain(0);
        tGain.gain.setValueAtTime(volume * 0.2, t);
        tGain.gain.exponentialRampToValueAtTime(0.001, t + 0.1);
        
        this._connect(rustle, rFilt, rGain);
        this._connect(thud, tGain);
        
        rustle.start(t); rustle.stop(t + 0.12);
        thud.start(t); thud.stop(t + 0.1);
    }
}
```

**Visual Assets Needed:**
- SVG icons for e-waste (🖥️) and textile (👕)
- Tile color gradients (tech blue for e-waste, fabric beige for textile)
- Match particle effects

---

## Sprint 2: Quest System & Biome Implementation

### Feature 4: Quest & Mission System

**Technical Design:**

```javascript
// QuestManager class
class QuestManager {
    constructor(game) {
        this.game = game;
        this.activeQuests = [];
        this.completedQuests = [];
        this.dailyRefreshTime = '00:00'; // Midnight refresh
        
        this.loadQuests();
        this.startQuestChecker();
    }
    
    loadQuests() {
        const saved = localStorage.getItem('upshalter_quests');
        if (saved) {
            const data = JSON.parse(saved);
            this.activeQuests = data.active || [];
            this.completedQuests = data.completed || [];
        } else {
            this.generateDailyQuests();
        }
    }
    
    generateDailyQuests() {
        const templates = [
            {
                id: 'match_organic_50',
                title: 'Organic Farmer',
                description: 'Match 50 organic materials',
                type: 'match_count',
                target: { material: 'organic', count: 50 },
                reward: { coins: 100, xp: 50 },
                progress: 0
            },
            {
                id: 'complete_levels_3',
                title: 'Level Explorer',
                description: 'Complete 3 levels',
                type: 'level_complete',
                target: { count: 3 },
                reward: { coins: 150, xp: 75 },
                progress: 0
            },
            {
                id: 'feed_gotchi_1',
                title: 'Gotchi Caretaker',
                description: 'Feed your gotchi once',
                type: 'gotchi_feed',
                target: { count: 1 },
                reward: { coins: 50, item: 'gotchi_hat' },
                progress: 0
            }
        ];
        
        this.activeQuests = templates;
        this.saveQuests();
    }
    
    updateQuestProgress(eventType, data) {
        this.activeQuests.forEach(quest => {
            switch(quest.type) {
                case 'match_count':
                    if (data.material === quest.target.material) {
                        quest.progress += data.count;
                    }
                    break;
                    
                case 'level_complete':
                    quest.progress += 1;
                    break;
                    
                case 'gotchi_feed':
                    quest.progress = data.fed ? 1 : 0;
                    break;
            }
            
            // Check completion
            if (quest.progress >= quest.target.count) {
                this.completeQuest(quest.id);
            }
        });
        
        this.saveQuests();
        this.updateQuestUI();
    }
    
    completeQuest(questId) {
        const quest = this.activeQuests.find(q => q.id === questId);
        if (!quest) return;
        
        // Move to completed
        this.activeQuests = this.activeQuests.filter(q => q.id !== questId);
        this.completedQuests.push({
            ...quest,
            completedAt: new Date().toISOString()
        });
        
        // Give rewards
        this._giveRewards(quest.reward);
        
        // Show completion notification
        this.game.showModal(
            '🎉 Quest Complete!',
            `You completed "${quest.title}" and earned ${quest.reward.coins} coins!`,
            () => {},
            null
        );
        
        this.saveQuests();
    }
    
    _giveRewards(reward) {
        // Add coins
        this.game.coins += reward.coins || 0;
        
        // Add XP
        this.game.xp += reward.xp || 0;
        
        // Add item if present
        if (reward.item) {
            this.game.unlockItem(reward.item);
        }
        
        this.game.saveGameState();
    }
}
```

**UI Screens Needed:**
- Quest log screen showing active/completed quests
- Quest progress indicators in game header
- Quest completion popups
- Daily quest refresh timer

---

### Feature 5: Biome System (Forest & Ocean)

**Technical Design:**

```javascript
// Biome configuration
const BIOMES = {
    forest: {
        name: 'Forest',
        description: 'Lush green forest with organic focus',
        background: 'linear-gradient(160deg, #1B5E20 0%, #4CAF50 60%, #A5D6A7 100%)',
        tilePalette: {
            organic: '#81C784',
            recyclable: '#A5D6A7',
            special: '#FFD54F',
            grime: '#8D6E63',
            ewaste: '#64B5F6',
            textile: '#F48FB1'
        },
        particleTheme: 'leaves',
        ambientSound: 'forest_ambient',
        gotchiVariant: 'forest'
    },
    
    ocean: {
        name: 'Ocean',
        description: 'Deep blue ocean with marine conservation focus',
        background: 'linear-gradient(160deg, #01579B 0%, #0288D1 60%, #4FC3F7 100%)',
        tilePalette: {
            organic: '#4DD0E1',      // Seaweed green-blue
            recyclable: '#80DEEA',   // Light ocean blue
            special: '#FFD740',      // Sun yellow
            grime: '#78909C',        // Stormy gray
            ewaste: '#B39DDB',       // Purple coral
            textile: '#FFAB91'       // Pink coral
        },
        particleTheme: 'bubbles',
        ambientSound: 'ocean_waves',
        gotchiVariant: 'ocean'
    }
};

// BiomeManager class
class BiomeManager {
    constructor(game) {
        this.game = game;
        this.currentBiome = 'forest';
        this.unlockedBiomes = new Set(['forest']); // Start with forest
        
        this.loadBiomeState();
    }
    
    setBiome(biomeId) {
        if (!this.unlockedBiomes.has(biomeId)) {
            console.warn(`Biome ${biomeId} not unlocked`);
            return;
        }
        
        this.currentBiome = biomeId;
        this.applyBiomeVisuals();
        this.saveBiomeState();
    }
    
    applyBiomeVisuals() {
        const biome = BIOMES[this.currentBiome];
        if (!biome) return;
        
        // Update game container background
        const container = document.getElementById('game-container');
        if (container) {
            container.style.background = biome.background;
        }
        
        // Update tile colors via CSS variables
        Object.entries(biome.tilePalette).forEach(([type, color]) => {
            document.documentElement.style.setProperty(
                `--tile-${type}`,
                color
            );
        });
        
        // Update particle theme
        this.game.particles.setTheme(biome.particleTheme);
        
        // Update gotchi variant
        this.game.setGotchiVariant(biome.gotchiVariant);
        
        // Play ambient sound
        window.soundManager?.playAmbient?.(biome.ambientSound);
    }
    
    unlockBiome(biomeId) {
        this.unlockedBiomes.add(biomeId);
        
        // Show unlock notification
        this.game.showModal(
            '🌊 New Biome Unlocked!',
            `You've unlocked the ${BIOMES[biomeId].name} biome!`,
            () => {},
            null
        );
        
        this.saveBiomeState();
    }
}
```

**Unlock Conditions:**
- Forest: Default (unlocked from start)
- Ocean: Complete level 10 + match 100 recyclable materials

**Visual Requirements:**
- Biome selection screen
- Biome-specific background images/patterns
- Custom particle effects per biome
- Gotchi visual variants per biome

---

## Sprint 3: Backend Integration

### Feature 6: Supabase API Integration

**Technical Design:**

```javascript
// APIClient class
class APIClient {
    constructor() {
        this.supabaseUrl = 'https://your-project.supabase.co';
        this.supabaseKey = 'your-anon-key';
        this.headers = {
            'apikey': this.supabaseKey,
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.supabaseKey}`
        };
    }
    
    async getLevels() {
        try {
            const response = await fetch(
                `${this.supabaseUrl}/rest/v1/levels?select=*`,
                { headers: this.headers }
            );
            
            if (!response.ok) throw new Error('Failed to fetch levels');
            
            const levels = await response.json();
            
            // Transform to game format
            return levels.map(level => ({
                id: level.id,
                name: level.name,
                moves: level.moves,
                target: level.target_score,
                layout: level.layout,
                description: level.description,
                difficulty: level.difficulty
            }));
        } catch (error) {
            console.error('Failed to load levels from API:', error);
            return null; // Fallback to local levels
        }
    }
    
    async saveGameState(userId, state) {
        if (!userId) {
            console.warn('No user ID, saving locally');
            return this._saveLocal(state);
        }
        
        try {
            const response = await fetch(
                `${this.supabaseUrl}/rest/v1/game_states`,
                {
                    method: 'POST',
                    headers: this.headers,
                    body: JSON.stringify({
                        user_id: userId,
                        state: state,
                        updated_at: new Date().toISOString()
                    })
                }
            );
            
            if (!response.ok) throw new Error('Failed to save game state');
            
            console.log('Game state saved to cloud');
            return true;
        } catch (error) {
            console.error('Cloud save failed:', error);
            return this._saveLocal(state);
        }
    }
    
    async getEvolutionStages() {
        try {
            const response = await fetch(
                `${this.supabaseUrl}/rest/v1/gotchi_stages?select=*&order=stage_order`,
                { headers: this.headers }
            );
            
            if (!response.ok) throw new Error('Failed to fetch evolution stages');
            
            const stages = await response.json();
            
            // Transform to game format
            return stages.reduce((acc, stage) => {
                acc[stage.stage_name] = {
                    threshold: stage.match_threshold,
                    visual: stage.visual_data,
                    abilities: stage.abilities || []
                };
                return acc;
            }, {});
        } catch (error) {
            console.error('Failed to load evolution stages:', error);
            return null; // Fallback to local stages
        }
    }
    
    _saveLocal(state) {
        localStorage.setItem('upshalter_game_state', JSON.stringify(state));
        return true;
    }
}
```

**Database Schema (Supabase):**

```sql
-- Levels table
CREATE TABLE levels (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    moves INTEGER NOT NULL,
    target_score INTEGER NOT NULL,
    layout JSONB NOT NULL,
    description TEXT,
    difficulty TEXT DEFAULT 'normal',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Game states table
CREATE TABLE game_states (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    state JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Gotchi evolution stages
CREATE TABLE gotchi_stages (
    id SERIAL PRIMARY KEY,
    stage_name TEXT NOT NULL,
    stage_order INTEGER NOT NULL,
    match_threshold INTEGER NOT NULL,
    visual_data JSONB NOT NULL,
    abilities JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Leaderboard entries
CREATE TABLE leaderboard_entries (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    level_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    username TEXT,
    country_code TEXT,
    submitted_at TIMESTAMP DEFAULT NOW()
);
```

**Migration Strategy:**
1. Deploy Supabase project
2. Create tables with sample data
3. Implement APIClient with fallback to local storage
4. Gradually migrate features to use API
5. Add real-time subscriptions for multiplayer features

---

## Development Timeline & Milestones

### Week 1-2: Sprint 1 Implementation
**Goal:** Advanced gameplay mechanics

**Tasks:**
1. Implement combo detection system
2. Create feeding mini-game UI
3. Add e-waste and textile materials
4. Integrate new sound profiles
5. Test and balance new mechanics

**Success Criteria:**
- Combo system working with visual feedback
- Feeding mini-game functional
- New materials appear in game
- No performance regression

### Week 3-4: Sprint 2 Implementation  
**Goal:** Content expansion

**Tasks:**
1. Build quest system with UI
2. Implement biome switching
3. Create ocean biome visuals
4. Add quest tracking to game events
5. Design and implement unlock conditions

**Success Criteria:**
- Daily quests refresh correctly
- Biome switching works smoothly
- Quest progress tracked accurately
- Rewards distributed properly

### Week 5-6: Sprint 3 Implementation
**Goal:** Backend integration

**Tasks:**
1. Set up Supabase project
2. Implement APIClient with fallbacks
3. Migrate level data to API
4. Implement cloud save/load
5. Add evolution stages API

**Success Criteria:**
- Game loads levels from API
- Cloud save works with offline fallback
- No data loss during migration
- API errors handled gracefully

### Week 7-8: Polish & Testing
**Goal:** Production readiness

**Tasks:**
1. Performance optimization
2. Cross-browser testing
3. Mobile responsiveness testing
4. Bug fixing
5. User acceptance testing

**Success Criteria:**
- All features work on mobile/desktop
- No critical bugs
- Performance metrics met
- Ready for production deployment

---

## Risk Mitigation Plan

### Technical Risks
1. **File Size Bloat**
   - Monitor bundle size after each feature
   - Consider code splitting if >500KB
   - Use lazy loading for biome assets

2. **State Management Complexity**
   - Keep state updates atomic
   - Add comprehensive logging for debugging
   - Implement state validation

3. **Backend Integration Failures**
   - Build robust fallback mechanisms
   - Implement retry logic with exponential backoff
   - Cache API responses locally

### Product Risks
1. **Feature Overload**
   - Weekly playtesting with new users
   - A/B test new features
   - Be prepared to cut features if confusing

2. **Balance Issues**
   - Mathematical modeling of new mechanics
   - Extensive playtesting for tuning
   - Hotfix capability for balance patches

---

## Quality Assurance Checklist

### Before Each Release
- [ ] All new features tested on Chrome, Firefox, Safari
- [ ] Mobile touch interactions verified
- [ ] Performance metrics recorded (FPS, load time)
- [ ] Sound effects working on all devices
- [ ] No console errors or warnings
- [ ] Game state persists correctly
- [ ] All buttons/controls accessible
- [ ] No memory leaks detected

### User Experience
- [ ] New features have clear tutorials
- [ ] Error messages are user-friendly
- [ ] Loading states are shown appropriately
- [ ] Visual feedback is immediate and clear
- [ ] Sound design supports gameplay

### Accessibility
- [ ] Screen reader compatibility tested
- [ ] Color contrast ratios meet WCAG standards
- [ ] Keyboard navigation works for all features
- [ ] Text sizes adjustable via browser zoom

---

## Deployment Strategy

### Staging Environment
- Deploy to https://staging.regrow.upshalter.com
- Use separate Supabase project for testing
- Enable detailed logging and analytics

### Production Deployment
1. Deploy code changes (auto-deploy via regrow-watcher.service)
2. Run database migrations
3. Enable new features via feature flags
4. Monitor error rates and performance
5. Roll back if issues detected

### Monitoring
- Real-time error tracking (Sentry)
- Performance monitoring (Lighthouse)
- User behavior analytics (Amplitude)
- Server response times (Supabase dashboard)

---

## Success Metrics for Phase 2

### Quantitative Metrics
- **Session Length:** Increase from 8min to 15min average
- **Daily Active Users:** 20% increase
- **Quest Completion Rate:** >60% of daily quests completed
- **Biome Engagement:** 40% of players unlock ocean biome
- **Retention:** Day 30 retention >25%

### Qualitative Metrics
- User feedback on new mechanics
- Community engagement on social features
- Educational content effectiveness
- Overall game "fun factor" rating

---

## Next Steps

### Immediate (Today)
1. Review this spec with development team
2. Create GitHub issues for each feature
3. Set up development branches
4. Begin Sprint 1 implementation

### This Week
1. Start implementing combo system
2. Design feeding UI mockups
3. Create e-waste and textile assets
4. Set up Supabase project

### Ongoing
- Daily standups to track progress
- Weekly playtesting sessions
- Bi-weekly stakeholder reviews
- Continuous integration/deployment

---

**Document Status:** READY FOR IMPLEMENTATION  
**Version:** 1.0  
**Last Updated:** 2026-05-04  
**Owner:** GameDev Agent
