const express = require('express');
const http = require('http');
const WebSocket = require('ws');

const app = express();
const PORT = 5000;
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

app.use(express.json());


let commandQueue = [];
let currentTradeRule = {
    triggerPercent: 40.0,
    moveToBE: true,
    closePercent: 50.0,
    auto_trading_enabled: true
};
const clients = new Set();

wss.on('connection', (ws) => {
    console.log('[WebSocket]  Python dashboard connected✅.');
    clients.add(ws);
    ws.send(JSON.stringify({ type: 'settings', data: currentTradeRule }));
    ws.on('close', () => {
        console.log('[WebSocket]  The dashboard was disconnected❌.');
        clients.delete(ws);
    });
});

app.post('/data', (req, res) => {
    const jsonData = req.body;
    // console.log(jsonData);
    
    if (!jsonData || typeof jsonData !== 'object') {
      return res.status(400).json({ status: 'error', message: 'Invalid JSON data' });
    }
  
    try {
      broadcast({ type: 'trade_data', data: jsonData });
      res.status(200).json({ status: 'success' });
    } catch (error) {
      console.error("Error broadcasting data:", error);
      res.status(500).json({ status: 'error', message: 'Internal server error' });
    }
  });
  






app.post('/command', (req, res) => {
    const command = req.body;
    if (command && command.action) {
        console.log(`[Python -> Server] New command received🔵.`, command);
        if (command.action === 'update_settings') {
            currentTradeRule = { ...currentTradeRule, ...command.settings };
            broadcast({ type: 'settings', data: currentTradeRule });
        } else if (command.action === 'toggle_auto') {
            currentTradeRule.auto_trading_enabled = command.auto_state;
            broadcast({ type: 'settings', data: currentTradeRule });
        } else {
            commandQueue.push(command);
        }
        res.status(200).json({ status: 'success' });
    } else {
        res.status(400).json({ status: 'error' });
    }
});

app.get('/get-command', (req, res) => {
    if (commandQueue.length > 0) res.status(200).json(commandQueue.shift());
    else res.status(200).json({ status: 'no command' });
});

app.get('/get-settings', (req, res) => {
    res.status(200).json(currentTradeRule);
});

function broadcast(messageObject) {
    const message = JSON.stringify(messageObject);
    for (const client of clients) {
        if (client.readyState === WebSocket.OPEN) client.send(message);
    }
}

server.listen(PORT, '0.0.0.0', () => {
  console.log("=============================================");
  console.log(`🚀server is running...`);
  console.log(`http://127.0.0.1:${PORT}`);
  console.log("=============================================");
});