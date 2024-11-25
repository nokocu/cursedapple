# get data -> categorize -> sort
import json
import os
import sqlite3
import re
from pprint import pprint

import requests

# get data ############################################################################################################

characters = []
items = {
    "Weapon": [],
    "Spirit": [],
    "Vitality": []
}

final_structure = {
    "heroes": {},
    "items": {"Weapon": {}, "Spirit": {}, "Vitality": {}},
    "new": [],
    "gameplay": [],
    "fixes": [],
    "uncategorized": [],
    "gallery": [],
    "hidden": []
}

with sqlite3.connect("patch.db") as conn:
    cursor = conn.cursor()

    # get characters
    cursor.execute("SELECT name FROM characters")
    characters.extend([hero_name for (hero_name,) in cursor.fetchall()])
    for hero in characters:
        final_structure["heroes"][hero] = {"buff": [], "nerf": [], "other": []}

    # get items
    cursor.execute("SELECT name, category FROM items")
    for item_name, category in cursor.fetchall():
        if category not in items:
            items[category] = []
        items[category].append(item_name)
    for category, item_list in items.items():
        for item in item_list:
            final_structure["items"][category][item] = {"buff": [], "nerf": [], "other": []}

    # get abilites
    cursor.execute(""" SELECT name, ability1, ability2, ability3, ability4 FROM characters """)
    char_abilities = {
        hero_name: [ability1, ability2, ability3, ability4]
        for hero_name, ability1, ability2, ability3, ability4 in cursor.fetchall()
    }


# categorize ##########################################################################################################

def categorize(line, characters, items, final_structure, force_category=None):

    # gallery
    def gallery_flag(line):
        href_pattern = r'src="([^"]+)"'
        href_match = re.search(href_pattern, line)
        if href_match:
            url = href_match.group(1)
            return url
        else:
            return None

    # hero flag (prioritize the "hero:" format, ignore hero labs)
    def hero_flag(line, characters, char_abilities):
        ignore_words = ["hero labs"]
        line_lower = line.lower()

        # hero names
        for hero in characters:
            # ignore word list
            if any(word in line.lower() for word in ignore_words):
                return None
            # ignore mentions like "you are perfection, Haze"
            elif f'{hero}"' in line_lower or f'"{hero}' in line_lower:
                return None
            elif f"{hero}:" in line_lower:
                return hero
            elif hero in line_lower:
                return hero

        # ability names
        for hero, abilities in char_abilities.items():
            for ability in abilities:
                if ability.lower() in line_lower:
                    return hero

        return None

    # item flag (prioritize the "item:" format, then ignore item names that may be used in normal sentence)
    def item_flag(line, items):
        ignore_words = ["long range"]

        line_lower = line.lower()
        for category, item_list in items.items():
            for item in item_list:
                item_lower = item.lower()
                if f"{item_lower}:" in line_lower:
                    return category, item

        for category, item_list in items.items():
            for item in item_list:
                item_lower = item.lower()
                if item_lower in line_lower and not any(ignore_word in line_lower for ignore_word in ignore_words):
                    return category, item

        return None

    # buff or nerf checker
    def buff_flag(line):
        buff_words = ["increased", "improved", "now grants", "now has"]
        nerf_words = ["reduced", "no longer grants"]
        other_words = ["vfx", "sfx", "sound", "animation", "Paradoxical Swap time", "visual"]

        if any(phrase.lower() in line.lower() for phrase in other_words):
            return "other"

        if "cooldown" in line.lower() or "cd" in line.lower():
            time_values = re.findall(r"-?\d+\.?\d*s", line)
            if time_values:
                time_values = [float(val.replace('s', '')) for val in time_values]
            else:
                time_values = re.findall(r"-?\d+\.?\d+", line)
                time_values = [float(val) for val in time_values]
            if len(time_values) >= 2:
                first, second = time_values[0], time_values[1]
                if first < second:
                    return "nerf"
                elif first >= second:
                    return "buff"
            else:
                return "other"

        elif any(word in line.lower() for word in buff_words):
            return "buff"
        elif any(word in line.lower() for word in nerf_words):
            return "nerf"
        else:
            return "other"

    # if not a hero or item related line
    def uncategorized_flag(line):
        fixes_words = ["fixed"]
        gameplay_words = [
                            "walker", "guardian", "shrine", "patron",
                            "souls", "urn", "mid boss", "trooper", "creep", "sinner's sacrifice", "camps", "breakables",
                            "respawn", "parry", "melee",
                            "stair", "lane", "hallway", "bounce pad", "traversal", "zipline", "bridge",
                            "backdoor", "spawn", "building", "rooftops", "interior", "chimney", "roof", "zap",
                            "sinners sacrifice", "comeback"
                          ]
        new_words = ["added", "updated"]
        ignore_words = ["View attachment"]

        first_word = line.lower().split()[0] if line.strip() else ""
        if first_word in fixes_words:
            return "fixes"
        elif line.endswith(".mp4"):
            return "hidden"
        elif any(word in line.lower() for word in gameplay_words):
            return "gameplay"
        elif any(word in line.lower() for word in new_words):
            return "new"
        else:
            return "uncategorized"

    # main categorizing logic
    # nested statements
    if force_category:
        final_structure[force_category].append(line)
        return
    elif line.endswith(":"):
        line = line[:-1]

    # gallery
    gallery_flag = gallery_flag(line)
    if gallery_flag:
        final_structure["gallery"].append(gallery_flag)
        return

    # hero
    hero = hero_flag(line, characters, char_abilities)
    if hero:
        buff_type = buff_flag(line)
        if buff_type:
            final_structure["heroes"][hero][buff_type].append(line)
        return

    # item
    item = item_flag(line, items)
    if item:
        category, item_name = item
        buff_type = buff_flag(line)
        if buff_type:
            final_structure["items"][category][item_name][buff_type].append(line)
            final_structure[f"{category}_changes"] = "true"
        return

    # other
    category = uncategorized_flag(line)
    final_structure[category].append(line)


# filter & sort ########################################################################################################

# if under hero or items, sort alphabeticaly but prioritize lines with values, elsewhere just alphabeticaly
def sorting(structure):
    for key, value in structure.items():
        if key in ['new', 'gameplay', 'fixes', 'uncategorized'] and isinstance(value, list):
            structure[key] = sorted(value)
        elif isinstance(value, dict):
            sorting(value)
        elif isinstance(value, list) and key in ['buff', 'nerf', 'other']:
            with_numbers = [entry for entry in value if any(char.isdigit() for char in entry)]
            without_numbers = [entry for entry in value if not any(char.isdigit() for char in entry)]
            with_numbers.sort()
            without_numbers.sort()
            structure[key] = with_numbers + without_numbers


def clear_empty_data(final_structure):
    for category, item_dict in final_structure["items"].items():
        final_structure["items"][category] = {item: value for item, value in item_dict.items() if any(value.values())}
    final_structure["items"] = {category: item_dict for category, item_dict in final_structure["items"].items() if item_dict}
    final_structure["heroes"] = {hero: value for hero, value in final_structure["heroes"].items() if any(value.values())}


# final ################################################################################################################

def notes_to_json(id, conn):
    cursor = conn.cursor()

    # Pobierz wybrany wpis na podstawie ID
    cursor.execute("SELECT content FROM patches WHERE id = ?", (id,))
    content = cursor.fetchone()

    if content:
        final_structure_copy = {
            "heroes": {hero: {"buff": [], "nerf": [], "other": []} for hero in characters},
            "items": {category: {item: {"buff": [], "nerf": [], "other": []} for item in item_list} for
                      category, item_list in items.items()},
            "new": [], "gameplay": [], "fixes": [], "uncategorized": [], "gallery": [], "hidden": []
        }

        # categorize (exceptions for image and nested note)
        last_line = None
        last_category = None
        temporary_list: []
        for line in content[0].splitlines():

            # when image src
            if 'src' in line:
                categorize(line, characters, items, final_structure_copy)
                continue

            # when nested statements with margin
            elif '<div style="margin-left: 20px">' in line:
                for chunk in line.split('<div style="margin-left: 20px">'):

                    if not chunk.strip():
                        continue

                    chunk = re.sub(r'<.*?>', '', chunk).strip()
                    chunk = chunk.replace("- ", f"{last_line} ").replace("- ", "")

                    categorize(chunk, characters, items, final_structure_copy, force_category="uncategorized")

            # when nested statements without margin
            elif re.sub(r'<.*?>', '', line).strip().startswith('['):
                line = re.sub(r'<.*?>', '', line).strip().replace("- ", "")
                last_category = re.sub(r"[\[\]]", "", line).strip()

            else:
                line = re.sub(r'<.*?>', '', line).strip()
                if not line.startswith('-') and line != "":
                    if last_category:
                        line = last_category + ": " + line
                        categorize(line, characters, items, final_structure_copy, force_category="uncategorized")
                        continue
                elif line == "":
                    continue

                categorize(line.replace("- ", ""), characters, items, final_structure_copy)
                last_line = line

        # sort
        sorting(final_structure_copy)

        # clear empty data
        clear_empty_data(final_structure_copy)

        # Zaktualizuj wpis w bazie danych
        content_filtered = json.dumps(final_structure_copy)
        cursor.execute("UPDATE patches SET content_filtered = ? WHERE id = ?", (content_filtered, id))
        conn.commit()

########################################################################################################################
if __name__ == "__main__":
    start_id = 1  # Starting ID
    end_id = 100  # Ending ID (adjust as needed)

    for current_id in range(start_id, end_id + 1):
        try:
            notes_to_json(current_id, conn)
            print(f"processed patch ID: {current_id}")
        except Exception as e:
            print(f"error processing patch ID: {current_id}. Error: {e}")
