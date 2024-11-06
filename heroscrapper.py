import requests
from bs4 import BeautifulSoup
import sqlite3


def init_db():
    conn = sqlite3.connect("patch.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS characters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    ability1 TEXT,
                    ability2 TEXT,
                    ability3 TEXT,
                    ability4 TEXT
                 )''')
    conn.commit()
    conn.close()

def save_character(name, ability1, ability2, ability3, ability4):
    conn = sqlite3.connect("patch.db")
    c = conn.cursor()
    c.execute('''INSERT INTO characters 
                (name, ability1, ability2, ability3, ability4) 
                VALUES (?, ?, ?, ?, ?)''',
              (name, ability1, ability2, ability3, ability4))
    conn.commit()
    conn.close()

def scrap_characters():
    url = "https://deadlocked.wiki/Hero"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"[scrap_characters] Failed to fetch the hero page: {url}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    tbody_elements = soup.find_all('tbody')[:-2]

    for tbody in tbody_elements:
        links = tbody.find_all('a', title=True)
        if len(links) >= 2:
            character_name = links[1].get_text().strip()

            abilities = tbody.find_all('div', class_='ability-icon')
            if len(abilities) >= 4:
                ability1 = abilities[0].find('img')['src'].split('/')[-1].split('.')[0].replace('_', ' ').replace('48px-', '').replace('%27', "'")
                ability2 = abilities[1].find('img')['src'].split('/')[-1].split('.')[0].replace('_', ' ').replace('48px-', '').replace('%27', "'")
                ability3 = abilities[2].find('img')['src'].split('/')[-1].split('.')[0].replace('_', ' ').replace('48px-', '').replace('%27', "'")
                ability4 = abilities[3].find('img')['src'].split('/')[-1].split('.')[0].replace('_', ' ').replace('48px-', '').replace('%27', "'")

                print(f"Found character: {character_name}")
                print(f"Abilities: {ability1}, {ability2}, {ability3}, {ability4}")

                save_character(character_name, ability1, ability2, ability3, ability4)


init_db()

if __name__ == "__main__":
    scrap_characters()
