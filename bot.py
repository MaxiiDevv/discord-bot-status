import os
import discord
from discord.ext import commands
from discord import app_commands
from aiohttp import web

# =========================
# KONFIGURACJA
# =========================

TOKEN = os.getenv("TOKEN")

GUILD_ID = 1462813807679115401
CHANNEL_ID = 1462835903629103206

SERVER_IP = "tapir.aternos.host"
SERVER_VERSION = "1.21.4"

ALLOWED_ROLES = [
    1463171621811519570,
    1491760080444592138,
    1463171617713684480,
    1518158676605534208,
    1519056707148316853,
    1463171602681430016
]

# =========================
# DISCORD
# =========================

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=intents)

guild = discord.Object(id=GUILD_ID)

status_message_id = None

# =========================
# KEEP ALIVE (RENDER)
# =========================

async def home(request):
    return web.Response(text="Bot działa!")

async def start_webserver():
    app = web.Application()
    app.router.add_get("/", home)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)

    await site.start()

# =========================
# POMOCNICZE
# =========================

def has_permission(member):
    return any(role.id in ALLOWED_ROLES for role in member.roles)

def build_online_embed():
    embed = discord.Embed(
        title="🟢 STATUS SERWERA MINECRAFT",
        description="Serwer jest aktualnie dostępny.",
        color=0x57F287
    )

    embed.add_field(
        name="🌍 Adres IP",
        value=f"`{SERVER_IP}`",
        inline=False
    )

    embed.add_field(
        name="⚡ Status",
        value="`ONLINE`",
        inline=True
    )

    embed.add_field(
        name="🏷️ Wersja",
        value=f"`{SERVER_VERSION}`",
        inline=True
    )

    embed.set_footer(text="Zrobiony przez maxidev")

    return embed

def build_offline_embed():
    embed = discord.Embed(
        title="🔴 STATUS SERWERA MINECRAFT",
        description="Serwer jest aktualnie wyłączony.",
        color=0xED4245
    )

    embed.add_field(
        name="🌍 Adres IP",
        value=f"`{SERVER_IP}`",
        inline=False
    )

    embed.add_field(
        name="⚡ Status",
        value="`OFFLINE`",
        inline=True
    )

    embed.add_field(
        name="🏷️ Wersja",
        value=f"`{SERVER_VERSION}`",
        inline=True
    )

    embed.set_footer(text="Zrobiony przez maxidev")

    return embed

async def update_status(embed):
    global status_message_id

    channel = bot.get_channel(CHANNEL_ID)

    if not channel:
        return

    if status_message_id:
        try:
            msg = await channel.fetch_message(status_message_id)
            await msg.edit(embed=embed)
            return
        except:
            status_message_id = None

    msg = await channel.send(embed=embed)
    status_message_id = msg.id

# =========================
# READY
# =========================

@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")

    await bot.change_presence(
        activity=discord.Game(name="Zrobiony przez maxidev")
    )

    await bot.tree.sync(guild=guild)

    if not hasattr(bot, "web_started"):
        bot.loop.create_task(start_webserver())
        bot.web_started = True

    print("Bot gotowy!")

# =========================
# SLASH COMMANDS
# =========================

@bot.tree.command(
    name="online",
    description="Ustaw status ONLINE",
    guild=guild
)
async def online(interaction: discord.Interaction):

    if not has_permission(interaction.user):
        await interaction.response.send_message(
            "❌ Nie masz uprawnień.",
            ephemeral=True
        )
        return

    await update_status(build_online_embed())

    await interaction.response.send_message(
        "✅ Status ustawiony na ONLINE.",
        ephemeral=True
    )

@bot.tree.command(
    name="offline",
    description="Ustaw status OFFLINE",
    guild=guild
)
async def offline(interaction: discord.Interaction):

    if not has_permission(interaction.user):
        await interaction.response.send_message(
            "❌ Nie masz uprawnień.",
            ephemeral=True
        )
        return

    await update_status(build_offline_embed())

    await interaction.response.send_message(
        "✅ Status ustawiony na OFFLINE.",
        ephemeral=True
    )

# =========================
# START
# =========================

bot.run(TOKEN)
```
