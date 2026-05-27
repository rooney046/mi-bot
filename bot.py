import discord
from discord import app_commands
import os
import asyncio
import random

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot conectado como: {client.user}")
    await client.change_presence(activity=discord.Game(name="/help"))

@tree.command(name="ping", description="Muestra la latencia del bot")
async def ping(interaction: discord.Interaction):
    latency = round(client.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! Latencia: **{latency}ms**")

@tree.command(name="saludar", description="Saluda a un usuario")
async def saludar(interaction: discord.Interaction, usuario: discord.Member = None):
    usuario = usuario or interaction.user
    await interaction.response.send_message(f"¡Hola, {usuario.mention}! 🎉")

@tree.command(name="info", description="Muestra información del servidor")
async def info(interaction: discord.Interaction):
    servidor = interaction.guild
    embed = discord.Embed(title=f"📋 Info de {servidor.name}", color=discord.Color.blue())
    embed.add_field(name="Miembros", value=servidor.member_count)
    embed.add_field(name="Canales", value=len(servidor.channels))
    await interaction.response.send_message(embed=embed)

@tree.command(name="limpiar", description="Borra mensajes del canal")
@app_commands.checks.has_permissions(manage_messages=True)
async def limpiar(interaction: discord.Interaction, cantidad: int = 5):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"🗑️ Se borraron **{cantidad}** mensajes.", ephemeral=True)

@tree.command(name="anuncio", description="Envía un anuncio a un canal específico")
@app_commands.checks.has_permissions(administrator=True)
async def anuncio(interaction: discord.Interaction, canal: discord.TextChannel, mensaje: str):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(description=mensaje, color=discord.Color.red())
    embed.set_author(name="📢 Anuncio")
    await canal.send(embed=embed)
    await interaction.followup.send(f"✅ Anuncio enviado a {canal.mention}", ephemeral=True)

# ── Mensaje en ticket ──────────────────────────────────────
@tree.command(name="mensaje-ticket", description="Envía un mensaje embed dentro de un ticket abierto")
@app_commands.checks.has_permissions(administrator=True)
async def mensaje_ticket(interaction: discord.Interaction, mensaje: str):
    if not interaction.channel.name.startswith("ticket-"):
        await interaction.response.send_message("❌ Este comando solo se puede usar dentro de un ticket.", ephemeral=True)
        return
    embed = discord.Embed(description=mensaje, color=discord.Color.gold())
    embed.set_author(name="📩 Mensaje del Staff")
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("✅ Mensaje enviado.", ephemeral=True)

# ── Hola Bot ──────────────────────────────────────────────
@tree.command(name="hola-bot", description="Habla con el bot como si fuera una persona")
async def hola_bot(interaction: discord.Interaction, mensaje: str):
    if interaction.channel.name != "comandos":
        await interaction.response.send_message("❌ Este comando solo se puede usar en el canal #comandos.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    mensaje_lower = mensaje.lower()
    if any(p in mensaje_lower for p in ["hola", "hey", "buenas", "saludos"]):
        respuesta = f"¡Hola {interaction.user.mention}! 👋 ¿Cómo estás? ¿En qué te puedo ayudar?"
    elif any(p in mensaje_lower for p in ["como estas", "cómo estás", "que tal", "qué tal"]):
        respuesta = f"¡Estoy genial {interaction.user.mention}! Gracias por preguntar 😄 ¿Y tú?"
    elif any(p in mensaje_lower for p in ["adios", "adiós", "chao", "bye", "hasta luego"]):
        respuesta = f"¡Hasta luego {interaction.user.mention}! 👋 Fue un placer hablar contigo."
    elif any(p in mensaje_lower for p in ["gracias", "thank"]):
        respuesta = f"¡De nada {interaction.user.mention}! Para eso estoy 😊"
    elif any(p in mensaje_lower for p in ["quien eres", "quién eres", "que eres", "qué eres"]):
        respuesta = f"Soy **Hurban Bot** 🤖, el bot oficial de este servidor. ¡Estoy aquí para ayudarte!"
    elif any(p in mensaje_lower for p in ["ayuda", "help", "comandos"]):
        respuesta = f"¡Claro {interaction.user.mention}! Puedes usar `/ping`, `/info`, `/anuncio`, `/panel-ticket` y muchos más 😊"
    elif any(p in mensaje_lower for p in ["aburrido", "aburrida"]):
        respuesta = f"¡Yo nunca me aburro {interaction.user.mention}! Siempre estoy monitoreando el servidor 👀"
    elif any(p in mensaje_lower for p in ["amor", "te quiero", "te amo"]):
        respuesta = f"Aww 🥺 ¡Yo también te quiero {interaction.user.mention}! Eres el mejor."
    elif any(p in mensaje_lower for p in ["chiste", "cuéntame", "cuentame"]):
        chistes = [
            "¿Por qué el libro de matemáticas está triste? Porque tiene demasiados problemas 😂",
            "¿Qué le dice un jardinero a otro? ¡Que te peta! 🌸",
            "¿Por qué los pájaros vuelan hacia el sur? ¡Porque caminar sería muy lejos! 😂"
        ]
        respuesta = random.choice(chistes)
    else:
        respuestas_generales = [
            f"Interesante lo que dices, {interaction.user.mention} 🤔 ¡Cuéntame más!",
            f"¡Eso es genial {interaction.user.mention}! 😄",
            f"Hmm... no estoy seguro de entenderte {interaction.user.mention}, ¿puedes explicarme mejor? 😅",
            f"¡Me parece muy bien {interaction.user.mention}! 👍",
            f"¡Qué interesante {interaction.user.mention}! No lo había pensado así 🤯"
        ]
        respuesta = random.choice(respuestas_generales)
    await interaction.channel.send(respuesta)
    await interaction.followup.send("✅", ephemeral=True)

# ── Anti Link ──────────────────────────────────────────────
canales_antilink = set()

@tree.command(name="antilink", description="Activa o desactiva el anti-link en un canal")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(canal="Canal donde aplicar el anti-link", activar="True para activar, False para desactivar")
async def antilink(interaction: discord.Interaction, canal: discord.TextChannel, activar: bool):
    if activar:
        canales_antilink.add(canal.id)
        await interaction.response.send_message(f"✅ Anti-link activado en {canal.mention}", ephemeral=True)
    else:
        canales_antilink.discard(canal.id)
        await interaction.response.send_message(f"❌ Anti-link desactivado en {canal.mention}", ephemeral=True)

# ── Malas palabras ─────────────────────────────────────────
MALAS_PALABRAS = [
    "mierda", "puta", "puto", "idiota", "imbecil", "pendejo",
    "cabron", "gay", "maricon", "maldito", "estupido", "culo",
    "joder", "coño", "verga", "chinga", "pinche", "gilipollas",
    "bastardo", "hdp", "ctm", "conchatumadre", "webon", "wey",
    "mamaguevo", "come mierda", "hijo de puta"
]

usuarios_aislados = set()

@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id in canales_antilink:
        if "http://" in message.content or "https://" in message.content or "discord.gg" in message.content:
            await message.delete()
            aviso = await message.channel.send(f"🚫 {message.author.mention} no se permiten links aquí.")
            await asyncio.sleep(5)
            await aviso.delete()
            return
    if message.author.id in usuarios_aislados:
        return
    contenido = message.content.lower()
    for palabra in MALAS_PALABRAS:
        if palabra in contenido:
            await message.delete()
            minutos = random.randint(5, 10)
            segundos = minutos * 60
            rol_aislado = discord.utils.get(message.guild.roles, name="Aislado")
            if not rol_aislado:
                rol_aislado = await message.guild.create_role(name="Aislado")
                for channel in message.guild.channels:
                    await channel.set_permissions(rol_aislado, send_messages=False, speak=False)
            await message.author.add_roles(rol_aislado)
            usuarios_aislados.add(message.author.id)
            embed_canal = discord.Embed(
                title="🔇 Usuario Aislado",
                description=f"{message.author.mention} fue aislado por **{minutos} minutos** por usar lenguaje inapropiado.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed_canal, delete_after=10)
            canal_adv = discord.utils.get(message.guild.text_channels, name="advertencia")
            if canal_adv:
                embed_adv = discord.Embed(title="⚠️ Advertencia — Usuario Aislado", color=discord.Color.red())
                embed_adv.add_field(name="👤 Usuario", value=f"{message.author.mention} (`{message.author.name}`)", inline=True)
                embed_adv.add_field(name="⏱️ Duración", value=f"{minutos} minutos", inline=True)
                embed_adv.add_field(name="📢 Canal", value=message.channel.mention, inline=True)
                embed_adv.add_field(name="📝 Motivo", value=f"Se detectó la palabra prohibida **`{palabra}`** en su mensaje.", inline=False)
                embed_adv.add_field(name="📋 Explicación", value="El servidor no permite el uso de lenguaje ofensivo, vulgar o discriminatorio. El usuario ha sido aislado temporalmente por violar las normas del servidor.", inline=False)
                embed_adv.set_thumbnail(url=message.author.display_avatar.url)
                embed_adv.set_footer(text=f"El a
