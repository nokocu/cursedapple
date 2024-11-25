import requests
from bs4 import BeautifulSoup
import sqlite3
import os  # For working with the file system

# Ensure the image directory exists
os.makedirs('static/assets/img', exist_ok=True)

# Function to initialize the database
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

# Function to save item to the database
def save_item(name, category, price, image_url):
    conn = sqlite3.connect("patch.db")
    c = conn.cursor()

    c.execute("INSERT INTO items (name, category, price, image_url) VALUES (?, ?, ?, ?)",
              (name, category, price, image_url))
    conn.commit()
    conn.close()

# Function to download images if they don't exist in the folder
def download_image(image_url, item_name):
    # Generate the image file name by replacing underscores with spaces and converting to lowercase
    file_name = f"{item_name.replace('_', ' ').lower()}.png"
    image_path = os.path.join("static", "assets", "img", file_name)

    try:
        # Download the image content
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            # Save the image to the file path
            with open(image_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Image saved for {item_name}: {image_path}")
            return image_url  # Return the original URL
        else:
            print(f"Failed to download image for {item_name}: {image_url}")
            return None
    except Exception as e:
        print(f"Error downloading image for {item_name}: {e}")
        return None

# Function to scrape items from the website
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

# Function to check if an item already exists in the database
def item_exists(name):
    conn = sqlite3.connect("patch.db")
    c = conn.cursor()

    c.execute("SELECT 1 FROM items WHERE name = ?", (name,))
    exists = c.fetchone() is not None
    conn.close()

    return exists

# Function to add missing items to the database
def add_missing_items(missing_items):
    for name, details in missing_items.items():
        if not item_exists(name):  # Check if the missing item is already in the database
            category = details["Category"]
            price = details["Price"]
            image = details["Image"]
            save_item(name, category, price, image)
            print(f"[INFO] Saved missing item: {name} (Category: {category}, Price: {price})")
        else:
            print(f"[INFO] Missing item '{name}' already exists in the database.")

# Function to scrape images only (without re-downloading already existing ones)
def scrap_images():
    conn = sqlite3.connect("patch.db")
    c = conn.cursor()

    c.execute("SELECT name, image_url FROM items WHERE image_url IS NOT NULL")
    items = c.fetchall()

    for name, image_url in items:
        if image_url:
            # Download the image and update the image URL in the database
            image_url = download_image(image_url, name)
        else:
            print(f"[ERROR] No image URL found for {name}")
    conn.close()

# Main execution flow
if __name__ == "__main__":
    init_db()
    scrap_items()  # Scraping items and saving to DB
    missing_items = {
        "Soul Rebirth": {"Category": "Vitality",
                         "Price": "6,200",
                         "Image": "https://deadlocked.wiki/images/thumb/c/c3/Soul_Rebirth.png/75px-Soul_Rebirth.png"}
    }
    add_missing_items(missing_items)
    scrap_images()  # optional image scraping
