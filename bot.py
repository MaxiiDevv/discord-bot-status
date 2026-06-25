import os
import asyncio
import discord
import aiohttp
import pytz

from discord.ext import commands, tasks
from datetime import datetime
from aiohttp import web

# =========================
# KONFIGURACJA
# =========================
TOKEN = os.environ.get("TOKEN")
GUILD_ID = 1462813807679115401
CHANNEL_ID = 1462835903629103206

# Zmieniono na adres fizyczny, który lepiej współpracuje z API
SERVER_IP = "tapir.aternos.host"

ALLOWED_ROLES = [
    1463171621811519570,
    1491760080444592138,
    1463171617713684480,
    1518158676605534208,
    1519056707148316853,
    1463171602681430016
]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.status_message_id = None
MY_GUILD = discord.Object(id=GUILD_ID)

# =========================
# WEB SERVER (KEEP ALIVE)
# =========================
async def handle(request):
    return web.Response(text="Bot jest aktywny!")

async def start_web_server():
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()

# =========================
# FUNKCJE POMOCNICZE
# =========================
def has_permission(member):
    return any(role.id in ALLOWED_ROLES for role in member.roles)

def build_embed(is_online, players="0", max_players="0"):
    warsaw_tz = pytz.timezone("Europe/Warsaw")
    now = datetime.now(warsaw_tz).strftime("%d.%m.%Y • %H:%M")
    
    title = "🟢 | STATUS SERWERA MINECRAFT" if is_online else "🔴 | STATUS SERWERA MINECRAFT"
    color = 0x57F287 if is_online else 0xED4245

    embed = discord.Embed(title=title, color=color)
    embed.add_field(name="🌍 Adres IP", value=f"> `{SERVER_IP}`", inline=False)

    if is_online:
        embed.add_field(name="👥 Gracze", value=f"> `{players} / {max_players}`", inline=True)
        embed.add_field(name="⚡ Status", value="> `Online`", inline=True)
    else:
        embed.add_field(name="❤️ Status", value="> Serwer jest obecnie wyłączony.", inline=False)

    embed.add_field(name="🏷️ Wersja", value="> `1.21.4`", inline=True)
    embed.set_footer(text=f"Ostatnia aktualizacja • {now}")
    return embed

async def update_status_message(embed):
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: return

    async for msg in channel.history(limit=5):
        if msg.author == bot.user and msg.id != bot.status_message_id:
            try: await msg.delete()
            except: pass

    if bot.status_message_id:
        try:
            msg = await channel.fetch_message(bot.status_message_id)
            await msg.edit(embed=embed)
            return
        except: bot.status_message_id = None

    new_msg = await channel.send(embed=embed)
    bot.status_message_id = new_msg.id

# =========================
# MONITORING SERWERA (Z LOGOWANIEM)
# =========================
@tasks.loop(minutes=2)
async def server_monitor():
    print("Sprawdzam status serwera przez API...")
    api_url = f"https://api.mcsrvstat.us/3/{SERVER_IP}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    # TO JEST KLUCZOWE: Zobaczymy w logach co zwraca API
                    print(f"DEBUG API: {data}") 
                    
                    is_online = data.get("online", False)
                    if is_online:
                        players_online = data.get("players", {}).get("online", 0)
                        players_max = data.get("players", {}).get("max", 0)
                        await update_status_message(build_embed(True, players_online, players_max))
                    else:
                        await update_status_message(build_embed(False))
                else:
                    print(f"Błąd HTTP: {response.status}")
                    await update_status_message(build_embed(False))
                    
    except Exception as e:
        print(f"[API ERROR] Problem: {e}")
        await update_status_message(build_embed(False))

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    if not hasattr(bot, "web_server_started"):
        bot.loop.create_task(start_web_server())
        bot.web_server_started = True

    await bot.tree.sync(guild=MY_GUILD)
    if not server_monitor.is_running():
        server_monitor.start()

    print(f"Zalogowano jako {bot.user}")
    print("Bot gotowy do użycia!")

# =========================
# KOMENDY
# =========================
@bot.tree.command(name="online", description="Wymuś ONLINE", guild=MY_GUILD)
async def cmd_online(interaction: discord.Interaction):
    if not has_permission(interaction.user): return await interaction.response.send_message("❌ Brak uprawnień.", ephemeral=True)
    await update_status_message(build_embed(True, "0", "0"))
    await interaction.response.send_message("✅ Wymuszono ONLINE.", ephemeral=True)

@bot.tree.command(name="offline", description="Wymuś OFFLINE", guild=MY_GUILD)
async def cmd_offline(interaction: discord.Interaction):
    if not has_permission(interaction.user): return await interaction.response.send_message("❌ Brak uprawnień.", ephemeral=True)
    await update_status_message(build_embed(False))
    await interaction.response.send_message("✅ Wymuszono OFFLINE.", ephemeral=True)

if __name__ == "__main__":
    bot.run(TOKEN)
