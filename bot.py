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
async def anuncio(interaction: discord.Interaction, canal: discord.TextChannel, mensaje: str):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(description=mensaje, color=discord.Color.red())
    embed.set_author(name="📢 Anuncio")
    await canal.send(embed=embed)
    await interaction.followup.send(f"✅ Anuncio enviado a {canal.mention}", ephemeral=True)

# ── Anuncio Global ─────────────────────────────────────────
@tree.command(name="anuncio-global", description="Envía un anuncio a todos los canales de texto del servidor")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    mensaje="El mensaje del anuncio",
    titulo="Título del anuncio (opcional)",
    color="Color del embed: rojo, azul, verde, dorado (por defecto: rojo)"
)
async def anuncio_global(
    interaction: discord.Interaction,
    mensaje: str,
    titulo: str = "📢 Anuncio Global",
    color: str = "rojo"
):
    await interaction.response.defer(ephemeral=True)

    colores = {
        "rojo": discord.Color.red(),
        "azul": discord.Color.blue(),
        "verde": discord.Color.green(),
        "dorado": discord.Color.gold()
    }
    color_embed = colores.get(color.lower(), discord.Color.red())

    embed = discord.Embed(
        title=titulo,
        description=mensaje,
        color=color_embed,
        timestamp=discord.utils.utcnow()
    )
    embed.set_author(
        name=interaction.user.display_name,
        icon_url=interaction.user.display_avatar.url
    )
    embed.set_footer(
        text=f"Servidor: {interaction.guild.name}",
        icon_url=interaction.guild.icon.url if interaction.guild.icon else None
    )

    enviados = 0
    fallidos = 0

    for canal in interaction.guild.text_channels:
        perms = canal.permissions_for(interaction.guild.me)
        if perms.send_messages and perms.embed_links:
            try:
                await canal.send(embed=embed)
                enviados += 1
            except Exception:
                fallidos += 1

    resumen = f"✅ Anuncio global enviado a **{enviados}** canal(es)."
    if fallidos:
        resumen += f"\n⚠️ No se pudo enviar a **{fallidos}** canal(es) por falta de permisos."

    await interaction.followup.send(resumen, ephemeral=True)

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
async def panel_bienvenida(
    interaction: discord.Interaction,
    canal: discord.TextChannel,
    titulo: str,
    descripcion: str,
    canal_bienvenida: discord.TextChannel,
    canal_despedida: discord.TextChannel
):
    config[interaction.guild.id] = {
        "bienvenida": canal_bienvenida.id,
        "despedida": canal_despedida.id
    }
    embed = discord.Embed(title=titulo, description=descripcion, color=discord.Color.blue())
    embed.set_footer(text=f"🎉 Bienvenidas en {canal_bienvenida.name} | Despedidas en {canal_despedida.name}")
    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
    await canal.send(embed=embed)
    await interaction.response.send_message("✅ Panel de bienvenida creado y canales configurados.", ephemeral=True)

@client.event
async def on_member_join(member):
    guild_config = config.get(member.guild.id)
    if guild_config:
        canal = client.get_channel(guild_config["bienvenida"])
        if canal:
            embed = discord.Embed(
                title="👋 ¡Bienvenido!",
                description=f"¡Bienvenido al servidor, {member.mention}!\nYa somos **{member.guild.member_count}** miembros.",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await canal.send(embed=embed)

@client.event
async def on_member_remove(member):
    guild_config = config.get(member.guild.id)
    if guild_config:
        canal = client.get_channel(guild_config["despedida"])
        if canal:
            embed = discord.Embed(
                title="👋 ¡Hasta luego!",
                description=f"**{member.name}** ha abandonado el servidor.",
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
