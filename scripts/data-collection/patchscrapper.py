import requests
from bs4 import BeautifulSoup
import sqlite3
import html
from newfiltering import notes_to_json

database = "patch.db"

def init_db():
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS patches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    content TEXT,
                    content_filtered TEXT,
                    link TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date TEXT
                 )''')
    conn.commit()
    conn.close()

init_db()


def insert_patch(title, content, link, timestamp, date):
    with sqlite3.connect(database) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO patches (title, content, link, timestamp, date) VALUES (?, ?, ?, ?, ?)",
                  (title, content, link, timestamp, date))
        last_id = c.lastrowid
        notes_to_json(last_id, conn)


def patch_content(link):
    response = requests.get(link)
    if response.status_code != 200:
        print(f"[patch_content] Failed to fetch the patch page: {link}")
        return None, None

    soup = BeautifulSoup(response.text, 'html.parser')

    content_div = soup.find("article", class_="message-body")
    if content_div:
        bb_wrapper = content_div.find("div", class_="bbWrapper")
        if bb_wrapper:
            content = str(bb_wrapper)
            content = html.unescape(content)
        else:
            print(f"[patch_content] no bbWrapper found for {link}")
            return None, None
    else:
        print(f"[patch_content] no content_div found for {link}")
        return None, None

    title_element = soup.find("h1", class_="p-title-value")
    if title_element:
        title = title_element.get_text().strip()
        date = title.split()[0]
    else:
        print(f"[patch_content] no title_element found for {link}")
        return None, None

    time_element = soup.find("time", class_="u-dt")
    timestamp = None
    if time_element:
        datetime = time_element.get('datetime')
        if datetime:
            timestamp = datetime

    return content, timestamp, title, date

def scrapper(forums="https://forums.playdeadlock.com/forums/changelog.10/"):
    patches_data = []

    while forums:
        print(f"[patch_link] Fetching page: {forums}")
        response = requests.get(forums)
        if response.status_code != 200:
            print("[patch_link] Failed to fetch the forum page.")
            break

        soup = BeautifulSoup(response.text, 'html.parser')

        threads = soup.find_all("div", class_="structItem--thread")

        for thread in threads[1:]:
            link_container = thread.find("div", class_="structItem-title")
            if link_container:
                link_tag = link_container.find("a", href=True)
                if link_tag:
                    link = "https://forums.playdeadlock.com" + link_tag['href']
                    print(f"[patch_link] Found link: {link}")

                    content, timestamp, title, date = patch_content(link)
                    if content and timestamp:
                        patches_data.append((title, content, link, timestamp, date))

        next_page = soup.find("a", class_="pageNav-jump--next", href=True)
        if next_page:
            forums = "https://forums.playdeadlock.com" + next_page['href']
        else:
            forums = None

    for title, content, link, timestamp, date in reversed(patches_data):
        insert_patch(title, content, link, timestamp, date)

if __name__ == "__main__":
    scrapper()
