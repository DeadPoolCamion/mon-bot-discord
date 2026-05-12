import discord
from discord.ext import commands
import json
import os
import random
from collections import defaultdict

# ==========================================
# CONFIG — mets ton token ici
# ==========================================
TOKEN = os.getenv("TOKEN")
TON_USER_ID = 964203981729595422  # Ton ID Discord (clic droit > Copier l'identifiant)
STYLE_FILE = "style_data.json"

# ==========================================
# CHARGEMENT DU STYLE
# ==========================================
def load_style():
    if os.path.exists(STYLE_FILE):
        with open(STYLE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"messages": [], "reactions": [], "words": {}}

def save_style(data):
    with open(STYLE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

style_data = load_style()

# ==========================================
# BOT SETUP
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ==========================================
# APPRENTISSAGE — le bot observe tes messages
# ==========================================
@bot.event
async def on_message(message):
    # Apprendre depuis TES messages
    if message.author.id == TON_USER_ID and not message.content.startswith("!"):
        content = message.content.strip()
        if content:
            style_data["messages"].append(content)
            # Compter les mots que t'utilises souvent
            for word in content.lower().split():
                style_data["words"][word] = style_data["words"].get(word, 0) + 1
            # Garder max 500 messages pour pas que ça explose
            if len(style_data["messages"]) > 500:
                style_data["messages"] = style_data["messages"][-500:]
            save_style(style_data)

    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    # Apprendre les emojis que tu utilises
    if user.id == TON_USER_ID:
        emoji = str(reaction.emoji)
        if emoji not in style_data["reactions"]:
            style_data["reactions"].append(emoji)
            save_style(style_data)

# ==========================================
# COMMANDES FUN
# ==========================================

@bot.command(name="parle")
async def parle(ctx):
    """Le bot envoie un de tes vieux messages au hasard"""
    if not style_data["messages"]:
        await ctx.send("J'ai encore rien appris de toi frr 👀")
        return
    msg = random.choice(style_data["messages"])
    await ctx.send(msg)

@bot.command(name="réagis")
async def reagis(ctx):
    """Le bot réagit avec un emoji que t'as déjà utilisé"""
    if not style_data["reactions"]:
        await ctx.send("T'as encore jamais réagi à rien 💀")
        return
    emoji = random.choice(style_data["reactions"])
    try:
        await ctx.message.add_reaction(emoji)
    except:
        await ctx.send(f"Je peux pas mettre {emoji} mais c'est ton style lol")

@bot.command(name="mots")
async def mots(ctx):
    """Affiche tes mots les plus utilisés"""
    if not style_data["words"]:
        await ctx.send("Aucun mot appris pour l'instant")
        return
    top = sorted(style_data["words"].items(), key=lambda x: x[1], reverse=True)[:10]
    result = "**Tes mots les + utilisés :**\n"
    for word, count in top:
        result += f"`{word}` — {count} fois\n"
    await ctx.send(result)

@bot.command(name="style")
async def style_info(ctx):
    """Stats sur ce que le bot a appris"""
    nb_msg = len(style_data["messages"])
    nb_emojis = len(style_data["reactions"])
    nb_mots = len(style_data["words"])
    await ctx.send(
        f"📊 **Ce que j'ai appris de toi :**\n"
        f"💬 {nb_msg} messages enregistrés\n"
        f"😂 {nb_emojis} emojis différents\n"
        f"📝 {nb_mots} mots uniques"
    )

@bot.command(name="reset")
async def reset(ctx):
    """Remet le style à zéro (à utiliser avec précaution)"""
    if ctx.author.id != TON_USER_ID:
        await ctx.send("T'es pas moi frérot 😭")
        return
    style_data["messages"] = []
    style_data["reactions"] = []
    style_data["words"] = {}
    save_style(style_data)
    await ctx.send("Style remis à zéro 🔄")

# ==========================================
# DÉMARRAGE
# ==========================================
@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user}")
    print(f"👀 En train d'observer l'utilisateur ID: {TON_USER_ID}")

bot.run(TOKEN)