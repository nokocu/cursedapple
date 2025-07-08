// main frontend application - typescript
import { 
    Patch, 
    PatchDetails, 
    Hero, 
    SearchResult, 
    SearchFilters, 
    ChangeType, 
    ViewType,
    HeroChange,
    ItemChange 
} from './types.js';

class DeadlockPatchNotesApp {
    private readonly apiBase = 'http://localhost:3000/api';
    private currentView: ViewType = 'patches';
    private patches: Patch[] = [];
    private searchFilters: SearchFilters = {};
    private debounceTimeout: number | null = null;

    constructor() {
        this.init();
    }

    private async init() {
        this.setupEventListeners();
        await this.loadPatches();
        this.renderPatchList();
    }

    private setupEventListeners() {
        // search functionality
        const searchInput = document.getElementById('search-input') as HTMLInputElement;
        const heroFilter = document.getElementById('hero-filter') as HTMLSelectElement;
        const itemFilter = document.getElementById('item-filter') as HTMLSelectElement;
        const changeTypeFilter = document.getElementById('change-type-filter') as HTMLSelectElement;

        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchFilters.text = (e.target as HTMLInputElement).value;
                this.debounceSearch();
            });
        }

        if (heroFilter) {
            heroFilter.addEventListener('change', (e) => {
                this.searchFilters.hero = (e.target as HTMLSelectElement).value;
                this.performSearch();
            });
        }

        if (itemFilter) {
            itemFilter.addEventListener('change', (e) => {
                this.searchFilters.item = (e.target as HTMLSelectElement).value;
                this.performSearch();
            });
        }

        if (changeTypeFilter) {
            changeTypeFilter.addEventListener('change', (e) => {
                this.searchFilters.change_type = (e.target as HTMLSelectElement).value as ChangeType;
                this.performSearch();
            });
        }

        // tab switching
        document.querySelectorAll('.tab[data-view]').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                const target = (e.target as HTMLElement).dataset.view;
                if (target) this.switchView(target);
            });
        });
    }

    private debounceSearch(): void {
        if (this.debounceTimeout) clearTimeout(this.debounceTimeout);
        this.debounceTimeout = window.setTimeout(() => this.performSearch(), 300);
    }

    private async performSearch(): Promise<void> {
        if (Object.keys(this.searchFilters).length === 0) {
            this.renderPatchList();
            return;
        }

        try {
            const params = new URLSearchParams();
            Object.entries(this.searchFilters).forEach(([key, value]) => {
                if (value) params.append(key, value as string);
            });

            const response = await fetch(`${this.apiBase}/search?${params}`);
            const results: SearchResult[] = await response.json();
            this.renderSearchResults(results);
        } catch (error) {
            console.error('search failed:', error);
        }
    }

    private async loadPatches(): Promise<void> {
        try {
            const response = await fetch(`${this.apiBase}/patches`);
            this.patches = await response.json();
        } catch (error) {
            console.error('failed to load patches:', error);
        }
    }

    private async loadPatchDetails(patchId: number): Promise<PatchDetails | null> {
        try {
            const response = await fetch(`${this.apiBase}/patches/${patchId}`);
            return await response.json();
        } catch (error) {
            console.error('failed to load patch details:', error);
            return null;
        }
    }

    private switchView(view: string): void {
        this.currentView = view as ViewType;
        
        // update active tab
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('tab-on');
            tab.classList.add('tab');
        });
        
        const activeTab = document.querySelector(`[data-view="${view}"]`);
        if (activeTab) {
            activeTab.classList.add('tab-on');
            activeTab.classList.remove('tab');
        }

        // render appropriate content
        switch (view) {
            case 'patches':
                this.renderPatchList();
                break;
            case 'heroes':
                this.loadAndRenderHeroes();
                break;
            case 'items':
                this.loadAndRenderItems();
                break;
            case 'analytics':
                this.loadAndRenderAnalytics();
                break;
        }
    }

    private renderPatchList() {
        const container = document.getElementById('content-container');
        if (!container) return;

        const html = `
            <div class="allposts-container">
                ${this.patches.map(patch => this.renderPatchCard(patch)).join('')}
            </div>
        `;
        
        container.innerHTML = html;

        // add click handlers for patch cards
        document.querySelectorAll('.patch-card').forEach(card => {
            card.addEventListener('click', async (e) => {
                const patchId = (e.currentTarget as HTMLElement).dataset.patchId;
                if (patchId) await this.showPatchDetails(parseInt(patchId));
            });
        });
    }

    private renderPatchCard(patch: any): string {
        const thumbNum = patch.id % 10;
        const date = new Date(patch.release_date);
        
        return `
            <div class="post patch-card" data-patch-id="${patch.id}">
                <div class="post-pic">
                    <img src="/static/assets/thumbs/posta${thumbNum}.png" alt="patch thumbnail">
                    <div class="post-pic-lines">
                        <span class="post-pic-text-a">${date.toLocaleDateString()}</span>
                        <span class="post-pic-text-b">UPDATE</span>
                    </div>
                </div>
                <div class="post-notes">
                    <span class="post-date-text">posted ${date.toLocaleDateString()}</span><br>
                    <span class="post-title-text">patchnotes for <b>${patch.version}</b></span><br>
                    
                    ${patch.heroes_affected > 0 ? `
                        <span class="post-info-text">
                            <img class="change" src="/static/assets/hero2.png" height="16" width="16">
                            <b>${patch.heroes_affected}</b> heroes
                        </span>
                    ` : ''}
                    
                    ${patch.items_affected > 0 ? `
                        <span class="post-info-text">
                            <img class="change" src="/static/assets/item.png" height="16" width="16">
                            <b>${patch.items_affected}</b> items
                        </span>
                    ` : ''}
                    
                    <div class="change-summary">
                        <span class="change-count buff-count">${patch.buffs} buffs</span>
                        <span class="change-count nerf-count">${patch.nerfs} nerfs</span>
                        <span class="change-count other-count">${patch.other_changes} other</span>
                    </div>
                </div>
            </div>
        `;
    }

    private async showPatchDetails(patchId: number) {
        const details = await this.loadPatchDetails(patchId);
        if (!details) return;

        const modal = this.createModal();
        modal.innerHTML = `
            <div class="modal-content patch-details">
                <div class="modal-header">
                    <h2>${details.patch.version}</h2>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    ${this.renderPatchChanges(details)}
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        
        // close modal handlers
        modal.querySelector('.modal-close')?.addEventListener('click', () => {
            document.body.removeChild(modal);
        });
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) document.body.removeChild(modal);
        });
    }

    private renderPatchChanges(details: any): string {
        const groupedHeroChanges = this.groupChangesByType(details.hero_changes, 'hero_name');
        const groupedItemChanges = this.groupChangesByCategory(details.item_changes);

        return `
            ${Object.keys(groupedHeroChanges).length > 0 ? `
                <div class="changes-section">
                    <h3>hero changes</h3>
                    ${Object.entries(groupedHeroChanges).map(([hero, changes]: [string, any]) => `
                        <div class="hero-changes">
                            <h4 class="hero-name" style="color: var(--${hero.replace(' ', '-')})">${hero}</h4>
                            ${this.renderChangesList(changes)}
                        </div>
                    `).join('')}
                </div>
            ` : ''}
            
            ${Object.keys(groupedItemChanges).length > 0 ? `
                <div class="changes-section">
                    <h3>item changes</h3>
                    ${Object.entries(groupedItemChanges).map(([category, items]: [string, any]) => `
                        <div class="category-changes">
                            <h4 class="category-name" style="color: var(--${category.toLowerCase()})">${category}</h4>
                            ${Object.entries(items).map(([item, changes]: [string, any]) => `
                                <div class="item-changes">
                                    <h5 class="item-name">${item}</h5>
                                    ${this.renderChangesList(changes)}
                                </div>
                            `).join('')}
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        `;
    }

    private groupChangesByType(changes: any[], nameField: string): any {
        const grouped: any = {};
        changes.forEach(change => {
            const name = change[nameField];
            if (!grouped[name]) grouped[name] = { buff: [], nerf: [], other: [] };
            grouped[name][change.change_type].push(change);
        });
        return grouped;
    }

    private groupChangesByCategory(changes: any[]): any {
        const grouped: any = {};
        changes.forEach(change => {
            const category = change.item_category;
            const item = change.item_name;
            
            if (!grouped[category]) grouped[category] = {};
            if (!grouped[category][item]) grouped[category][item] = { buff: [], nerf: [], other: [] };
            grouped[category][item][change.change_type].push(change);
        });
        return grouped;
    }

    private renderChangesList(changes: any): string {
        const types = ['buff', 'nerf', 'other'];
        return types.map(type => {
            if (changes[type].length === 0) return '';
            return `
                <div class="change-type-group ${type}">
                    ${changes[type].map((change: any) => `
                        <div class="change-item ${type}">
                            ${change.description.replace(/^- /, '')}
                        </div>
                    `).join('')}
                </div>
            `;
        }).join('');
    }

    private renderSearchResults(results: any[]) {
        const container = document.getElementById('content-container');
        if (!container) return;

        if (results.length === 0) {
            container.innerHTML = '<div class="no-results">no changes found</div>';
            return;
        }

        const html = `
            <div class="search-results">
                <h3>search results (${results.length})</h3>
                ${results.map(result => this.renderSearchResult(result)).join('')}
            </div>
        `;
        
        container.innerHTML = html;
    }

    private renderSearchResult(result: any): string {
        const entityName = result.hero_name || result.item_name || 'general';
        const entityType = result.hero_name ? 'hero' : result.item_name ? 'item' : 'general';
        
        return `
            <div class="search-result change-item ${result.change_type}">
                <div class="result-header">
                    <span class="entity-name ${entityType}">${entityName}</span>
                    <span class="patch-version">${result.version}</span>
                    <span class="change-type ${result.change_type}">${result.change_type}</span>
                </div>
                <div class="result-description">${result.description}</div>
            </div>
        `;
    }

    private async loadAndRenderHeroes() {
        try {
            const response = await fetch(`${this.apiBase}/heroes`);
            const heroes = await response.json();
            this.renderHeroStats(heroes);
        } catch (error) {
            console.error('failed to load heroes:', error);
        }
    }

    private renderHeroStats(heroes: any[]) {
        const container = document.getElementById('content-container');
        if (!container) return;

        const html = `
            <div class="hero-stats">
                <h2>hero statistics</h2>
                <div class="hero-grid">
                    ${heroes.map(hero => this.renderHeroCard(hero)).join('')}
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }

    private renderHeroCard(hero: any): string {
        const totalChanges = hero.total_changes || 0;
        const balanceScore = (hero.buffs || 0) - (hero.nerfs || 0);
        
        return `
            <div class="hero-card" style="border-color: var(--${hero.name.replace(' ', '-')})">
                <div class="hero-header">
                    <h3 class="hero-name" style="color: var(--${hero.name.replace(' ', '-')})">${hero.name}</h3>
                    <div class="balance-score ${balanceScore > 0 ? 'positive' : balanceScore < 0 ? 'negative' : 'neutral'}">
                        ${balanceScore > 0 ? '+' : ''}${balanceScore}
                    </div>
                </div>
                <div class="hero-abilities">
                    ${[hero.ability1, hero.ability2, hero.ability3, hero.ability4]
                        .filter(ability => ability)
                        .map(ability => `<span class="ability">${ability}</span>`)
                        .join('')}
                </div>
                <div class="hero-changes">
                    <span class="change-stat buff">${hero.buffs || 0} buffs</span>
                    <span class="change-stat nerf">${hero.nerfs || 0} nerfs</span>
                    <span class="change-stat other">${hero.other_changes || 0} other</span>
                </div>
            </div>
        `;
    }

    private async loadAndRenderItems() {
        // implementation for items view
        const container = document.getElementById('content-container');
        if (!container) return;
        container.innerHTML = '<div class="loading">loading items...</div>';
    }

    private async loadAndRenderAnalytics() {
        // implementation for analytics view
        const container = document.getElementById('content-container');
        if (!container) return;
        container.innerHTML = '<div class="loading">loading analytics...</div>';
    }

    private createModal(): HTMLElement {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        return modal;
    }
}

// initialize app when dom is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DeadlockPatchNotesApp();
});
