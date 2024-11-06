import requests
from bs4 import BeautifulSoup
import sqlite3


def init_db():
    conn = sqlite3.connect("patch.db")
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    category TEXT,
                    price TEXT,
                    icon_link TEXT
                 )''')
    conn.commit()
    conn.close()


def save_item(name, category, price, icon_link):
    conn = sqlite3.connect("patch.db")
    c = conn.cursor()

    c.execute("INSERT INTO items (name, category, price, icon_link) VALUES (?, ?, ?, ?)",
              (name, category, price, icon_link))
    conn.commit()
    conn.close()


def scrap_items():
    url = "https://deadlocked.wiki/Item"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"[ERROR] Failed to fetch the page. Status code: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all("table", class_="navbox")[:3]
    categories = ["Weapon", "Vitality", "Spirit"]

    if not tables:
        print("[ERROR] No categories found on the page!")
        return

    for i, table in enumerate(tables):
        category = categories[i] if i < len(categories) else f"Unknown Category {i + 1}"

        items = table.find_all("div", class_="HeroCard2")

        for item in items:
            try:
                price = item.find_all("tr")[0].get_text(strip=True)
                img_tag = item.find_all("tr")[1].find("img")
                icon_link = "https://deadlocked.wiki" + img_tag["src"] if img_tag else None
                name = item.find_all("tr")[2].get_text(strip=True)
                save_item(name, category, price, icon_link)
                print(f"[INFO] Saved item: {name} (Category: {category})")
            except Exception as e:
                print(f"[ERROR] Failed to process item: {e}")


if __name__ == "__main__":
    init_db()
    scrap_items()
