// deadlock patchnotes api server
const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const cors = require('cors');
const helmet = require('helmet');
const path = require('path');
const config = require('./config');

const app = express();
const PORT = config.server.apiPort;
const DB_PATH = config.database.path;

// middleware
app.use(helmet());
app.use(cors());
app.use(express.json());

// database connection
const db = new sqlite3.Database(DB_PATH, (err) => {
    if (err) {
        console.error('database connection failed:', err.message);
        process.exit(1);
    }
    console.log('connected to sqlite database');
});

// error handler
const handleDbError = (res, err, message = 'database error') => {
    console.error(message, err);
    res.status(500).json({ error: message });
};

// routes

// get all patches with summary stats
app.get('/api/patches', (req, res) => {
    const query = `
        SELECT 
            p.id,
            p.version,
            p.release_date,
            COUNT(pc.id) as total_changes,
            COUNT(CASE WHEN pc.change_type = 'buff' THEN 1 END) as buffs,
            COUNT(CASE WHEN pc.change_type = 'nerf' THEN 1 END) as nerfs,
            COUNT(CASE WHEN pc.change_type = 'other' THEN 1 END) as other_changes,
            COUNT(DISTINCT pc.hero_id) as heroes_affected,
            COUNT(DISTINCT pc.item_id) as items_affected,
            COUNT(pm.id) as media_count
        FROM patches p
        LEFT JOIN patch_changes pc ON p.id = pc.patch_id
        LEFT JOIN patch_media pm ON p.id = pm.patch_id
        WHERE p.processed = 1
        GROUP BY p.id, p.version, p.release_date
        ORDER BY p.id DESC
        LIMIT 50
    `;
    
    db.all(query, [], (err, rows) => {
        if (err) return handleDbError(res, err, 'failed to fetch patches');
        res.json(rows);
    });
});

// get specific patch details
app.get('/api/patches/:id', (req, res) => {
    const patchId = req.params.id;
    
    // get patch info
    const patchQuery = `
        SELECT id, version, release_date, processed
        FROM patches 
        WHERE id = ?
    `;
    
    db.get(patchQuery, [patchId], (err, patch) => {
        if (err) return handleDbError(res, err, 'failed to fetch patch');
        if (!patch) return res.status(404).json({ error: 'patch not found' });
        
        // get hero changes
        const heroQuery = `
            SELECT 
                h.name as hero_name,
                pc.change_type,
                pc.description,
                pc.id
            FROM patch_changes pc
            JOIN heroes h ON pc.hero_id = h.id
            WHERE pc.patch_id = ?
            ORDER BY h.name, pc.change_type
        `;
        
        // get item changes
        const itemQuery = `
            SELECT 
                i.name as item_name,
                i.category,
                pc.change_type,
                pc.description,
                pc.id
            FROM patch_changes pc
            JOIN items i ON pc.item_id = i.id
            WHERE pc.patch_id = ?
            ORDER BY i.category, i.name, pc.change_type
        `;
        
        // get general changes
        const generalQuery = `
            SELECT change_type, description, category, id
            FROM patch_changes
            WHERE patch_id = ? AND hero_id IS NULL AND item_id IS NULL
            ORDER BY change_type, description
        `;
        
        // get media
        const mediaQuery = `
            SELECT media_type, file_path, description, id
            FROM patch_media
            WHERE patch_id = ?
            ORDER BY media_type, file_path
        `;
        
        // execute all queries
        Promise.all([
            new Promise((resolve, reject) => {
                db.all(heroQuery, [patchId], (err, rows) => {
                    if (err) reject(err);
                    else resolve(rows);
                });
            }),
            new Promise((resolve, reject) => {
                db.all(itemQuery, [patchId], (err, rows) => {
                    if (err) reject(err);
                    else resolve(rows);
                });
            }),
            new Promise((resolve, reject) => {
                db.all(generalQuery, [patchId], (err, rows) => {
                    if (err) reject(err);
                    else resolve(rows);
                });
            }),
            new Promise((resolve, reject) => {
                db.all(mediaQuery, [patchId], (err, rows) => {
                    if (err) reject(err);
                    else resolve(rows);
                });
            })
        ]).then(([heroChanges, itemChanges, generalChanges, media]) => {
            res.json({
                patch,
                hero_changes: heroChanges,
                item_changes: itemChanges,
                general_changes: generalChanges,
                media
            });
        }).catch(err => handleDbError(res, err, 'failed to fetch patch details'));
    });
});

// search changes by hero/item/text
app.get('/api/search', (req, res) => {
    const { hero, item, text, change_type, limit = 100 } = req.query;
    
    let query = `
        SELECT 
            pc.id,
            pc.patch_id,
            p.version,
            pc.change_type,
            pc.description,
            h.name as hero_name,
            i.name as item_name,
            i.category as item_category
        FROM patch_changes pc
        LEFT JOIN patches p ON pc.patch_id = p.id
        LEFT JOIN heroes h ON pc.hero_id = h.id
        LEFT JOIN items i ON pc.item_id = i.id
        WHERE 1=1
    `;
    
    const params = [];
    
    if (hero) {
        query += ` AND LOWER(h.name) LIKE LOWER(?)`;
        params.push(`%${hero}%`);
    }
    
    if (item) {
        query += ` AND LOWER(i.name) LIKE LOWER(?)`;
        params.push(`%${item}%`);
    }
    
    if (text) {
        query += ` AND LOWER(pc.description) LIKE LOWER(?)`;
        params.push(`%${text}%`);
    }
    
    if (change_type) {
        query += ` AND pc.change_type = ?`;
        params.push(change_type);
    }
    
    query += ` ORDER BY pc.patch_id DESC, pc.id LIMIT ?`;
    params.push(parseInt(limit));
    
    db.all(query, params, (err, rows) => {
        if (err) return handleDbError(res, err, 'search failed');
        res.json(rows);
    });
});

// get hero statistics
app.get('/api/heroes', (req, res) => {
    const query = `
        SELECT 
            h.name,
            h.ability1,
            h.ability2,
            h.ability3,
            h.ability4,
            COUNT(pc.id) as total_changes,
            COUNT(CASE WHEN pc.change_type = 'buff' THEN 1 END) as buffs,
            COUNT(CASE WHEN pc.change_type = 'nerf' THEN 1 END) as nerfs,
            COUNT(CASE WHEN pc.change_type = 'other' THEN 1 END) as other_changes
        FROM heroes h
        LEFT JOIN patch_changes pc ON h.id = pc.hero_id
        GROUP BY h.id, h.name, h.ability1, h.ability2, h.ability3, h.ability4
        ORDER BY total_changes DESC, h.name
    `;
    
    db.all(query, [], (err, rows) => {
        if (err) return handleDbError(res, err, 'failed to fetch heroes');
        res.json(rows);
    });
});

// get item statistics by category
app.get('/api/items', (req, res) => {
    const { category } = req.query;
    
    let query = `
        SELECT 
            i.name,
            i.category,
            COUNT(pc.id) as total_changes,
            COUNT(CASE WHEN pc.change_type = 'buff' THEN 1 END) as buffs,
            COUNT(CASE WHEN pc.change_type = 'nerf' THEN 1 END) as nerfs,
            COUNT(CASE WHEN pc.change_type = 'other' THEN 1 END) as other_changes
        FROM items i
        LEFT JOIN patch_changes pc ON i.id = pc.item_id
    `;
    
    const params = [];
    
    if (category) {
        query += ` WHERE i.category = ?`;
        params.push(category);
    }
    
    query += `
        GROUP BY i.id, i.name, i.category
        ORDER BY i.category, total_changes DESC, i.name
    `;
    
    db.all(query, params, (err, rows) => {
        if (err) return handleDbError(res, err, 'failed to fetch items');
        res.json(rows);
    });
});

// analytics endpoint - hero balance trends
app.get('/api/analytics/heroes', (req, res) => {
    const query = `
        WITH hero_stats AS (
            SELECT 
                h.name,
                COUNT(CASE WHEN pc.change_type = 'buff' THEN 1 END) as total_buffs,
                COUNT(CASE WHEN pc.change_type = 'nerf' THEN 1 END) as total_nerfs,
                COUNT(pc.id) as total_changes
            FROM heroes h
            LEFT JOIN patch_changes pc ON h.id = pc.hero_id
            GROUP BY h.id, h.name
            HAVING total_changes > 0
        )
        SELECT 
            name,
            total_buffs,
            total_nerfs,
            total_changes,
            (total_buffs - total_nerfs) as balance_score,
            CASE 
                WHEN total_buffs > total_nerfs THEN 'buffed_overall'
                WHEN total_nerfs > total_buffs THEN 'nerfed_overall'
                ELSE 'balanced'
            END as trend
        FROM hero_stats
        ORDER BY balance_score DESC, total_changes DESC
    `;
    
    db.all(query, [], (err, rows) => {
        if (err) return handleDbError(res, err, 'analytics query failed');
        res.json(rows);
    });
});

// health check
app.get('/api/health', (req, res) => {
    db.get('SELECT COUNT(*) as count FROM patches', (err, row) => {
        if (err) return res.status(500).json({ status: 'error', error: err.message });
        res.json({ 
            status: 'healthy', 
            database: 'connected',
            patches: row.count,
            timestamp: new Date().toISOString()
        });
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({ error: 'endpoint not found' });
});

// start server
app.listen(PORT, () => {
    console.log(`deadlock patchnotes api running on port ${PORT}`);
    console.log(`health check: http://localhost:${PORT}/api/health`);
});

// graceful shutdown
process.on('SIGINT', () => {
    console.log('shutting down server...');
    db.close((err) => {
        if (err) console.error('error closing database:', err.message);
        else console.log('database connection closed');
        process.exit(0);
    });
});
