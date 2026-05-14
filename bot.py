import discord
from discord.ext import commands
import json
import os
import random
import aiohttp

# ==========================================
# CONFIG
# ==========================================
TOKEN = os.getenv("TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TON_USER_ID = 964203981729595422
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
# FONCTION IA
# ==========================================
async def ask_claude(prompt):
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    body = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 300,
        "messages": [{"role": "user", "content": prompt}]
    }
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.anthropic.com/v1/messages", headers=headers, json=body) as resp:
            data = await resp.json()
            return data["content"][0]["text"]

def get_style_context():
    if not style_data["messages"]:
        return "Pas encore de messages enregistrés."
    exemples = random.sample(style_data["messages"], min(15, len(style_data["messages"])))
    return "\n".join(f"- {m}" for m in exemples)

# ==========================================
# COMMANDES FUN AVEC IA
# ==========================================

@bot.command(name="blague")
async def blague(ctx):
    await ctx.typing()
    contexte = get_style_context()
    prompt = f"""Voici des exemples de messages d'une personne :
{contexte}

En imitant exactement son style d'écriture, son humour, ses expressions et son langage (argot, abréviations, emojis s'il en utilise), génère UNE blague courte et drôle. Réponds uniquement avec la blague, rien d'autre."""
    try:
        reponse = await ask_claude(prompt)
        await ctx.send(reponse)
    except:
        await ctx.send("Aïe j'arrive pas à générer une blague là 💀")

@bot.command(name="vanne")
async def vanne(ctx, *, cible: str = None):
    await ctx.typing()
    contexte = get_style_context()
    target = cible if cible else "quelqu'un au hasard"
    prompt = f"""Voici des exemples de messages d'une personne :
{contexte}

En imitant exactement son style d'écriture, son humour et ses expressions, génère UNE vanne sympa et drôle (pas méchante) envers "{target}". Réponds uniquement avec la vanne, rien d'autre."""
    try:
        reponse = await ask_claude(prompt)
        await ctx.send(reponse)
    except:
        await ctx.send("J'arrive pas à trouver une vanne là 😭")

@bot.command(name="avis")
async def avis(ctx, *, sujet: str):
    await ctx.typing()
    contexte = get_style_context()
    prompt = f"""Voici des exemples de messages d'une personne :
{contexte}

En imitant exactement son style d'écriture, ses expressions et son humour, donne un avis tranché et drôle sur : "{sujet}". Réponds uniquement avec l'avis, rien d'autre."""
    try:
        reponse = await ask_claude(prompt)
        await ctx.send(reponse)
    except:
        await ctx.send("J'ai pas d'avis là frr 😅")

@bot.command(name="repond")
async def repond(ctx, *, message: str):
    await ctx.typing()
    contexte = get_style_context()
    prompt = f"""Voici des exemples de messages d'une personne :
{contexte}

En imitant exactement son style d'écriture, réponds à ce message comme si tu étais cette personne : "{message}". Réponds uniquement avec la réponse, rien d'autre."""
    try:
        reponse = await ask_claude(prompt)
        await ctx.send(reponse)
    except:
        await ctx.send("Je sais pas quoi répondre là 💀")

@bot.command(name="parle")
async def parle(ctx):
    if not style_data["messages"]:
        await ctx.send("J'ai encore rien appris de toi frr 👀")
        return
    msg = random.choice(style_data["messages"])
    await ctx.send(msg)

@bot.command(name="style")
async def style_info(ctx):
    nb_msg = len(style_data["messages"])
    nb_emojis = len(style_data["reactions"])
    nb_mots = len(style_data["words"])
    await ctx.send(
        f"📊 **Ce que j'ai appris de toi :**\n"
        f"💬 {nb_msg} messages enregistrés\n"
        f"😂 {nb_emojis} emojis différents\n"
        f"📝 {nb_mots} mots uniques"
    )

@bot.command(name="commandes")
async def commandes(ctx):
    await ctx.send(
        "**Commandes disponibles :**\n"
        "`!blague` — génère une blague dans ton style\n"
        "`!vanne @quelqu'un` — balance une vanne\n"
        "`!avis [sujet]` — donne un avis sur n'importe quoi\n"
        "`!repond [message]` — répond comme toi\n"
        "`!parle` — répète un de tes vieux messages\n"
        "`!style` — stats de ce que j'ai appris"
    )

# ==========================================
# DÉMARRAGE
# ==========================================
@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user}")
    print(f"👀 En train d'observer l'utilisateur ID: {TON_USER_ID}")

bot.run(TOKEN)
