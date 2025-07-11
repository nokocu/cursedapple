import requests
from bs4 import BeautifulSoup
import sqlite3
import urllib.parse  # For decoding URL-encoded characters
import os  # For working with the file system

# ensure dir exists
os.makedirs('static/assets/img', exist_ok=True)


def init_db():
    conn = sqlite3.connect("patch.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS characters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    ability1 TEXT,
                    ability2 TEXT,
                    ability3 TEXT,
                    ability4 TEXT,
                    image_url TEXT
                 )''')
    conn.commit()
    conn.close()


def save_character(name, ability1, ability2, ability3, ability4, image_url=None):
    conn = sqlite3.connect("patch.db")
    c = conn.cursor()

    # check if the character already exists
    c.execute('SELECT id FROM characters WHERE name = ?', (name,))
    existing_character = c.fetchone()

    if existing_character:
        # update the image_url if the character exists
        c.execute('''UPDATE characters 
                     SET image_url = ? 
                     WHERE name = ?''', (image_url, name))
        print(f"Updated image for {name}")
    else:
        # insert a new record if the character doesn't exist
        c.execute('''INSERT INTO characters 
                    (name, ability1, ability2, ability3, ability4, image_url) 
                    VALUES (?, ?, ?, ?, ?, ?)''',
                  (name, ability1, ability2, ability3, ability4, image_url))
        print(f"Inserted new character {name}")

    conn.commit()
    conn.close()


def download_image(image_url, hero_name):
    # extract the image file extension from the URL
    file_name = f"{hero_name}.png"
    image_path = os.path.join("static", "assets", "img", file_name)

    try:
        # download
        response = requests.get(image_url, stream=True)

        if response.status_code == 200:
            # save the image to the file path
            with open(image_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Image saved for {hero_name}")
            # save relative path for the database
            return f"/static/assets/img/{file_name}"
        else:
            print(f"Failed to download image for {hero_name}: {image_url}")
            return None
    except Exception as e:
        print(f"Error downloading image for {hero_name}: {e}")
        return None


def scrap_characters():
    url = "https://deadlocked.wiki/Hero"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"[scrap_characters] Failed to fetch the hero page: {url}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # extract character abilities
    tbody_elements = soup.find_all('tbody')[:-2]

    for tbody in tbody_elements:
        links = tbody.find_all('a', title=True)
        if len(links) >= 2:
            character_name = links[1].get_text().strip().lower()

            abilities = tbody.find_all('div', class_='ability-icon')
            if len(abilities) >= 4:
                ability1 = abilities[0].find('img')['src'].split('/')[-1].split('.')[0].replace('_', ' ').replace(
                    '48px-', '').replace('%27', "'").lower()
                ability2 = abilities[1].find('img')['src'].split('/')[-1].split('.')[0].replace('_', ' ').replace(
                    '48px-', '').replace('%27', "'").lower()
                ability3 = abilities[2].find('img')['src'].split('/')[-1].split('.')[0].replace('_', ' ').replace(
                    '48px-', '').replace('%27', "'").lower()
                ability4 = abilities[3].find('img')['src'].split('/')[-1].split('.')[0].replace('_', ' ').replace(
                    '48px-', '').replace('%27', "'").lower()

                print(f"Found character: {character_name}")
                print(f"Abilities: {ability1}, {ability2}, {ability3}, {ability4}")

                save_character(character_name, ability1, ability2, ability3, ability4)


def scrap_images():
    url = "https://deadlocked.wiki/Hero"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"[scrap_images] Failed to fetch the hero page: {url}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # target the last two tbody elements
    tbody_elements = soup.find_all('tbody')[-2:]  # Only the last two tbody elements for images

    for tbody in tbody_elements:
        # locate all hero cards
        hero_cards = tbody.find_all('div', class_='HeroCard2')

        for hero_card in hero_cards:
            # extract hero name
            hero_link = hero_card.find('a', href=True)
            if hero_link:
                hero_name = hero_link['href'].split('/')[-1].lower()  # Extract hero name from the href

                # decode
                hero_name = urllib.parse.unquote(hero_name)

                # replace underscores with spaces
                hero_name = hero_name.replace('_', ' ')

                # extract the image URL
                hero_image_tag = hero_card.find('img', src=True)
                if hero_image_tag:
                    hero_image_url = "https://deadlocked.wiki/" + hero_image_tag['src']

                    # download and update
                    download_image(hero_image_url, hero_name)
                    save_character(hero_name, None, None, None, None, hero_image_url)


if __name__ == "__main__":
    init_db()
    scrap_characters()
    scrap_images()
