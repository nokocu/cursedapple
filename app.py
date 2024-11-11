import json
from pprint import pprint

from flask import Flask, render_template
from flask_apscheduler import APScheduler
from updater import check_for_patch
import sqlite3

app = Flask(__name__)
database = "patch.db"

class Config:
    SCHEDULER_API_ENABLED = True
app.config.from_object(Config)
scheduler = APScheduler()
scheduler.init_app(app)


def init_db():
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS patches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    link TEXT,
                    content TEXT,
                    content_filtered TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )''')
    conn.commit()
    conn.close()

init_db()


@scheduler.task('interval', id='check_for_patch_job', minutes=1)
def scheduled_check():
    # print("[scheduler] Checking for new patches...")
    # check_for_patch()
    pass


def get_patches():
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, link, content, content_filtered, timestamp FROM patches ORDER BY timestamp DESC")
    patches = c.fetchall()

    patches = [dict(patch) for patch in patches]

    for patch in patches:
        if patch['content_filtered']:
            patch['content_filtered'] = json.loads(patch['content_filtered'])

    conn.close()
    return patches


@app.route('/')
def home():
    patches = get_patches()
    return render_template('index.html', patches=patches)


if __name__ == "__main__":
    check_for_patch()
    scheduler.start()
    app.run(debug=True)
