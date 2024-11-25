import sqlite3
import requests
from bs4 import BeautifulSoup
from patchscrapper import patch_content, insert_patch

def scrapper_updater(forums="https://forums.playdeadlock.com/forums/changelog.10/"):
    response = requests.get(forums)
    if response.status_code != 200:
        print("[scrapper_updater] Failed to fetch the forum page.")
        return None
    else:
        print(f"[scrapper_updater] {response.status_code=}")

    soup = BeautifulSoup(response.text, 'html.parser')
    threads = soup.find_all("div", class_="structItem--thread")
    latest_thread = threads[1]
    link_container = latest_thread.find("div", class_="structItem-title")
    if link_container:
        link_tag = link_container.find("a", href=True)
        if link_tag:
            print(f"[scrapper_updater] Found link: {link_tag['href']}")
            return "https://forums.playdeadlock.com" + link_tag['href']

    print("[scrapper_updater] Link tag not found!")
    return None


def is_patch_new(link):
    conn = sqlite3.connect("patch.db")
    c = conn.cursor()
    c.execute("SELECT id FROM patches WHERE link = ?", (link,))
    result = c.fetchone()
    conn.close()
    return result is None


def check_for_patch():
    link = scrapper_updater()
    if not link:
        print("[check_for_patch] scrapper_updater returned no link")
        return False

    if not is_patch_new(link):
        print("[check_for_patch] Patch already exists in the database.")
        return False

    content, timestamp, title, date = patch_content(link)

    if content and timestamp:
        print("[check_for_patch] New Patch Found!")
        print(content)
        insert_patch(title, content, link, timestamp, date)
        return True
    else:
        print("[check_for_patch] Failed to extract patch content or timestamp.")
        return False

