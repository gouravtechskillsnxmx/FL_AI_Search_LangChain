const express = require('express');
const fetch = require('node-fetch');
const app = express();
app.use(express.static('public'));
app.use(express.json());
const PORT = 3000;
app.listen(PORT, ()=> console.log('Frontend server running on', PORT));
