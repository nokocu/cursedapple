// Application configuration
const path = require('path');

const config = {
    // Server configuration
    server: {
        port: process.env.PORT || 5000,
        apiPort: process.env.API_PORT || 3000,
        host: process.env.HOST || 'localhost'
    },
    
    // Database configuration
    database: {
        path: path.join(__dirname, '../../database/patch.db'),
        options: {
            verbose: console.log // Set to null in production
        }
    },
    
    // Paths configuration
    paths: {
        views: path.join(__dirname, '../views'),
        static: path.join(__dirname, '../../public/static'),
        scripts: path.join(__dirname, '../../scripts'),
        docs: path.join(__dirname, '../../docs')
    },
    
    // API configuration
    api: {
        baseUrl: '/api',
        defaultLimit: 50,
        maxLimit: 1000,
        timeout: 30000
    },
    
    // Environment
    env: process.env.NODE_ENV || 'development',
    
    // Security
    security: {
        helmet: true,
        cors: true,
        rateLimiting: false // Enable in production
    }
};

module.exports = config;
