"""
bot.py — Street Bronx Bot con integración a la API REST
Requiere: pip install discord.py flask flask-cors requests
"""

import discord
from discord import app_commands
import os
import asyncio
import threading
import requests
import datetime

# ── Importar y lanzar la API en un hilo separado ───────────
from api import app as flask_app, state, add_event

def run_api():
    flask_app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

api_thread = threading.Thread(target=run_api, daemon=True)
api_thread.start()

# ── Bot setup ───────────────────────────────────────────────
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# IDs de canales con anti-link activo (sincronizado con API)
canales_antilink_ids: set = set()

MALAS_PALABRAS_DEFAULT = ["mierda", "puta", "idiota", "imbecil", "pendejo", "cabron"]

config = {}

# ── Helper: push estado al API state dict ──────────────────
def push_state():
    """Actualiza el state compartido con info actual del bot."""
    if not client.guilds:
        return
    guild = client.guilds[0]
    # Contar tickets abiertos (canales cuyo nombre empieza con "ticket-")
    tickets = sum(1 for ch in guild.text_channels if ch.name.startswith("ticket-"))
    state.update({
        "bot_online": True,
        "latency_ms": round(client.latency * 1000),
        "guild_name": guild.name,
        "member_count": guild.member_count,
        "boost_count": guild.premium_subscription_count,
        "boost_tier": guild.premium_tier,
        "channel_count": len(guild.channels),
        "open_tickets": tickets,
        "config": config.get(guild.id, {}),
        "last_updated": datetime.datetime.utcnow().isoformat(),
    })

async def periodic_push():
    """Pushea estado cada 30 segundos."""
    await client.wait_until_ready()
    while not client.is_closed():
        push_state()
        await asyncio.sleep(30)

# ════════════════════════════════════════════════════════════
#  EVENTOS
# ════════════════════════════════════════════════════════════

@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot conectado como: {client.user}")
    await client.change_presence(activity=discord.Game(name="/help"))
    push_state()
    client.loop.create_task(periodic_push())

@client.event
async def on_member_join(member):
    push_state()
    add_event("join", member.name, f"Se unió a {member.guild.name}")

    guild_config = config.get(member.guild.id)
    if not guild_config:
        return
    canal = client.get_channel(guild_config["bienvenida"])
    if not canal:
        return

    nombre_servidor = guild_config.get("nombre_servidor", member.guild.name)
    roles           = guild_config.get("roles", "policía 🚓, médico 🚑, bombero 🔥")
    canal_reglas_id    = guild_config.get("canal_reglas")
    canal_anuncios_id  = guild_config.get("canal_anuncios")
    canal_chat_id      = guild_config.get("canal_chat")

    embed = discord.Embed(
        title=f"✨ Bienvenido/a {member.name} ✨",
        description=(
            f"🏙️ Has llegado a **{nombre_servidor}**, el mejor servidor de Roleplay en Roblox.\n"
            f"Aquí podrás convertirte en quien quieras: {roles}\n"
            "con tus propias historias.\n\n"
            "📋 **Pasos para empezar:**\n"
            f"1️⃣ Lee las reglas en <#{canal_reglas_id}>\n"
            f"2️⃣ Mira las novedades en <#{canal_anuncios_id}>\n"
            f"3️⃣ Pasa por <#{canal_chat_id}>\n\n"
            "🎭 **Recuerda:**\n"
            "• El respeto es fundamental 🙌\n"
            "• Juega con creatividad y realismo 🎬\n"
            "• Cumple las normas 🚫\n\n"
            f"🚀 ¡Tu segunda vida comienza ahora en **{nombre_servidor}**! 🎉"
        ),
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await canal.send(embed=embed)

@client.event
async def on_member_remove(member):
    push_state()
    add_event("leave", member.name, f"Salió de {member.guild.name}")

    guild_config = config.get(member.guild.id)
    if not guild_config:
        return
    canal = client.get_channel(guild_config["despedida"])
    if not canal:
        return

    nombre_servidor = guild_config.get("nombre_servidor", member.guild.name)
    embed = discord.Embed(
        title=f"👋 {member.name} ha salido del servidor...",
        description=(
            f"🏙️ Hoy nos despedimos de un ciudadano más de **{nombre_servidor}**.\n"
            "Quizás su historia termine aquí, o tal vez solo sea una pausa.\n\n"
            "💭 Cada rol deja recuerdos 🚀\n\n"
            "✨ Las puertas siempre estarán abiertas para volver.\n"
            "🚪 ¡Hasta pronto, viajero!"
        ),
        color=discord.Color.red()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await canal.send(embed=embed)

@client.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if before.premium_since is None and after.premium_since is not None:
        push_state()
        add_event("boost", after.name, f"Boost #{after.guild.premium_subscription_count}")
        canal_boosts = discord.utils.get(after.guild.text_channels, name="boots")
        if canal_boosts:
            embed = discord.Embed(
                title="🚀 ¡Nuevo Boost al servidor!",
                description=(
                    f"✨ ¡Gracias {after.mention} por el **Nitro Boost**! 💜\n\n"
                    f"💎 Total boosts: **{after.guild.premium_subscription_count}**\n"
                    f"🏆 Nivel: **{after.guild.premium_tier}**\n\n"
                    "¡Tu apoyo hace este servidor increíble! 🎉"
                ),
                color=discord.Color.purple()
            )
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.set_footer(text="¡Gracias por tu apoyo! 💜")
            await canal_boosts.send(embed=embed)

@client.event
async def on_message(message):
    if message.author.bot:
        return

    # Anti-link (usa IDs del state compartido con la API)
    ids_antilink = {c["id"] for c in state.get("canales_antilink", [])}
    if message.channel.id in ids_antilink:
        if any(x in message.content for x in ["http://","https://","discord.gg"]):
            await message.delete()
            add_event("antilink", message.author.name, f"Link eliminado en #{message.channel.name}")
            aviso = await message.channel.send(f"🚫 {message.author.mention} no se permiten links aquí.")
            await asyncio.sleep(5)
            await aviso.delete()
            return

    # Malas palabras (usa lista del state)
    palabras = state.get("malas_palabras", MALAS_PALABRAS_DEFAULT)
    contenido = message.content.lower()
    for palabra in palabras:
        if palabra in contenido:
            await message.delete()
            add_event("badword", message.author.name, f"Palabra: {palabra}")
            rol_aislado = discord.utils.get(message.guild.roles, name="Aislado")
            if not rol_aislado:
                rol_aislado = await message.guild.create_role(name="Aislado")
                for ch in message.guild.channels:
                    await ch.set_permissions(rol_aislado, send_messages=False, speak=False)
            await message.author.add_roles(rol_aislado)
            aviso = await message.channel.send(
                f"🔇 {message.author.mention} fue aislado 5 min por lenguaje inapropiado."
            )
            await asyncio.sleep(300)
            await message.author.remove_roles(rol_aislado)
            await aviso.delete()
            break

# ════════════════════════════════════════════════════════════
#  SLASH COMMANDS
# ════════════════════════════════════════════════════════════

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
@app_commands.describe(canal="Canal destino", mensaje="Mensaje", link="Link opcional", texto_link="Texto del link")
async def anuncio(interaction: discord.Interaction, canal: discord.TextChannel,
                  mensaje: str, link: str = None, texto_link: str = "Ver más"):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(description=mensaje, color=discord.Color.red())
    embed.set_author(name="📢 Anuncio")
    if link:
        embed.add_field(name="🔗 Link", value=f"[{texto_link}]({link})", inline=False)
    await canal.send(embed=embed)
    await interaction.followup.send(f"✅ Anuncio enviado a {canal.mention}", ephemeral=True)

@tree.command(name="antilink", description="Activa o desactiva el anti-link en un canal")
@app_commands.checks.has_permissions(administrator=True)
async def antilink(interaction: discord.Interaction, canal: discord.TextChannel, activar: bool):
    lista = state["canales_antilink"]
    if activar:
        if canal.id not in [c["id"] for c in lista]:
            lista.append({"id": canal.id, "name": canal.name})
        await interaction.response.send_message(f"✅ Anti-link activado en {canal.mention}", ephemeral=True)
    else:
        state["canales_antilink"] = [c for c in lista if c["id"] != canal.id]
        await interaction.response.send_message(f"❌ Anti-link desactivado en {canal.mention}", ephemeral=True)

@tree.command(name="panel-bienvenida", description="Crea un panel de bienvenida")
@app_commands.checks.has_permissions(administrator=True)
async def panel_bienvenida(
    interaction: discord.Interaction,
    canal: discord.TextChannel,
    nombre_servidor: str, descripcion_servidor: str, roles: str,
    canal_reglas: discord.TextChannel, canal_anuncios: discord.TextChannel,
    canal_chat: discord.TextChannel,
    canal_bienvenida: discord.TextChannel, canal_despedida: discord.TextChannel
):
    config[interaction.guild.id] = {
        "bienvenida": canal_bienvenida.id, "despedida": canal_despedida.id,
        "nombre_servidor": nombre_servidor, "descripcion_servidor": descripcion_servidor,
        "roles": roles,
        "canal_reglas": canal_reglas.id, "canal_anuncios": canal_anuncios.id,
        "canal_chat": canal_chat.id
    }
    push_state()
    embed = discord.Embed(
        title=f"✨ Panel de Bienvenida — {nombre_servidor} ✨",
        description=(
            f"🏙️ Has llegado a **{nombre_servidor}**, {descripcion_servidor}.\n"
            f"Aquí podrás convertirte en quien quieras: {roles}\n\n"
            "📋 **Pasos para empezar:**\n"
            f"1️⃣ Lee las reglas en {canal_reglas.mention}\n"
            f"2️⃣ Novedades en {canal_anuncios.mention}\n"
            f"3️⃣ Chat en {canal_chat.mention}\n\n"
            "🎭 • Respeto 🙌 • Creatividad 🎬 • Normas 🚫\n\n"
            f"🚀 ¡Bienvenido a **{nombre_servidor}**! 🎉"
        ),
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Bienvenidas en #{canal_bienvenida.name} | Despedidas en #{canal_despedida.name}")
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
    await canal.send(embed=embed)
    await interaction.response.send_message("✅ Panel creado y canales configurados.", ephemeral=True)

# ── Verificación ───────────────────────────────────────────
class VerificarBoton(discord.ui.View):
    def __init__(self, rol_id):
        super().__init__(timeout=None)
        self.rol_id = rol_id

    @discord.ui.button(label="✅ Verificarme", style=discord.ButtonStyle.green, custom_id="verificar")
    async def verificar(self, interaction: discord.Interaction, button: discord.ui.Button):
        rol = interaction.guild.get_role(self.rol_id)
        if rol in interaction.user.roles:
            await interaction.response.send_message("Ya estás verificado. ✅", ephemeral=True)
        else:
            await interaction.user.add_roles(rol)
            await interaction.response.send_message(f"¡Verificado! 🎉 Rol: **{rol.name}**.", ephemeral=True)

@tree.command(name="panel-verificacion", description="Crea un panel de verificación")
@app_commands.checks.has_permissions(administrator=True)
async def panel_verificacion(interaction: discord.Interaction, canal: discord.TextChannel,
                              rol: discord.Role, titulo: str, descripcion: str):
    embed = discord.Embed(title=titulo, description=descripcion, color=discord.Color.green())
    embed.set_footer(text="Toca el botón para verificarte")
    await canal.send(embed=embed, view=VerificarBoton(rol.id))
    await interaction.response.send_message("✅ Panel de verificación creado.", ephemeral=True)

# ── Tickets ────────────────────────────────────────────────
class CerrarTicket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Cerrar Ticket", style=discord.ButtonStyle.red, custom_id="cerrar_ticket")
    async def cerrar_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Cerrando en 5 segundos...", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.channel.delete()
        push_state()

class TicketBoton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Abrir Ticket", style=discord.ButtonStyle.blurple, custom_id="abrir_ticket")
    async def abrir_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        nombre_canal = f"ticket-{interaction.user.name}"
        canal_existente = discord.utils.get(guild.text_channels, name=nombre_canal)
        if canal_existente:
            await interaction.response.send_message(f"Ya tienes ticket: {canal_existente.mention}", ephemeral=True)
            return
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        canal_ticket = await guild.create_text_channel(nombre_canal, overwrites=overwrites)
        embed = discord.Embed(
            title="🎫 Ticket Abierto",
            description=f"Hola {interaction.user.mention}, el staff te atenderá pronto.",
            color=discord.Color.blue()
        )
        await canal_ticket.send(embed=embed, view=CerrarTicket())
        await interaction.response.send_message(f"✅ Ticket: {canal_ticket.mention}", ephemeral=True)
        add_event("ticket", interaction.user.name, f"Abrió {nombre_canal}")
        push_state()

@tree.command(name="panel-ticket", description="Crea un panel de tickets")
@app_commands.checks.has_permissions(administrator=True)
async def panel_ticket(interaction: discord.Interaction, canal: discord.TextChannel,
                       titulo: str, descripcion: str):
    embed = discord.Embed(title=titulo, description=descripcion, color=discord.Color.blue())
    embed.set_footer(text="Toca el botón para abrir un ticket")
    await canal.send(embed=embed, view=TicketBoton())
    await interaction.response.send_message("✅ Panel de tickets creado.", ephemeral=True)

# ════════════════════════════════════════════════════════════
TOKEN = os.getenv("DISCORD_TOKEN")
client.run(TOKEN)
