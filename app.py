import json
from datetime import datetime

from flask import Flask, render_template, request
from flask_apscheduler import APScheduler
from updater import check_for_patch
import sqlite3
import logging
from flask_babel import Babel, format_datetime

app = Flask(__name__)
database = "patch.db"
log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)


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


@scheduler.task('interval', id='check_for_patch_job', minutes=1)
def scheduled_check():
    # print("[scheduler] Checking for new patches...")
    # check_for_patch()
    pass


def get_patches():
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, title, content, content_filtered, link, timestamp, date FROM patches ORDER BY timestamp DESC")
    patches = c.fetchall()

    patches = [dict(patch) for patch in patches]

    for patch in patches:
        if patch['content_filtered']:
            patch['content_filtered'] = json.loads(patch['content_filtered'])

    c.execute("SELECT id, title, content, content_filtered, link, timestamp, date FROM patches WHERE id = (SELECT MAX(id) FROM patches)")
    newest = c.fetchone()
    conn.close()

    return patches, newest

def get_patch_by_id(patch_id):
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, title, content, content_filtered, link, timestamp, date FROM patches WHERE id = ?", (patch_id,))
    patch = c.fetchone()
    c.execute("SELECT id, title, content, content_filtered, link, timestamp, date FROM patches WHERE id = (SELECT MAX(id) FROM patches)")
    newest = c.fetchone()
    conn.close()

    if patch:
        patch = dict(patch)
        if patch['content_filtered']:
            patch['content_filtered'] = json.loads(patch['content_filtered'])
        return patch, newest
    return None


@app.route('/')
def home():
    patches = get_patches()
    return render_template('index.html', patches=patches[0], newest=patches[1])

@app.route('/patchnote/<int:id>')
def notes(id):
    patch = get_patch_by_id(id)
    if patch:
        return render_template('post.html', patch=patch[0], newest=patch[1])
    else:
        patches = get_patches()
        return render_template('index.html', patches=patches[0], newest=patches[1])

# time
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'
babel = Babel(app)

@app.template_filter('datetime_us')
def format_date_us(value):
    dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
    return dt.strftime("%B %d, %Y, %I:%M %p")

@app.template_filter('datetime_eu')
def format_date_eu(value):
    dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
    return dt.strftime("%B %d, %Y, %H:%M")

@app.template_filter('titledate')
def format_date_us(value):
    dt = datetime.strptime(value, "%m-%d-%Y")
    return dt.strftime("%B %d, %Y")

@app.template_filter('titlepic_eu')
def format_date_eu(value):
    dt = datetime.strptime(value, "%m-%d-%Y")
    return dt.strftime("%d.%m.%Y")


if __name__ == "__main__":
    check_for_patch()
    scheduler.start()
    app.run(host="0.0.0.0", port=5000, debug=True)
