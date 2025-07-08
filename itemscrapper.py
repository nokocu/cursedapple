import requests
from bs4 import BeautifulSoup
import sqlite3
import os

# directory
os.makedirs('static/assets/img', exist_ok=True)


# initialize the db
def init_db():
    conn = sqlite3.connect("patch.db")
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    category TEXT,
                    price TEXT,
                    image_url TEXT
                 )''')
    conn.commit()
    conn.close()


# save item to the db
def save_item(name, category, price, image_url):
    conn = sqlite3.connect("patch.db")
    c = conn.cursor()

    c.execute("INSERT INTO items (name, category, price, image_url) VALUES (?, ?, ?, ?)",
              (name, category, price, image_url))
    conn.commit()
    conn.close()


# download images if they dont exist in the folder
def download_image(image_url, item_name):
    # generate the image file
    file_name = f"{item_name.replace('_', ' ').lower()}.png"
    image_path = os.path.join("static", "assets", "img", file_name)

    try:
        # download
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            # save
            with open(image_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Image saved for {item_name}: {image_path}")
            return image_url
        else:
            print(f"Failed to download image for {item_name}: {image_url}")
            return None
    except Exception as e:
        print(f"Error downloading image for {item_name}: {e}")
        return None


# function to scrape items from the website
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
                name = item.find_all("tr")[2].get_text(strip=True)

                img_tag = item.find_all("tr")[1].find("img")
                if img_tag and img_tag.get("src"):
                    image_src = img_tag.get("src")
                    image_url = f"https://deadlocked.wiki{image_src}" if not image_src.startswith("http") else image_src

                    if image_url:
                        save_item(name, category, price, image_url)
                        print(f"[INFO] Saved item: {name} (Category: {category})")
                else:
                    print(f"[ERROR] No image found for {name}")
            except Exception as e:
                print(f"[ERROR] Failed to process item: {e}")


# check if an item already exists
def item_exists(name):
    conn = sqlite3.connect("patch.db")
    c = conn.cursor()

    c.execute("SELECT 1 FROM items WHERE name = ?", (name,))
    exists = c.fetchone() is not None
    conn.close()

    return exists


# add missing items
def add_missing_items(missing_items):
    for name, details in missing_items.items():
        if not item_exists(name):
            category = details["Category"]
            price = details["Price"]
            image = details["Image"]
            save_item(name, category, price, image)
            print(f"[INFO] Saved missing item: {name} (Category: {category}, Price: {price})")
        else:
            print(f"[INFO] Missing item '{name}' already exists in the database.")


# scrape images only (without redownloading)
def scrap_images():
    conn = sqlite3.connect("patch.db")
    c = conn.cursor()

    c.execute("SELECT name, image_url FROM items WHERE image_url IS NOT NULL")
    items = c.fetchall()

    for name, image_url in items:
        if image_url:
            image_url = download_image(image_url, name)
        else:
            print(f"[ERROR] No image URL found for {name}")
    conn.close()


# main
if __name__ == "__main__":
    init_db()
    scrap_items()
    missing_items = {
        "Soul Rebirth": {"Category": "Vitality",
                         "Price": "6,200",
                         "Image": "https://deadlocked.wiki/images/thumb/c/c3/Soul_Rebirth.png/75px-Soul_Rebirth.png"}
    }
    add_missing_items(missing_items)
    scrap_images()
