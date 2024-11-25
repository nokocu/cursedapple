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
    "[ Heroes ]": {},
    "[ Items ]": {"Weapon": {}, "Spirit": {}, "Vitality": {}},
    "[ Gallery ]": [],
    "[ Hidden ]": []
}

with sqlite3.connect("patch.db") as conn:
    cursor = conn.cursor()

    # get characters
    cursor.execute("SELECT name FROM characters")
    characters.extend([hero_name for (hero_name,) in cursor.fetchall()])
    for hero in characters:
        final_structure["[ Heroes ]"][hero] = {"buff": [], "nerf": [], "other": []}

    # get items
    cursor.execute("SELECT name, category FROM items")
    for item_name, category in cursor.fetchall():
        if category not in items:
            items[category] = []
        items[category].append(item_name)
    for category, item_list in items.items():
        for item in item_list:
            final_structure["[ Items ]"][category][item] = {"buff": [], "nerf": [], "other": []}

    # get abilites
    cursor.execute(""" SELECT name, ability1, ability2, ability3, ability4 FROM characters """)
    char_abilities = {
        hero_name: [ability1, ability2, ability3, ability4]
        for hero_name, ability1, ability2, ability3, ability4 in cursor.fetchall()
    }


# categorize ##########################################################################################################

def categorize(line, characters, items, final_structure, force_category=None):

    def item_or_hero_flag(line, characters, char_abilities, items):
        ignore_words = ["long range", "hero labs"]
        mistyped_dict = {"knockdown": {"Knock Down"}}
        line_lower = line.lower()

        # handle mistyped items
        for correct, mistyped_list in mistyped_dict.items():
            for mistyped in mistyped_list:
                if mistyped.lower() in line_lower:
                    line_lower = line_lower.replace(mistyped.lower(), correct)



        # check for "item:" format first
        for category, item_list in items.items():
            for item in item_list:
                item_lower = item.lower()
                if f"{item_lower}:" in line_lower:
                    return "item", category, item  # Return item category and name

        # check for "hero:" format second
        for hero in characters:
            # handle cases like "you are perfection, Haze"
            if f'{hero}"' in line.lower() or f'"{hero}' in line.lower():
                return None
            if f"{hero}:" in line_lower:
                return "hero", hero  # Return hero name

        # check for general item mentions
        for category, item_list in items.items():
            for item in item_list:
                item_lower = item.lower()
                if item_lower in line_lower and not any(ignore_word in line_lower for ignore_word in ignore_words):
                    return "item", category, item  # Return item category and name

        # check for general hero mentions
        for hero in characters:
            if hero in line_lower and not any(word in line_lower for word in ignore_words):
                return "hero", hero  # Return hero name

        # check for hero abilities at the end
        for hero, abilities in char_abilities.items():
            for ability in abilities:
                if ability is None:
                    continue
                if ability.lower() in line_lower:
                    return "hero", hero

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

    # main categorizing logic
    result = item_or_hero_flag(line, characters, char_abilities, items)
    if result:
        if result[0] == "item":
            category, item_name = result[1], result[2]
            buff_type = buff_flag(line)
            if buff_type:
                final_structure["[ Items ]"][category][item_name][buff_type].append(line)
            return

        elif result[0] == "hero":
            hero_name = result[1]
            buff_type = buff_flag(line)
            if buff_type:
                final_structure["[ Heroes ]"][hero_name][buff_type].append(line)
            return

    # other
    if force_category not in final_structure:
        final_structure[force_category] = []
    final_structure[force_category].append(line)




# filter & sort ########################################################################################################

def sorting(structure):
    for key, value in structure.items():
        if key not in ["[ Heroes ]", "[ Vitality Items ]", "[ Weapon Items ]", "[ Spirit Items ]", "[ Hero Changes ]"] and isinstance(value, list):
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
    for category, item_dict in final_structure["[ Items ]"].items():
        final_structure["[ Items ]"][category] = {item: value for item, value in item_dict.items() if any(value.values())}
    final_structure["[ Items ]"] = {category: item_dict for category, item_dict in final_structure["[ Items ]"].items() if item_dict}
    final_structure["[ Heroes ]"] = {hero: value for hero, value in final_structure["[ Heroes ]"].items() if any(value.values())}


# final ################################################################################################################

def notes_to_json(id, conn):
    cursor = conn.cursor()

    # Pobierz wybrany wpis na podstawie ID
    cursor.execute("SELECT content FROM patches WHERE id = ?", (id,))
    content = cursor.fetchone()

    if content:
        final_structure_copy = {
            "[ Heroes ]": {hero: {"buff": [], "nerf": [], "other": []} for hero in characters},
            "[ Items ]": {category: {item: {"buff": [], "nerf": [], "other": []} for item in item_list} for
                      category, item_list in items.items()},
            "[ Gallery ]": [], "[ Hidden ]": []
        }

        # categorize (exceptions for image and nested note)
        last_line = None
        last_category = None
        temporary_list: []

        for line in content[0].splitlines():
            stripped_line = re.sub(r'<.*?>', '', line).strip().replace("- ", "")

            if stripped_line.endswith(".mp4"):
                categorize(stripped_line, characters, items, final_structure_copy, force_category="[ Hidden ]")
                continue

            # Check if its the category
            elif stripped_line.startswith("[") and stripped_line.endswith("]"):
                last_category = stripped_line
                continue

            elif '<div style="margin-left: 20px">' in line:
                if not last_line.endswith(":"):
                    last_line = last_line + ": "
                last_category_temp = last_category if last_category is not None else "[ General Changes ]"
                for chunk in line.split('<div style="margin-left: 20px">'):
                    if not chunk.strip():
                        continue

                    chunk = re.sub(r'<.*?>', '', chunk).strip()
                    chunk = chunk.replace("- ", f"{last_line} ")

                    categorize(chunk, characters, items, final_structure_copy, force_category=last_category_temp)
                continue

            # Check if line has any image src
            elif 'src' in line:
                src_pattern = r'src="([^"]+)"'
                src_match = re.search(src_pattern, line)
                if src_match:
                    line = src_match.group(1)
                    categorize(line, characters, items, final_structure_copy, force_category="[ Gallery ]")
                    continue

            # If line ends with ":", remove it
            elif stripped_line.endswith(":"):
                stripped_line = stripped_line[:-1]

            # Ignore empty lines
            elif stripped_line == "":
                continue

            # Categorize the line (use last_category or default to "[ OTHER ]")
            last_category_temp = last_category if last_category is not None else "[ General Changes ]"
            categorize(stripped_line, characters, items, final_structure_copy, force_category=last_category_temp)
            last_line = re.sub(r'<.*?>', '', line).strip().replace("- ", "")

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
