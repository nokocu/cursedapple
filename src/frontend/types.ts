// Type definitions for the application
export interface Patch {
    id: number;
    version: string;
    release_date: string;
    total_changes: number;
    buffs: number;
    nerfs: number;
    other_changes: number;
    heroes_affected: number;
    items_affected: number;
    media_count: number;
}

export interface PatchDetails {
    patch: {
        id: number;
        version: string;
        release_date: string;
        processed: number;
    };
    hero_changes: HeroChange[];
    item_changes: ItemChange[];
    general_changes: GeneralChange[];
    media: MediaFile[];
}

export interface HeroChange {
    hero_name: string;
    change_type: ChangeType;
    description: string;
    id: number;
}

export interface ItemChange {
    item_name: string;
    item_category: ItemCategory;
    change_type: ChangeType;
    description: string;
    id: number;
}

export interface GeneralChange {
    change_type: ChangeType;
    description: string;
    category: string | null;
    id: number;
}

export interface MediaFile {
    media_type: string;
    file_path: string;
    description: string;
    id: number;
}

export interface Hero {
    name: string;
    ability1: string;
    ability2: string;
    ability3: string;
    ability4: string;
    total_changes: number;
    buffs: number;
    nerfs: number;
    other_changes: number;
}

export interface SearchResult {
    id: number;
    patch_id: number;
    version: string;
    change_type: ChangeType;
    description: string;
    hero_name: string | null;
    item_name: string | null;
    item_category: ItemCategory | null;
}

export interface SearchFilters {
    text?: string;
    hero?: string;
    item?: string;
    change_type?: ChangeType;
}

export type ChangeType = 'buff' | 'nerf' | 'other';
export type ItemCategory = 'Weapon' | 'Spirit' | 'Vitality';
export type ViewType = 'patches' | 'heroes' | 'items' | 'analytics';
