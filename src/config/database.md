# Database Configuration

Database connection settings and schema information.

## Connection Details

- **Type**: SQLite3
- **Location**: `../database/patch.db`
- **Connection Pool**: Single connection with proper error handling

## Schema Overview

### Tables

1. **patches**
   - Primary table for patch information
   - Indexes: id (primary), version, release_date

2. **heroes**
   - Deadlock heroes with abilities
   - Indexes: id (primary), name

3. **items**
   - Game items with categories
   - Indexes: id (primary), name, category

4. **patch_changes**
   - Individual changes linked to patches
   - Foreign keys: patch_id, hero_id, item_id
   - Indexes: patch_id, hero_id, item_id, change_type

5. **patch_media**
   - Media files associated with patches
   - Foreign key: patch_id

## Migration Scripts

Located in `../scripts/migration/`:
- `db_migration.py` - Initial schema creation
- `populate_items.py` - Populate items table
- `verify_schema.py` - Schema verification

## Backup Strategy

- Database backups should be created before major migrations
- Use SQLite's backup commands for production deployments

## Performance Considerations

- Proper indexes on frequently queried columns
- Connection pooling for high-traffic scenarios
- Query optimization for analytics endpoints
