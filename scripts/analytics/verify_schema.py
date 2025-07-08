import sqlite3

def verify_schema():
    conn = sqlite3.connect('patch.db')
    cursor = conn.cursor()
    
    print('=== PROFESSIONAL DATABASE SCHEMA ===')
    print()
    
    # show all tables
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name NOT LIKE "%backup%"')
    tables = [row[0] for row in cursor.fetchall()]
    print('✓ tables:', ', '.join(tables))
    print()
    
    # show data counts
    cursor.execute('SELECT COUNT(*) FROM patches')
    print(f'patches: {cursor.fetchone()[0]}')
    
    cursor.execute('SELECT COUNT(*) FROM heroes') 
    print(f'heroes: {cursor.fetchone()[0]}')
    
    cursor.execute('SELECT COUNT(*) FROM items')
    print(f'items: {cursor.fetchone()[0]}')
    
    cursor.execute('SELECT COUNT(*) FROM patch_changes')
    print(f'patch changes: {cursor.fetchone()[0]}')
    
    cursor.execute('SELECT COUNT(*) FROM patch_media')
    print(f'media files: {cursor.fetchone()[0]}')
    print()
    
    # show schema structure
    print('schema overview:')
    print('├── patches (main patch data)')
    print('├── heroes (all game heroes + abilities)')  
    print('├── items (all game items by category)')
    print('├── patch_changes (normalized change tracking)')
    print('└── patch_media (images/videos per patch)')
    print()
    
    # show sample data
    print('sample data:')
    cursor.execute('SELECT name FROM heroes LIMIT 3')
    heroes = [row[0] for row in cursor.fetchall()]
    print(f'heroes: {", ".join(heroes)}...')
    
    cursor.execute('SELECT category, COUNT(*) FROM items GROUP BY category')
    for category, count in cursor.fetchall():
        print(f'{category.lower()} items: {count}')
    
    conn.close()

if __name__ == "__main__":
    verify_schema()
