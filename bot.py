import os
import asyncio
import discord

from discord.ext import commands, tasks
from mcstatus import JavaServer
from datetime import datetime
import pytz

from aiohttp import web

# =========================
# KONFIGURACJA
# =========================

TOKEN = os.environ.get("TOKEN")

GUILD_ID = 1462813807679115401
CHANNEL_ID = 1462835903629103206

# Fizyczny adres omijający zabezpieczenia DNS Rendera/Aternosa
SERVER_IP = "mc.hypixel.net"
SERVER_PORT = 25565
DISPLAY_IP = "mc.hypixel.net"

# Adres do ładnego wyświetlania w wiadomości na Discordzie
DISPLAY_IP = "admincube.aternos.me"

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
# WEB SERVER (KEEP ALIVE DLA RENDERA)
# =========================

async def handle(request):
    return web.Response(text="Bot jest aktywny!")

async def start_web_server():
    app = web.Application()
    app.add_routes([
        web.get('/', handle)
    ])

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 10000))

    site = web.TCPSite(
        runner,
        host="0.0.0.0",
        port=port
    )

    await site.start()
    print(f"Serwer WWW uruchomiony na porcie {port}")


# =========================
# FUNKCJE
# =========================

def has_permission(member):
    return any(role.id in ALLOWED_ROLES for role in member.roles)


def build_embed(is_online, players="0", max_players="0", ping=0):
    warsaw_tz = pytz.timezone("Europe/Warsaw")
    now = datetime.now(warsaw_tz).strftime("%d.%m.%Y • %H:%M")

    title = (
        "🟢 | STATUS SERWERA MINECRAFT"
        if is_online
        else "🔴 | STATUS SERWERA MINECRAFT"
    )

    color = 0x57F287 if is_online else 0xED4245

    embed = discord.Embed(
        title=title,
        color=color
    )

    embed.add_field(
        name="🌍 Adres IP",
        value=f"> `{DISPLAY_IP}`",
        inline=False
    )

    if is_online:
        embed.add_field(
            name="👥 Gracze",
            value=f"> `{players} / {max_players}`",
            inline=True
        )

        embed.add_field(
            name="⚡ Ping",
            value=f"> `{ping} ms`",
            inline=True
        )
    else:
        embed.add_field(
            name="❤️ Status",
            value="> Serwer jest obecnie wyłączony.",
            inline=False
        )

    embed.add_field(
        name="🏷️ Wersja",
        value="> `1.21.4`",
        inline=True
    )

    embed.set_footer(
        text=f"Ostatnia aktualizacja • {now}"
    )

    return embed


async def update_status_message(embed):
    channel = bot.get_channel(CHANNEL_ID)

    if not channel:
        return

    async for msg in channel.history(limit=5):
        if msg.author == bot.user and msg.id != bot.status_message_id:
            try:
                await msg.delete()
            except:
                pass

    if bot.status_message_id:
        try:
            msg = await channel.fetch_message(
                bot.status_message_id
            )

            await msg.edit(embed=embed)
            return

        except:
            bot.status_message_id = None

    new_msg = await channel.send(embed=embed)
    bot.status_message_id = new_msg.id


# =========================
# MONITORING SERWERA MC
# =========================

@tasks.loop(minutes=2)
async def server_monitor():
    try:
        # Próba 1: Łączymy się bezpośrednio z ominięciem .lookup()
        server = JavaServer(SERVER_IP, SERVER_PORT, timeout=10)
        status = await server.async_status()
        
        await update_status_message(
            build_embed(True, status.players.online, status.players.max, round(status.latency))
        )

    except Exception as e:
        # Logowanie błędu, żebyśmy w końcu wiedzieli DLACZEGO serwer jest offline
        print(f"[STATUS ERROR] Nie udało się pobrać statusu: {e}")
        
        try:
            # Próba 2: Sam ping, jeśli status zostanie zablokowany
            server = JavaServer(SERVER_IP, SERVER_PORT, timeout=10)
            ping_latency = await server.async_ping()
            
            await update_status_message(
                build_embed(True, "?", "?", round(ping_latency))
            )
        except Exception as e2:
            print(f"[PING ERROR] Nie udało się spingować serwera: {e2}")
            
            await update_status_message(
                build_embed(False)
            )


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

    await bot.change_presence(
        activity=discord.Game(
            name="Stworzony przez MaxiDev"
        )
    )

    print(f"Zalogowano jako {bot.user}")
    print("Bot gotowy!")


# =========================
# KOMENDY
# =========================

@bot.tree.command(
    name="online",
    description="Wymuś ONLINE",
    guild=MY_GUILD
)
async def cmd_online(interaction: discord.Interaction):

    if not has_permission(interaction.user):
        return await interaction.response.send_message(
            "❌ Nie masz uprawnień.",
            ephemeral=True
        )

    await update_status_message(
        build_embed(True, 0, 0, 0)
    )

    await interaction.response.send_message(
        "✅ Wymuszono ONLINE.",
        ephemeral=True
    )


@bot.tree.command(
    name="offline",
    description="Wymuś OFFLINE",
    guild=MY_GUILD
)
async def cmd_offline(interaction: discord.Interaction):

    if not has_permission(interaction.user):
        return await interaction.response.send_message(
            "❌ Nie masz uprawnień.",
            ephemeral=True
        )

    await update_status_message(
        build_embed(False)
    )

    await interaction.response.send_message(
        "✅ Wymuszono OFFLINE.",
        ephemeral=True
    )


# =========================
# START BOTA
# =========================

if __name__ == "__main__":
    bot.run(TOKEN)
