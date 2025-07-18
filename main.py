import discord
from flask import Flask
import os
from discord import app_commands
import asyncio
import datetime
import json
import zoneinfo
from threading import Thread
from dotenv import load_dotenv

print("=== fichiers présents dans le dossier ===")
print(os.listdir("."))
print("DISCORD VERSION:", getattr(discord, '__version__', '???'))
print("DISCORD MODULE PATH:", discord.__file__)
print("DISCORD LOCATION:", discord.__file__)
print("HAS APP_COMMANDS:", hasattr(discord, 'app_commands'))

# Charger les variables d'environnement (utile si tu testes en local)
load_dotenv()

# Configuration Flask pour Render
app = Flask(__name__)

@app.route('/')
def home():
    return '✅ Le bot est vivant sur Render !'

def run():
    port = int(os.environ.get("PORT", 8080))  # Compatible Render (PORT dynamique)
    print(f"[INFO] Flask écoute sur le port {port}")
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Fichier de sauvegarde
PROGRAMMES_FILE = "programmes.json"
TZ = zoneinfo.ZoneInfo("Europe/Paris")

def load_programmes():
    if os.path.exists(PROGRAMMES_FILE):
        with open(PROGRAMMES_FILE, "r") as f:
            return json.load(f)
    return []

def save_programmes(programmes):
    with open(PROGRAMMES_FILE, "w") as f:
        json.dump(programmes, f, indent=4)

def add_programme(prog):
    programmes = load_programmes()
    programmes.append(prog)
    save_programmes(programmes)

def remove_programme_by_id(prog_id):
    programmes = load_programmes()
    new_programmes = [p for p in programmes if p.get("id") != prog_id]
    save_programmes(new_programmes)

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@tree.command(name="video", description="Envoie une vidéo avec options")
@app_commands.describe(
    url="Lien de la vidéo",
    hour="Heure d’envoi (HH:MM, heure française)",
    role="Rôle à mentionner (optionnel)",
    message="Message avant le lien (optionnel)")
async def send_video(interaction: discord.Interaction, url: str, hour: str = None, role: discord.Role = None, message: str = None):
    channel = interaction.channel
    mention = role.mention if role else ""
    if message:
        message = message.replace("//", "\n")

    async def send():
        content = f"{mention}\n{message}\n{url}" if message else f"{mention}\n**🎬 Nouvelle vidéo à regarder !**\n{url}"
        await channel.send(content=content)
        print(f"[INFO] Vidéo envoyée à {datetime.datetime.now(TZ)}")

    if hour:
        try:
            now = datetime.datetime.now(TZ)
            target = datetime.datetime.strptime(hour, "%H:%M").replace(year=now.year, month=now.month, day=now.day, tzinfo=TZ)
            if target < now:
                target += datetime.timedelta(days=1)
            delay = (target - now).total_seconds()

            prog = {
                "id": f"video_{interaction.id}",
                "type": "video",
                "channel": channel.id,
                "url": url,
                "message": message,
                "mention": mention,
                "time": target.strftime("%Y-%m-%d %H:%M:%S%z")
            }
            add_programme(prog)
            await interaction.response.send_message(f"⏰ Vidéo programmée pour {target.strftime('%H:%M')}", ephemeral=True)

            await asyncio.sleep(delay)
            await send()
            remove_programme_by_id(prog["id"])
        except ValueError:
            await interaction.response.send_message("❌ Heure invalide (HH:MM)", ephemeral=True)
    else:
        await send()
        await interaction.response.send_message("✅ Vidéo envoyée !", ephemeral=True)

# Commande /localvideo
@tree.command(name="localvideo",
              description="Envoie une vidéo stockée localement (max ~8 Mo)")
async def send_local(interaction: discord.Interaction):
    try:
        with open("video.mp4", "rb") as f:
            file = discord.File(f, filename="video.mp4")
            await interaction.response.send_message("🎞️ Vidéo locale :",
                                                    file=file)
            print(
                f"[INFO] Vidéo locale envoyée dans {interaction.channel} à {datetime.datetime.now(TZ)}"
            )
    except FileNotFoundError:
        await interaction.response.send_message(
            "⚠️ Le fichier `video.mp4` est introuvable.")


# Commande /annoncer
@app_commands.command(name="annoncer",
                      description="Annonce un message personnalisé")
@app_commands.describe(
    message="Message à envoyer",
    role="Mentionner un rôle (optionnel)",
    hour="Programmer l'heure d'envoi (HH:MM, heure française, optionnel)",
    sticker_id="ID d’un autocollant à ajouter (optionnel)")
@app_commands.checks.has_permissions(administrator=True)
async def annoncer(interaction: discord.Interaction,
                   message: str,
                   role: discord.Role = None,
                   hour: str = None,
                   sticker_id: str = None):
    channel = interaction.channel
    mention = role.mention if role else ""
    message = message.replace("//", "\n")

    async def send():
        try:
            sticker = discord.Object(
                id=int(sticker_id)) if sticker_id else None
            await channel.send(
                content=f"{mention}\n{message}" if mention else message,
                stickers=[sticker] if sticker else None)
            print(
                f"[INFO] Annonce envoyée dans {channel} à {datetime.datetime.now(TZ)}"
            )
        except Exception as e:
            await interaction.followup.send(f"⚠️ Erreur lors de l’envoi : {e}",
                                            ephemeral=True)

    if hour:
        try:
            now = datetime.datetime.now(TZ)
            target = datetime.datetime.strptime(hour, "%H:%M").replace(
                year=now.year, month=now.month, day=now.day, tzinfo=TZ)
            if target < now:
                target += datetime.timedelta(days=1)
            delay = (target - now).total_seconds()

            prog = {
                "id": f"annoncer_{interaction.id}",
                "type": "annoncer",
                "channel": channel.id,
                "message": message,
                "mention": mention,
                "sticker_id": sticker_id,
                "time": target.strftime("%Y-%m-%d %H:%M:%S%z")
            }
            add_programme(prog)
            await interaction.response.send_message(
                f"⏰ Message programmé pour {target.strftime('%H:%M')}",
                ephemeral=True)

            await asyncio.sleep(delay)
            await send()
            remove_programme_by_id(prog["id"])
        except ValueError:
            await interaction.response.send_message(
                "❌ Heure invalide. Format : HH:MM", ephemeral=True)
    else:
        await send()
        await interaction.response.send_message("✅ Message envoyé !",
                                                ephemeral=True)


tree.add_command(annoncer)


# Commande /listemessages
@tree.command(name="listemessages",
              description="Liste les messages programmés")
@app_commands.checks.has_permissions(administrator=True)
async def liste_messages(interaction: discord.Interaction):
    programmes = load_programmes()
    if not programmes:
        await interaction.response.send_message("📭 Aucun message programmé.",
                                                ephemeral=True)
        return
    texte = "\n".join([
        f"📝 ID: `{p['id']}` | Type: {p['type']} | Heure: {p['time']}"
        for p in programmes
    ])
    await interaction.response.send_message(
        f"📅 Messages programmés :\n{texte}", ephemeral=True)


# Commande /annulermessage
@tree.command(name="annulermessage", description="Annule un message programmé")
@app_commands.describe(id="ID du message à annuler (voir /listemessages)")
@app_commands.checks.has_permissions(administrator=True)
async def annuler_message(interaction: discord.Interaction, id: str):
    programmes = load_programmes()
    match = next((p for p in programmes if p["id"] == id), None)
    if not match:
        await interaction.response.send_message(
            "❌ Aucun message trouvé avec cet ID.", ephemeral=True)
        return
    remove_programme_by_id(id)
    await interaction.response.send_message(
        f"✅ Message avec l'ID `{id}` annulé.", ephemeral=True)

# Reprogrammation
async def recharger_programmes():
    programmes = load_programmes()
    now = datetime.datetime.now(TZ)
    for prog in programmes:
        try:
            target = datetime.datetime.strptime(prog["time"], "%Y-%m-%d %H:%M:%S%z")
            delay = (target - now).total_seconds()
            if delay < 0:
                continue

            async def envoyer(p=prog):
                channel = bot.get_channel(p["channel"])
                if not channel:
                    print(f"[WARN] Canal introuvable pour ID {p['id']}")
                    return
                if p["type"] == "video":
                    content = f"{p['mention']}\n{p['message']}\n{p['url']}" if p["message"] else f"{p['mention']}\n**🎬 Nouvelle vidéo à regarder !**\n{p['url']}"
                    await channel.send(content=content)
                elif p["type"] == "annoncer":
                    sticker = discord.Object(id=int(p["sticker_id"])) if p.get("sticker_id") else None
                    await channel.send(content=f"{p['mention']}\n{p['message']}" if p["mention"] else p["message"],
                                       stickers=[sticker] if sticker else None)
                remove_programme_by_id(p["id"])

            asyncio.create_task(asyncio.sleep(delay))
            asyncio.create_task(envoyer())

        except Exception as e:
            print(f"[ERREUR] {prog.get('id')} : {e}")

@bot.event
async def on_ready():
    print(f"[INFO] Connecté en tant que {bot.user}")
    try:
        synced = await tree.sync()
        print(f"[INFO] {len(synced)} commandes slash synchronisées")
        await recharger_programmes()
    except Exception as e:
        print(f"[ERREUR] sync : {e}")

# Lancement
if __name__ == "__main__":
    try:
        keep_alive()
        bot.run(os.getenv("DISCORD_TOKEN"))
        client.run(token)
    except Exception as e:
        print(f"[ERREUR] Démarrage : {e}")
