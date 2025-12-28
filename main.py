import asyncio
import json
import logging
import os
from typing import List, Dict

import discord
from discord.ext import commands
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("Main")

class SelfBot(commands.Bot):
    def __init__(self, account_config, owner_id=None, *args, **kwargs):
        self.account_config = account_config
        self.name = account_config['name']
        super().__init__(command_prefix=account_config['prefix'], self_bot=True, owner_id=owner_id, *args, **kwargs)

    async def on_ready(self):
        logger.info(f"[Account: {self.name}] Logged in as {self.user}")

    async def setup_hook(self):
        cogs = ['cogs.account', 'cogs.nuke', 'cogs.misc', 'cogs.troll', 'cogs.help', 'cogs.hosting']

        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"[Account: {self.name}] Loaded {cog}")
            except Exception as e:
                logger.error(f"[Account: {self.name}] Failed to load {cog}: {e}")

app = FastAPI()
bots: Dict[str, SelfBot] = {}

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    bot_info = []
    for name, bot in bots.items():
        status = "Online" if bot.is_ready() else "Connecting/Offline"
        user = str(bot.user) if bot.user else "Unknown"
        prefix = bot.command_prefix
        bot_info.append({"name": name, "status": status, "user": user, "prefix": prefix})

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Rishu Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg: #050505;
                --card-bg: rgba(20, 20, 20, 0.7);
                --accent: transparent;
                --accent-hover: #232323;
                --text: #ffffff;
                --text-muted: #a0a0a0;
                --border: rgba(255, 255, 255, 0.05);
                --success: #4ade80;
                --error: #f87171;
            }}
            body {{ 
                font-family: 'Outfit', sans-serif; 
                background: var(--bg); 
                color: var(--text); 
                margin: 0; 
                padding: 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                overflow-x: hidden;
            }}
            .card {{ 
                background: var(--card-bg); 
                backdrop-filter: blur(12px);
                border: 1px solid var(--border); 
                border-radius: 20px; 
                padding: 30px; 
                width: 100%;
                max-width: 500px; 
                box-shadow: 0 20px 50px rgba(0,0,0,0.8); 
                display: flex;
                flex-direction: column;
            }}
            h1 {{ 
                font-size: 1.8rem; 
                margin-top: 0; 
                margin-bottom: 20px;
                color: #fff; 
                font-weight: 600;
                text-align: center;
            }}
            .bot-list {{ margin-bottom: 20px; }}
            .bot-row {{ 
                display: flex; 
                align-items: center; 
                justify-content: space-between; 
                padding: 12px 15px; 
                background: rgba(255,255,255,0.02);
                border-radius: 12px;
                margin-bottom: 8px;
                border: 1px solid var(--border);
                transition: transform 0.2s;
            }}
            .bot-row:hover {{ transform: translateX(5px); }}
            .bot-name {{ font-weight: 400; }}
            .bot-prefix {{ font-size: 0.8rem; color: var(--text-muted); margin-left: 8px; font-family: monospace; }}
            .status {{ font-size: 0.7rem; padding: 3px 8px; border-radius: 20px; font-weight: 600; text-transform: uppercase; }}
            .online {{ background: rgba(74, 222, 128, 0.1); color: var(--success); border: 1px solid rgba(74, 222, 128, 0.2); }}
            .offline {{ background: rgba(248, 113, 113, 0.1); color: var(--error); border: 1px solid rgba(248, 113, 113, 0.2); }}
            .input-group {{ margin-top: 10px; display: flex; flex-direction: column; gap: 12px; }}
            .flex-row {{ display: flex; gap: 10px; }}
            input, select {{ 
                background: rgba(255,255,255,0.05); 
                border: 1px solid var(--border); 
                color: #fff; 
                padding: 10px 14px; 
                border-radius: 10px; 
                font-size: 0.95rem;
                outline: none;
                transition: border 0.3s;
            }}
            input:focus, select:focus {{ border-color: var(--accent); }}
            button {{ 
                background: var(--accent); 
                color: #fff; 
                border: none; 
                padding: 10px 20px; 
                border-radius: 10px; 
                cursor: pointer; 
                font-weight: 600;
                font-size: 0.95rem;
                transition: background 0.3s, transform 0.1s;
            }}
            button:hover {{ background: var(--accent-hover); }}
            button:active {{ transform: scale(0.98); }}
            #logs {{ 
                margin-top: 20px; 
                background: #000; 
                border: 1px solid var(--border); 
                padding: 12px; 
                height: 150px; 
                overflow-y: auto; 
                font-family: 'Consolas', monospace; 
                font-size: 0.8rem; 
                border-radius: 12px; 
                color: #72f272; 
                line-height: 1.4;
            }}
            .log-entry {{ margin-bottom: 2px; }}
            .log-cmd {{ color: #5865f2; }}
            .log-res {{ color: #aaa; margin-left: 10px; font-style: italic; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Rishu Dashboard</h1>
            <div class="bot-list" id="bots">
                {"".join([f'<div class="bot-row" id="bot-{b["name"]}"><span class="bot-name">{b["name"]}<span class="bot-prefix">{b["prefix"]}</span></span><span class="status {b["status"].lower().replace("/", "-")[:7]}">{b["status"]}</span></div>' for b in bot_info])}
            </div>
            <div class="input-group">
                <div class="flex-row">
                    <select id="botSelect" style="flex: 1;">
                        {"".join([f'<option value="{name}">{name}</option>' for name in bots.keys()])}
                    </select>
                </div>
                <div class="flex-row">
                    <input type="text" id="command" placeholder="Enter command..." style="flex: 1;">
                    <button onclick="executeCommand()">Run</button>
                </div>
            </div>
            </div>
        </div>
        <script>

            async function updateStatus() {{
                try {{
                    const response = await fetch('/status');
                    const data = await response.json();
                    const botsDiv = document.getElementById('bots');
                    const select = document.getElementById('botSelect');
                    const currentSelection = select.value;

                    let html = '';
                    let selectHtml = '';
                    data.forEach(b => {{
                        const statusClass = b.status.toLowerCase().replace('/', '-').substring(0, 7);
                        html += `<div class="bot-row" id="bot-${{b.name}}">
                                    <span class="bot-name">${{b.name}}<span class="bot-prefix">${{b.prefix}}</span></span>
                                    <span class="status ${{statusClass}}">${{b.status}}</span>
                                 </div>`;
                        selectHtml += `<option value="${{b.name}}" ${{b.name === currentSelection ? 'selected' : ''}}>${{b.name}}</option>`;
                    }});
                    botsDiv.innerHTML = html;
                    select.innerHTML = selectHtml;
                }} catch (e) {{
                    console.error("Status update failed", e);
                }}
            }}

            setInterval(updateStatus, 3000);

            async function executeCommand() {{
                const botName = document.getElementById('botSelect').value;
                const cmd = document.getElementById('command').value;
                const log = document.getElementById('logs');
                
                if(!cmd) return;

                const entry = document.createElement('div');
                entry.className = 'log-entry';
                entry.innerHTML = `<span class="log-cmd">> ${{botName}}:</span> ${{cmd}}`;
                log.appendChild(entry);
                log.scrollTop = log.scrollHeight;
                
                try {{
                    const response = await fetch('/execute', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                        body: `name=${{encodeURIComponent(botName)}}&command=${{encodeURIComponent(cmd)}}`
                    }});
                    const result = await response.json();
                    
                    const resEntry = document.createElement('div');
                    resEntry.className = 'log-entry';
                    resEntry.innerHTML = `<span class="log-res">${{result.message}}</span>`;
                    log.appendChild(resEntry);
                }} catch (e) {{
                    const errEntry = document.createElement('div');
                    errEntry.className = 'log-entry';
                    errEntry.innerHTML = `<span style="color: #f87171">Error: ${{e.message}}</span>`;
                    log.appendChild(errEntry);
                }}
                log.scrollTop = log.scrollHeight;
                document.getElementById('command').value = '';
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/status")
async def get_status():
    bot_info = []
    for name, bot in bots.items():
        status = "Online" if bot.is_ready() else "Connecting/Offline"
        prefix = bot.command_prefix
        bot_info.append({"name": name, "status": status, "prefix": prefix})
    return JSONResponse(content=bot_info)

    return JSONResponse(content=bot_info)

@app.post("/execute")
async def execute(name: str = Form(...), command: str = Form(...)):
    if name not in bots:
        return JSONResponse({"status": "error", "message": "Bot not found"}, status_code=404)
    
    bot = bots[name]
    
    class MockMessage:
        def __init__(self, content, author, bot, channel):
            self.content = content
            self.author = author
            self.channel = channel
            self.guild = getattr(channel, 'guild', None)
            self._state = getattr(channel, '_state', getattr(bot, '_connection', None))
            self.id = 0
            self.nonce = None
            self.attachments = []
            self.embeds = []
            self.mentions = []
            self.role_mentions = []
            self.channel_mentions = []
            self.mention_everyone = False
            self.pinned = False
            self.tts = False
            self.type = discord.MessageType.default
            self.flags = discord.MessageFlags()
            self.reference = None
            self.components = []
            self.stickers = []
            self.edited_at = None
            self.created_at = discord.utils.utcnow()

        async def delete(self, *, delay=None):
            pass

        async def reply(self, content=None, **kwargs):
            return await self.channel.send(content, **kwargs)

    target_channel = None
    log_info = ""
    if bot.guilds:
        for guild in bot.guilds:
            if guild.text_channels:
                target_channel = guild.text_channels[0]
                log_info = f"Guild: {guild.name}"
                break
    
    if not target_channel:
        target_channel = bot.user
        log_info = "DMs (No guilds found)"

    full_command = command if command.startswith(bot.command_prefix) else f"{bot.command_prefix}{command}"
    logger.info(f"Dashboard Exec: [{name}] {full_command} in {log_info}")
    
    mock_msg = MockMessage(full_command, bot.user, bot, target_channel)
    asyncio.create_task(bot.process_commands(mock_msg))

    return JSONResponse({"status": "success", "message": f"Command processed for {name} ({log_info})"})

async def start_bot(name, token, prefix="!", owner_id=None):
    if name in bots:
        logger.warning(f"Bot {name} is already running. Stopping it first...")
        await stop_bot(name)

    acc = {"name": name, "token": token, "prefix": prefix}
    bot = SelfBot(acc, owner_id=owner_id)
    bots[name] = bot
    asyncio.create_task(bot.start(token))
    logger.info(f"Bot {name} started.")
    return bot

async def stop_bot(name):
    if name in bots:
        bot = bots[name]
        try:
            await bot.close()
        except: pass
        if name in bots:
            del bots[name]
        logger.info(f"Bot {name} stopped.")
    else:
        logger.warning(f"Bot {name} not found to stop.")

async def run_bots(config):
    owner_id = config.get('owner_id')
    for acc in config['accounts']:
        if acc['token'] == "YOUR_TOKEN_HERE":
            continue
        await start_bot(acc['name'], acc['token'], acc.get('prefix', '!'), owner_id=owner_id)

async def main():
    if not os.path.exists("config.json"):
        logger.error("config.json not found!")
        return

    with open("config.json", "r") as f:
        config = json.load(f)

    await run_bots(config)

    config_api = uvicorn.Config(app, host=config['dashboard']['host'], port=config['dashboard']['port'], log_level="info")
    server = uvicorn.Server(config_api)
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
