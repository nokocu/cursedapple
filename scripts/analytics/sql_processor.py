# sql-based patch processor
import sqlite3
import re
import json
from datetime import datetime

class PatchProcessor:
    def __init__(self, db_path="patch.db"):
        self.db_path = db_path
        self.buff_words = ["increased", "improved", "now grants", "now has"]
        self.nerf_words = ["reduced", "no longer grants", "decreased"]
        self.other_words = ["vfx", "sfx", "sound", "animation", "visual", "fixed"]

    def get_heroes_and_items(self):
        """fetch heroes and items from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # get heroes with abilities
            cursor.execute("SELECT id, name, ability1, ability2, ability3, ability4 FROM heroes")
            heroes = {}
            for row in cursor.fetchall():
                hero_id, name = row[0], row[1]
                abilities = [ability for ability in row[2:] if ability]
                heroes[name.lower()] = {"id": hero_id, "abilities": abilities}
            
            # get items by category
            cursor.execute("SELECT id, name, category FROM items")
            items = {}
            for item_id, name, category in cursor.fetchall():
                if category not in items:
                    items[category] = {}
                items[category][name.lower()] = {"id": item_id, "name": name}
            
            return heroes, items

    def classify_change_type(self, text):
        """determine if change is buff, nerf, or other"""
        text_lower = text.lower()
        
        # check for visual/audio changes first
        if any(word in text_lower for word in self.other_words):
            return "other"
        
        # analyze cooldown changes
        if "cooldown" in text_lower or "cd" in text_lower:
            time_values = re.findall(r"-?\d+\.?\d*s?", text)
            if len(time_values) >= 2:
                try:
                    first = float(time_values[0].replace('s', ''))
                    second = float(time_values[1].replace('s', ''))
                    return "nerf" if first < second else "buff"
                except ValueError:
                    pass
        
        # check buff/nerf keywords
        if any(word in text_lower for word in self.buff_words):
            return "buff"
        elif any(word in text_lower for word in self.nerf_words):
            return "nerf"
        
        return "other"

    def find_hero_or_item(self, text, heroes, items):
        """identify if text mentions a hero or item"""
        text_lower = text.lower()
        
        # check for explicit format (name:)
        for hero_name, hero_data in heroes.items():
            if f"{hero_name}:" in text_lower:
                return "hero", hero_data["id"], hero_name
        
        for category, category_items in items.items():
            for item_name, item_data in category_items.items():
                if f"{item_name}:" in text_lower:
                    return "item", item_data["id"], item_data["name"]
        
        # check for general mentions
        for hero_name, hero_data in heroes.items():
            if hero_name in text_lower:
                # check abilities too
                for ability in hero_data["abilities"]:
                    if ability and ability.lower() in text_lower:
                        return "hero", hero_data["id"], hero_name
                if hero_name in text_lower:
                    return "hero", hero_data["id"], hero_name
        
        for category, category_items in items.items():
            for item_name, item_data in category_items.items():
                if item_name in text_lower:
                    return "item", item_data["id"], item_data["name"]
        
        return None, None, None

    def process_patch_content(self, patch_id):
        """process raw patch content into structured changes"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # get patch content
            cursor.execute("SELECT raw_content FROM patches WHERE id = ?", (patch_id,))
            result = cursor.fetchone()
            if not result or not result[0]:
                return False
            
            content = result[0]
            heroes, items = self.get_heroes_and_items()
            
            # clear existing changes for this patch
            cursor.execute("DELETE FROM patch_changes WHERE patch_id = ?", (patch_id,))
            cursor.execute("DELETE FROM patch_media WHERE patch_id = ?", (patch_id,))
            
            changes_added = 0
            media_added = 0
            
            # process each line
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                
                # remove html tags
                clean_line = re.sub(r'<.*?>', '', line).strip()
                if not clean_line:
                    continue
                
                # handle media files
                if clean_line.endswith(('.mp4', '.jpg', '.png', '.gif')):
                    media_type = "video" if clean_line.endswith('.mp4') else "image"
                    cursor.execute("""
                        INSERT INTO patch_media (patch_id, media_type, file_path)
                        VALUES (?, ?, ?)
                    """, (patch_id, media_type, clean_line))
                    media_added += 1
                    continue
                
                # handle image src tags
                src_match = re.search(r'src="([^"]+)"', line)
                if src_match:
                    cursor.execute("""
                        INSERT INTO patch_media (patch_id, media_type, file_path)
                        VALUES (?, ?, ?)
                    """, (patch_id, "image", src_match.group(1)))
                    media_added += 1
                    continue
                
                # skip category headers
                if clean_line.startswith('[') and clean_line.endswith(']'):
                    continue
                
                # process actual changes
                entity_type, entity_id, entity_name = self.find_hero_or_item(clean_line, heroes, items)
                change_type = self.classify_change_type(clean_line)
                
                if entity_type == "hero":
                    cursor.execute("""
                        INSERT INTO patch_changes (patch_id, hero_id, change_type, description)
                        VALUES (?, ?, ?, ?)
                    """, (patch_id, entity_id, change_type, clean_line))
                    changes_added += 1
                
                elif entity_type == "item":
                    cursor.execute("""
                        INSERT INTO patch_changes (patch_id, item_id, change_type, description)
                        VALUES (?, ?, ?, ?)
                    """, (patch_id, entity_id, change_type, clean_line))
                    changes_added += 1
                
                else:
                    # general change
                    cursor.execute("""
                        INSERT INTO patch_changes (patch_id, change_type, description, category)
                        VALUES (?, ?, ?, ?)
                    """, (patch_id, change_type, clean_line, "general"))
                    changes_added += 1
            
            # mark patch as processed
            cursor.execute("UPDATE patches SET processed = TRUE WHERE id = ?", (patch_id,))
            conn.commit()
            
            print(f"✓ patch {patch_id}: {changes_added} changes, {media_added} media files")
            return True

    def get_patch_summary(self, patch_id):
        """get processed patch data using sql queries"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # hero changes by type
            cursor.execute("""
                SELECT h.name, pc.change_type, COUNT(*) as count
                FROM patch_changes pc
                JOIN heroes h ON pc.hero_id = h.id
                WHERE pc.patch_id = ?
                GROUP BY h.name, pc.change_type
                ORDER BY h.name, pc.change_type
            """, (patch_id,))
            hero_changes = cursor.fetchall()
            
            # item changes by category and type
            cursor.execute("""
                SELECT i.category, i.name, pc.change_type, COUNT(*) as count
                FROM patch_changes pc
                JOIN items i ON pc.item_id = i.id
                WHERE pc.patch_id = ?
                GROUP BY i.category, i.name, pc.change_type
                ORDER BY i.category, i.name, pc.change_type
            """, (patch_id,))
            item_changes = cursor.fetchall()
            
            # media files
            cursor.execute("""
                SELECT media_type, COUNT(*) as count
                FROM patch_media
                WHERE patch_id = ?
                GROUP BY media_type
            """, (patch_id,))
            media_counts = cursor.fetchall()
            
            return {
                "hero_changes": hero_changes,
                "item_changes": item_changes,
                "media_counts": media_counts
            }

def process_all_patches():
    """process all unprocessed patches"""
    processor = PatchProcessor()
    
    with sqlite3.connect("patch.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM patches WHERE processed = FALSE ORDER BY id")
        unprocessed = cursor.fetchall()
    
    print(f"processing {len(unprocessed)} patches...")
    
    for (patch_id,) in unprocessed:
        try:
            processor.process_patch_content(patch_id)
        except Exception as e:
            print(f"✗ error processing patch {patch_id}: {e}")
    
    print("✓ all patches processed")

if __name__ == "__main__":
    process_all_patches()
