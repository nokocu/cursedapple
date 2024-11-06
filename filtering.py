import re
import sqlite3
from pprint import pprint


def process_text(content, heroes_database, items_database):
    result = {
        "Heroes": {},
        "Items": {"Spirit items": {}, "Weapon items": {}, "Vitality items": {}},
        "Gameplay & Other": [],
        "Fixes": [],
    }

    for line in content.splitlines():
        line = re.sub(r'<.*?>', '', line).strip().replace("- ", "")

        if any(hero[0].lower() in line.lower() for hero in heroes_database):
            for hero in heroes_database:
                if hero[0].lower() in line.lower():
                    if hero[0] not in result["Heroes"]:
                        result["Heroes"][hero[0]] = []
                    result["Heroes"][hero[0]].append(
                        line.replace(f"{hero[0]} ", "").replace(f"{hero[0]}: ", "").strip())
                    break

        elif any(item.lower() in line.lower() for item in items_database):
            for item, category in items_database.items():
                if item.lower() in line.lower():
                    if item not in result["Items"][f"{category} items"]:
                        result["Items"][f"{category} items"][item] = []
                    result["Items"][f"{category} items"][item].append(
                        line.replace(f"{item} ", "").replace(f"{item}: ", "").strip())
                    break

        elif line.startswith("Fixed") or line.startswith("Fix"):
            result["Fixes"].append(line.strip())

        elif line != "" and not line.startswith("["):
            result["Gameplay & Other"].append(line.strip())

    result["Gameplay & Other"].sort()
    result["Fixes"].sort()

    # fixes at the end
    for category in result["Items"]:
        result["Items"][category] = dict(
            sorted(result["Items"][category].items(), key=lambda item: (item[0].startswith(('Fixed', 'Fix')), item[0])))

    for hero in result["Heroes"]:
        result["Heroes"][hero] = sorted(result["Heroes"][hero], key=lambda x: (x.startswith(('Fixed', 'Fix')), x))

    return result


content = """

<br/>
- Added something1<br/>
- Added something2<br/>
- Vampiric Burst: changed something1<br/>
- Vampiric Burst: changed something2<br/>
- Unstoppable: changed something2<br/>
<br/>
[ Hero Gameplay Changes ]<br/>
<br/>
- Abrams: Zncreased something<br/>
<br/>
- Bebop: Zncreased something<br/>

<br/>
<br/>
[ Misc Gameplay Changes ]<br/>
<br/>
- Crate Powerups: something1<br/>
- Walkers: something2<br/>
- Fixed some issues<br/>
- Fixed some more issues<br/>

[ Other ]<br/>
- Fixed sometimes abrams something<br/>
- Fixed sometimes bebop something<br/>
- Fixed lash stuck sometimes<br/>
- Replaced something
- Enabled something
- For private lobbies something has changed
- Vampiric Burst: fixed something<br/>
"""

# main
if __name__ == "__main__":
    conn = sqlite3.connect('patch.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, ability1, ability2, ability3, ability4 FROM characters")
    heroes_data = [(row[0], [row[1], row[2], row[3], row[4]]) for row in cursor.fetchall()]
    cursor.execute("SELECT name, category FROM items")
    items_data = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()

    result = process_text(content, heroes_data, items_data)
    pprint(result)
    pprint(heroes_data)
    pprint(items_data)
