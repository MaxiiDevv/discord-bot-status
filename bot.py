import discord
from discord.ext import commands, tasks
from mcstatus import JavaServer
from datetime import datetime
import os
# KONFIGURACJA
TOKEN = os.environ.get("TOKEN")
GUILD_ID = 1462813807679115401
CHANNEL_ID = 1462835903629103206
SERVER_IP = "admincube.aternos.me"

ALLOWED_ROLES = [
    1463171621811519570, 1491760080444592138, 1463171617713684480,
    1518158676605534208, 1519056707148316853, 1463171602681430016
]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

bot.auto_mode = True
bot.status_message_id = None
MY_GUILD = discord.Object(id=GUILD_ID)

def has_permission(member):
    return any(role.id in ALLOWED_ROLES for role in member.roles)

def build_embed(is_online, players=0, max_players=0, ping=0):
    now = datetime.now().strftime("%d.%m.%Y • %H:%M")
    # Tytuł i kolor zależnie od stanu
    title = "🟢 | STATUS SERWERA MINECRAFT" if is_online else "🔴 | STATUS SERWERA MINECRAFT"
    color = 0x57F287 if is_online else 0xED4245
    
    embed = discord.Embed(title=title, color=color)
    embed.add_field(name="🌍 Adres IP", value=f"> `{SERVER_IP}`", inline=False)
    
    if is_online:
        embed.add_field(name="👥 Gracze", value=f"> `{players} / {max_players}`", inline=True)
        embed.add_field(name="⚡ Ping", value=f"> `{ping} ms`", inline=True)
    else:
        embed.add_field(name="❤️ Status", value="> Serwer jest obecnie wyłączony.", inline=False)
    
    embed.add_field(name="🏷️ Wersja", value=f"> `1.21.4`", inline=True)
    embed.set_footer(text=f"Ostatnia aktualizacja • {now}")
    return embed

async def update_status_message(embed):
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: return
    
    # Usuwamy stare wiadomości bota z tego kanału (maks 5 ostatnich)
    async for msg in channel.history(limit=5):
        if msg.author == bot.user and msg.id != bot.status_message_id:
            await msg.delete()

    if bot.status_message_id:
        try:
            msg = await channel.fetch_message(bot.status_message_id)
            await msg.edit(embed=embed)
            return
        except: bot.status_message_id = None
    
    new_msg = await channel.send(embed=embed)
    bot.status_message_id = new_msg.id

@tasks.loop(seconds=60)
async def server_monitor():
    if not bot.auto_mode: return
    try:
        server = JavaServer.lookup(SERVER_IP, timeout=5)
        status = server.status()
        if status.players.online == 0 and status.players.max == 0: raise Exception()
        await update_status_message(build_embed(True, status.players.online, status.players.max, round(status.latency)))
    except:
        await update_status_message(build_embed(False))

@bot.event
async def setup_hook():
    await bot.tree.sync(guild=MY_GUILD)

@bot.event
async def on_ready():
    server_monitor.start()
    print("Bot gotowy!")

# Komendy... (reszta bez zmian)
@bot.tree.command(name="auto", description="Włącz tryb AUTO", guild=MY_GUILD)
async def cmd_auto(interaction: discord.Interaction):
    if not has_permission(interaction.user): return await interaction.response.send_message("❌", ephemeral=True)
    bot.auto_mode = True
    await interaction.response.send_message("✅ Włączono tryb AUTO.", ephemeral=True)

@bot.tree.command(name="online", description="Wymuś ONLINE", guild=MY_GUILD)
async def cmd_online(interaction: discord.Interaction):
    if not has_permission(interaction.user): return await interaction.response.send_message("❌", ephemeral=True)
    bot.auto_mode = False
    await update_status_message(build_embed(True, 0, 0, 0))
    await interaction.response.send_message("✅ Wymuszono ONLINE.", ephemeral=True)

@bot.tree.command(name="offline", description="Wymuś OFFLINE", guild=MY_GUILD)
async def cmd_offline(interaction: discord.Interaction):
    if not has_permission(interaction.user): return await interaction.response.send_message("❌", ephemeral=True)
    bot.auto_mode = False
    await update_status_message(build_embed(False))
    await interaction.response.send_message("✅ Wymuszono OFFLINE.", ephemeral=True)

bot.run(TOKEN)