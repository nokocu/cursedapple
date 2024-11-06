import sqlite3
import requests
from bs4 import BeautifulSoup


def patch_link(forums="https://forums.playdeadlock.com/forums/changelog.10/"):
    response = requests.get(forums)
    if response.status_code != 200:
        print("[patch_link] Failed to fetch the forum page.")
        return None
    else:
        print(f"[patch_link] {response.status_code=}")

    soup = BeautifulSoup(response.text, 'html.parser')
    threads = soup.find_all("div", class_="structItem--thread")
    latest_thread = threads[1]
    link_container = latest_thread.find("div", class_="structItem-title")
    if link_container:
        link_tag = link_container.find("a", href=True)
        if link_tag:
            print(f"[patch_link] Found link: {link_tag['href']}")
            return "https://forums.playdeadlock.com" + link_tag['href']

    print("[patch_link] Link tag not found!")
    return None


def is_patch_new(link):
    conn = sqlite3.connect("patch.db")
    c = conn.cursor()
    c.execute("SELECT id FROM patches WHERE link = ?", (link,))
    result = c.fetchone()
    conn.close()
    return result is None


def patch_content(link):
    response = requests.get(link)
    if response.status_code != 200:
        print("[patch_content] Failed to fetch the patch page.")
        return None, None

    soup = BeautifulSoup(response.text, 'html.parser')

    content_div = soup.find("article", class_="message-body")
    if content_div:
        bb_wrapper = content_div.find("div", class_="bbWrapper")
        if bb_wrapper:
            content = str(bb_wrapper)
        else:
            print("[patch_content] no bbWrapper found!")
            return None, None
    else:
        print("[patch_content] no content_div found!")
        return None, None

    time_element = soup.find("time", class_="u-dt")
    timestamp = None
    if time_element:
        datetime = time_element.get('datetime')
        if datetime:
            timestamp = datetime

    return content, timestamp


def save_patch(link, content, timestamp):
    conn = sqlite3.connect("patch.db")
    c = conn.cursor()
    c.execute("INSERT INTO patches (link, content, timestamp) VALUES (?, ?, ?)", (link, content, timestamp))
    conn.commit()
    conn.close()


def check_for_patch():
    link = patch_link()
    if not link:
        print("[check_for_patch] patch_link returned no link")
        return False

    if not is_patch_new(link):
        print("[check_for_patch] Patch already exists in the database.")
        return False

    content, timestamp = patch_content(link)
    if content and timestamp:
        print("[check_for_patch] New Patch Found!")
        print(content)
        save_patch(link, content, timestamp)
        return True
    else:
        print("[check_for_patch] Failed to extract patch content or timestamp.")
        return False

