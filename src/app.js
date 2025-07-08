// Deadlock patch notes tracker - Node.js application
const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const config = require('./config');

const app = express();
const PORT = config.server.port;
const DB_PATH = config.database.path;

// template engine setup
app.set('view engine', 'ejs');
app.set('views', config.paths.views);

// static files
app.use('/static', express.static(config.paths.static));

// database connection
const db = new sqlite3.Database(DB_PATH, (err) => {
    if (err) {
        console.error('database connection failed:', err.message);
        process.exit(1);
    }
    console.log('connected to sqlite database');
});

// helper functions for date formatting (matching your flask filters)
const formatDateUS = (dateString) => {
    if (!dateString) return '';
    try {
        const dt = new Date(dateString);
        return dt.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });
    } catch (e) {
        return dateString;
    }
};

const formatDateEU = (dateString) => {
    if (!dateString) return '';
    try {
        const dt = new Date(dateString);
        return dt.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            hour12: false
        });
    } catch (e) {
        return dateString;
    }
};

const formatTitleDate = (dateString) => {
    if (!dateString) return '';
    try {
        // assuming date format is mm-dd-yyyy from old system
        const parts = dateString.split('-');
        if (parts.length === 3) {
            const dt = new Date(parts[2], parts[0] - 1, parts[1]);
            return dt.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric'
            });
        }
        return dateString;
    } catch (e) {
        return dateString;
    }
};

const formatTitlePicEU = (dateString) => {
    if (!dateString) return '';
    try {
        const parts = dateString.split('-');
        if (parts.length === 3) {
            return `${parts[1]}.${parts[0]}.${parts[2]}`;
        }
        return dateString;
    } catch (e) {
        return dateString;
    }
};

// database functions that match your flask logic but use our new schema
const getPatches = () => {
    return new Promise((resolve, reject) => {
        const query = `
            SELECT 
                p.id,
                p.version as title,
                p.raw_content as content,
                p.release_date as timestamp,
                p.version as date
            FROM patches p
            WHERE p.processed = 1
            ORDER BY p.id DESC
            LIMIT 50
        `;
        
        db.all(query, [], (err, rows) => {
            if (err) {
                reject(err);
                return;
            }
            
            // process each patch to get change counts (matching your old structure)
            const processedPatches = rows.map(patch => {
                // get hero and item counts for this patch
                const heroQuery = `SELECT COUNT(DISTINCT hero_id) as count FROM patch_changes WHERE patch_id = ? AND hero_id IS NOT NULL`;
                const itemQuery = `SELECT COUNT(DISTINCT item_id) as count FROM patch_changes WHERE patch_id = ? AND item_id IS NOT NULL`;
                
                // for now, create a structure that matches your templates
                const contentFiltered = {
                    '[ Heroes ]': {},
                    '[ Items ]': {
                        'Weapon': {},
                        'Spirit': {},
                        'Vitality': {}
                    }
                };
                
                // simulate the old structure for template compatibility
                // we'll populate this with actual data in a more efficient way later
                return {
                    ...patch,
                    content_filtered: contentFiltered
                };
            });
            
            resolve(processedPatches);
        });
    });
};

const getPatchById = (patchId) => {
    return new Promise((resolve, reject) => {
        // get patch basic info
        const patchQuery = `
            SELECT 
                p.id,
                p.version as title,
                p.raw_content as content,
                p.release_date as timestamp,
                p.version as date
            FROM patches p
            WHERE p.id = ?
        `;
        
        db.get(patchQuery, [patchId], (err, patch) => {
            if (err) {
                reject(err);
                return;
            }
            
            if (!patch) {
                resolve(null);
                return;
            }
            
            // get hero changes for this patch
            const heroQuery = `
                SELECT 
                    h.name as hero_name,
                    pc.change_type,
                    pc.description
                FROM patch_changes pc
                JOIN heroes h ON pc.hero_id = h.id
                WHERE pc.patch_id = ?
                ORDER BY h.name, pc.change_type
            `;
            
            // get item changes for this patch
            const itemQuery = `
                SELECT 
                    i.name as item_name,
                    i.category,
                    pc.change_type,
                    pc.description
                FROM patch_changes pc
                JOIN items i ON pc.item_id = i.id
                WHERE pc.patch_id = ?
                ORDER BY i.category, i.name, pc.change_type
            `;
            
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
                })
            ]).then(([heroChanges, itemChanges]) => {
                // organize data to match your template structure
                const contentFiltered = {
                    '[ Heroes ]': {},
                    '[ Items ]': {
                        'Weapon': {},
                        'Spirit': {},
                        'Vitality': {}
                    }
                };
                
                // group hero changes by hero name and type
                heroChanges.forEach(change => {
                    if (!contentFiltered['[ Heroes ]'][change.hero_name]) {
                        contentFiltered['[ Heroes ]'][change.hero_name] = {
                            'buff': [],
                            'nerf': [],
                            'other': []
                        };
                    }
                    contentFiltered['[ Heroes ]'][change.hero_name][change.change_type].push(change.description);
                });
                
                // group item changes by category, item name, and type
                itemChanges.forEach(change => {
                    if (!contentFiltered['[ Items ]'][change.category][change.item_name]) {
                        contentFiltered['[ Items ]'][change.category][change.item_name] = {
                            'buff': [],
                            'nerf': [],
                            'other': []
                        };
                    }
                    contentFiltered['[ Items ]'][change.category][change.item_name][change.change_type].push(change.description);
                });
                
                patch.content_filtered = contentFiltered;
                resolve(patch);
                
            }).catch(reject);
        });
    });
};

const getNewestPatch = () => {
    return new Promise((resolve, reject) => {
        const query = `
            SELECT 
                p.id,
                p.version as title,
                p.raw_content as content,
                p.release_date as timestamp,
                p.version as date
            FROM patches p
            WHERE p.processed = 1
            ORDER BY p.id DESC
            LIMIT 1
        `;
        
        db.get(query, [], (err, row) => {
            if (err) reject(err);
            else resolve(row);
        });
    });
};

// template helpers (matching your flask filters)
app.locals.formatDateUS = formatDateUS;
app.locals.formatDateEU = formatDateEU;
app.locals.formatTitleDate = formatTitleDate;
app.locals.formatTitlePicEU = formatTitlePicEU;

// routes matching your flask app
app.get('/', async (req, res) => {
    try {
        const [patches, newest] = await Promise.all([
            getPatches(),
            getNewestPatch()
        ]);
        
        res.render('index', { 
            patches, 
            newest,
            // template helpers
            datetime_us: formatDateUS,
            datetime_eu: formatDateEU,
            titledate: formatTitleDate,
            titlepic_eu: formatTitlePicEU
        });
    } catch (error) {
        console.error('error loading home page:', error);
        res.status(500).send('server error');
    }
});

app.get('/patchnote/:id', async (req, res) => {
    try {
        const patchId = parseInt(req.params.id);
        const [patch, newest] = await Promise.all([
            getPatchById(patchId),
            getNewestPatch()
        ]);
        
        if (!patch) {
            // redirect to home if patch not found
            return res.redirect('/');
        }
        
        res.render('post', { 
            patch, 
            newest,
            // template helpers
            datetime_us: formatDateUS,
            datetime_eu: formatDateEU,
            titledate: formatTitleDate,
            titlepic_eu: formatTitlePicEU
        });
    } catch (error) {
        console.error('error loading patch:', error);
        res.redirect('/');
    }
});

// health check
app.get('/health', (req, res) => {
    res.json({ 
        status: 'healthy',
        server: 'node.js + ejs',
        timestamp: new Date().toISOString()
    });
});

// start server
app.listen(PORT, () => {
    console.log(`CursedApple patchnotes server running on port ${PORT}`);
    console.log(`visit: http://localhost:${PORT}`);
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
