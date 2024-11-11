# get data -> categorize -> sort
import json
import sqlite3
import re
from pprint import pprint

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

    # example content to sort
    # cursor.execute("SELECT content FROM patches WHERE id = 43")
    # content = cursor.fetchone()


# categorize ##########################################################################################################

def categorize(line, characters, items, final_structure):

    # hero mentioned (prioritize hero_name with a colon)
    def hero_flag(line, characters):
        for word in characters:
            pattern = r'\b' + re.escape(word) + r':'
            if re.search(pattern, line, re.IGNORECASE):
                return word

            pattern = r'\b' + re.escape(word) + r'\b'
            if re.search(pattern, line, re.IGNORECASE):
                return word

        return None

    # item mentioned
    def item_flag(line, items):
        for category, item_list in items.items():
            for item in item_list:
                if item.lower() in line.lower():
                    return category, item
        return None

    # buff or nerf checker
    def buff_flag(line):
        buff_words = ["increased", "improved", "now grants", "now has"]
        nerf_words = ["reduced", "no longer grants"]

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
        fixes_words = ["fixed", "fixed", "fixing"]
        gameplay_words = ["walker", "guardian", "shrine", "patron",
                          "souls", "urn", "mid boss", "trooper", "creep", "sinner's sacrifice", "camps", "breakables",
                          "respawn", "parry", "melee",
                          "stair", "lane", "hallway", "bounce pad", "traversal", "zipline", "bridge"]
        new_words = ["added", "updated"]
        if any(word in line.lower() for word in fixes_words):
            return "fixes"
        elif any(word in line.lower() for word in gameplay_words):
            return "gameplay"
        elif any(word in line.lower() for word in new_words):
            return "new"
        else:
            return "uncategorized"

    # main categorizing logic
    hero = hero_flag(line, characters)
    if hero:
        buff_type = buff_flag(line)
        if buff_type:
            final_structure["heroes"][hero][buff_type].append(line)
        return

    item = item_flag(line, items)
    if item:
        category, item_name = item
        buff_type = buff_flag(line)
        if buff_type:
            final_structure["items"][category][item_name][buff_type].append(line)
            final_structure[f"{category}_changes"] = "true"
        return

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


########################################################################################################################
if __name__ == "__main__":

    # newfiltering -> get data
    with sqlite3.connect("patch.db") as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id, content FROM patches")
        patches = cursor.fetchall()

        for patch_id, content in patches:
            final_structure_copy = {
                "heroes": {hero: {"buff": [], "nerf": [], "other": []} for hero in characters},
                "items": {category: {item: {"buff": [], "nerf": [], "other": []} for item in item_list} for category, item_list in items.items()},
                "new": [],
                "gameplay": [],
                "fixes": [],
                "uncategorized": [],
            }

            # newfiltering -> categorize
            for line in content.splitlines():
                line = re.sub(r'<.*?>', '', line).strip().replace("- ", "")
                if line.startswith('[') or line == "":
                    continue
                categorize(line, characters, items, final_structure_copy)

            # newfiltering -> sort
            sorting(final_structure_copy)

            # newfiltering -> clearing empty data
            clear_empty_data(final_structure_copy)

            # insert filtered content back into the database
            content_filtered = json.dumps(final_structure_copy)
            cursor.execute("UPDATE patches SET content_filtered = ? WHERE id = ?", (content_filtered, patch_id))
