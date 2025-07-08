# CursedApple - Deadlock Patchnotes Tracker

Full-stack web app for tracking Deadlock patch notes with analytics and REST API.

## What it does
- Tracks patch changes for heroes, items, and general game updates
- Shows balance trends and statistics
- Provides search functionality across all patches
- REST API for data access

## Tech Stack
Node.js, Express, SQLite, TypeScript, EJS templates

## Quick Start
```bash
npm install
npm run build:ts
npm start          # web app on :5000
npm run api        # api server on :3000
```

## API Endpoints
```
GET /api/health                    # status check
GET /api/patches                   # all patches with stats
GET /api/patches/:id              # detailed patch info
GET /api/search?hero=name         # search changes
GET /api/heroes                   # hero statistics  
GET /api/items?category=Weapon    # item stats by category
GET /api/analytics/heroes         # balance trends
```

## Database
SQLite with normalized schema:
- `patches` - patch metadata
- `heroes` - hero info and abilities  
- `items` - game items by category
- `patch_changes` - individual changes
- `patch_media` - associated files

## Scripts
```bash
# Data collection (Python)
python scripts/data-collection/patchscrapper.py
python scripts/migration/db_migration.py

# Development
npm run watch:ts   # typescript watch mode
npm run dev:full   # compile + dev server
```



