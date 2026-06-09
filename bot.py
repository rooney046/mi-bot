import discord
from discord import app_commands
import os
import asyncio

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
@app_commands.describe(
    canal="Canal donde enviar el anuncio",
    mensaje="Mensaje del anuncio",
    link="Link que se incluirá en el anuncio (opcional)",
    texto_link="Texto visible del link (opcional, por defecto: Ver más)"
)
async def anuncio(
    interaction: discord.Interaction,
    canal: discord.TextChannel,
    mensaje: str,
    link: str = None,
    texto_link: str = "Ver más"
):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(description=mensaje, color=discord.Color.red())
    embed.set_author(name="📢 Anuncio")
    if link:
        embed.add_field(name="🔗 Link", value=f"[{texto_link}]({link})", inline=False)
    await canal.send(embed=embed)
    await interaction.followup.send(f"✅ Anuncio enviado a {canal.mention}", ephemeral=True)

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
MALAS_PALABRAS = ["mierda", "puta", "idiota", "imbecil", "pendejo", "cabron"]

@client.event
async def on_message(message):
    if message.author.bot:
        return

    # Anti link
    if message.channel.id in canales_antilink:
        if "http://" in message.content or "https://" in message.content or "discord.gg" in message.content:
            await message.delete()
            aviso = await message.channel.send(f"🚫 {message.author.mention} no se permiten links aquí.")
            await asyncio.sleep(5)
            await aviso.delete()
            return

    # Malas palabras
    contenido = message.content.lower()
    for palabra in MALAS_PALABRAS:
        if palabra in contenido:
            await message.delete()
            rol_aislado = discord.utils.get(message.guild.roles, name="Aislado")
            if not rol_aislado:
                rol_aislado = await message.guild.create_role(name="Aislado")
                for channel in message.guild.channels:
                    await channel.set_permissions(rol_aislado, send_messages=False, speak=False)
            await message.author.add_roles(rol_aislado)
            aviso = await message.channel.send(
                f"🔇 {message.author.mention} fue aislado 5 minutos por usar lenguaje inapropiado."
            )
            await asyncio.sleep(300)
            await message.author.remove_roles(rol_aislado)
            await aviso.delete()
            break

# ── Configuración ──────────────────────────────────────────
config = {}

# ── Panel de bienvenida ────────────────────────────────────
@tree.command(name="panel-bienvenida", description="Crea un panel de bienvenida en un canal")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    canal="Canal donde mostrar el panel",
    nombre_servidor="Nombre del servidor (ej: Aguado Studio)",
    descripcion_servidor="Descripción corta del servidor (ej: el mejor servidor de Roleplay en Roblox)",
    roles="Roles que puede tener el usuario (ej: policía, médico, bombero...)",
    canal_reglas="Canal de reglas",
    canal_anuncios="Canal de anuncios",
    canal_chat="Canal de chat",
    canal_bienvenida="Canal donde enviar bienvenidas",
    canal_despedida="Canal donde enviar despedidas"
)
async def panel_bienvenida(
    interaction: discord.Interaction,
    canal: discord.TextChannel,
    nombre_servidor: str,
    descripcion_servidor: str,
    roles: str,
    canal_reglas: discord.TextChannel,
    canal_anuncios: discord.TextChannel,
    canal_chat: discord.TextChannel,
    canal_bienvenida: discord.TextChannel,
    canal_despedida: discord.TextChannel
):
    config[interaction.guild.id] = {
        "bienvenida": canal_bienvenida.id,
        "despedida": canal_despedida.id,
        "nombre_servidor": nombre_servidor,
        "descripcion_servidor": descripcion_servidor,
        "roles": roles,
        "canal_reglas": canal_reglas.id,
        "canal_anuncios": canal_anuncios.id,
        "canal_chat": canal_chat.id
    }
    embed = discord.Embed(
        title=f"✨ Panel de Bienvenida — {nombre_servidor} ✨",
        description=(
            f"🏙️ Has llegado a **{nombre_servidor}**, {descripcion_servidor}.\n"
            f"Aquí podrás convertirte en quien quieras: {roles}\n"
            "con tus propias historias.\n\n"
            f"📋 **Pasos importantes para empezar:**\n"
            f"1️⃣ Lee las reglas en {canal_reglas.mention}\n"
            f"2️⃣ Mira las novedades en {canal_anuncios.mention}\n"
            f"3️⃣ Pasa por {canal_chat.mention}\n\n"
            "🎭 **Recuerda:**\n"
            "• El respeto es fundamental 🙌\n"
            "• Juega con creatividad y realismo 🎬\n"
            "• Cumple las normas para no recibir sanciones 🚫\n\n"
            f"🚀 ¡Gracias por unirte a nuestra comunidad!\n"
            f"Tu segunda vida comienza ahora en **{nombre_servidor}** 🎉"
        ),
        color=discord.Color.green()
    )
    embed.set_footer(text=f"🎉 Bienvenidas en #{canal_bienvenida.name} | Despedidas en #{canal_despedida.name}")
    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
    await canal.send(embed=embed)
    await interaction.response.send_message("✅ Panel de bienvenida creado y canales configurados.", ephemeral=True)

@client.event
async def on_member_join(member):
    guild_config = config.get(member.guild.id)
    if guild_config:
        canal = client.get_channel(guild_config["bienvenida"])
        nombre_servidor = guild_config.get("nombre_servidor", member.guild.name)
        roles = guild_config.get("roles", "policía 🚓, médico 🚑, bombero 🔥")
        canal_reglas_id = guild_config.get("canal_reglas")
        canal_anuncios_id = guild_config.get("canal_anuncios")
        canal_chat_id = guild_config.get("canal_chat")
        canal_reglas_mention = f"<#{canal_reglas_id}>" if canal_reglas_id else "#reglas"
        canal_anuncios_mention = f"<#{canal_anuncios_id}>" if canal_anuncios_id else "#anuncios"
        canal_chat_mention = f"<#{canal_chat_id}>" if canal_chat_id else "#chat"
        if canal:
            embed = discord.Embed(
                title=f"✨ Bienvenido/a {member.name} ✨",
                description=(
                    f"🏙️ Has llegado a **{nombre_servidor}**, el mejor servidor de Roleplay en Roblox.\n"
                    f"Aquí podrás convertirte en quien quieras: {roles}\n"
                    "con tus propias historias.\n\n"
                    "📋 **Pasos importantes para empezar:**\n"
                    f"1️⃣ Lee las reglas en {canal_reglas_mention}\n"
                    f"2️⃣ Mira las novedades en {canal_anuncios_mention}\n"
                    f"3️⃣ Pasa por {canal_chat_mention}\n\n"
                    "🎭 **Recuerda:**\n"
                    "• El respeto es fundamental 🙌\n"
                    "• Juega con creatividad y realismo 🎬\n"
                    "• Cumple las normas para no recibir sanciones 🚫\n\n"
                    f"🚀 ¡Gracias por unirte a nuestra comunidad!\n"
                    f"Tu segunda vida comienza ahora en **{nombre_servidor}** 🎉"
                ),
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await canal.send(embed=embed)

@client.event
async def on_member_remove(member):
    guild_config = config.get(member.guild.id)
    if guild_config:
        canal = client.get_channel(guild_config["despedida"])
        nombre_servidor = guild_config.get("nombre_servidor", member.guild.name)
        if canal:
            embed = discord.Embed(
                title=f"👋 {member.name} ha salido del servidor...",
                description=(
                    f"🏙️ Hoy nos despedimos de un ciudadano más de **{nombre_servidor}**.\n"
                    "Quizás su historia termine aquí, o tal vez solo sea una pausa.\n\n"
                    "💭 Cada rol deja recuerdos:\n"
                    "• Risas compartidas 😂\n"
                    "• Aventuras vividas 🚀\n"
                    "• Amistades creadas 🤝\n\n"
                    "✨ Aunque ya no esté en la ciudad,\n"
                    "las puertas siempre estarán abiertas para volver.\n\n"
                    "🚪 ¡Hasta pronto, viajero de Roleplay!"
                ),
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await canal.send(embed=embed)

# ── Panel de verificación ──────────────────────────────────
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
            await interaction.response.send_message(f"¡Verificado! 🎉 Ahora tienes el rol **{rol.name}**.", ephemeral=True)

@tree.command(name="panel-verificacion", description="Crea un panel de verificación con botón")
@app_commands.checks.has_permissions(administrator=True)
async def panel_verificacion(
    interaction: discord.Interaction,
    canal: discord.TextChannel,
    rol: discord.Role,
    titulo: str,
    descripcion: str
):
    embed = discord.Embed(title=titulo, description=descripcion, color=discord.Color.green())
    embed.set_footer(text="Toca el botón para verificarte")
    await canal.send(embed=embed, view=VerificarBoton(rol.id))
    await interaction.response.send_message("✅ Panel de verificación creado.", ephemeral=True)

# ── Panel de Tickets ───────────────────────────────────────
class CerrarTicket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Cerrar Ticket", style=discord.ButtonStyle.red, custom_id="cerrar_ticket")
    async def cerrar_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Cerrando ticket en 5 segundos...", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketBoton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Abrir Ticket", style=discord.ButtonStyle.blurple, custom_id="abrir_ticket")
    async def abrir_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        nombre_canal = f"ticket-{interaction.user.name}"
        canal_existente = discord.utils.get(guild.text_channels, name=nombre_canal)
        if canal_existente:
            await interaction.response.send_message(f"Ya tienes un ticket abierto: {canal_existente.mention}", ephemeral=True)
            return
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        canal_ticket = await guild.create_text_channel(nombre_canal, overwrites=overwrites)
        embed = discord.Embed(
            title="🎫 Ticket Abierto",
            description=f"Hola {interaction.user.mention}, el staff te atenderá pronto.\nPara cerrar el ticket usa el botón de abajo.",
            color=discord.Color.blue()
        )
        await canal_ticket.send(embed=embed, view=CerrarTicket())
        await interaction.response.send_message(f"✅ Ticket creado: {canal_ticket.mention}", ephemeral=True)

@tree.command(name="panel-ticket", description="Crea un panel de tickets")
@app_commands.checks.has_permissions(administrator=True)
async def panel_ticket(
    interaction: discord.Interaction,
    canal: discord.TextChannel,
    titulo: str,
    descripcion: str
):
    embed = discord.Embed(title=titulo, description=descripcion, color=discord.Color.blue())
    embed.set_footer(text="Toca el botón para abrir un ticket")
    await canal.send(embed=embed, view=TicketBoton())
    await interaction.response.send_message("✅ Panel de tickets creado.", ephemeral=True)

TOKEN = os.getenv("DISCORD_TOKEN")
client.run(TOKEN)
