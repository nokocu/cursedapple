// simple static file server for frontend testing
const express = require('express');
const path = require('path');

const app = express();
const PORT = 8080;

// serve static files
app.use('/static', express.static(path.join(__dirname, 'static')));

// serve main html file
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
    console.log(`frontend server running on http://localhost:${PORT}`);
    console.log('make sure api server is running on port 3000');
});
