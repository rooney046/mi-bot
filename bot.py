import discord
from discord import app_commands
import os
import asyncio
import random
import yt_dlp

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    print(f"Bot conectado como: {client.user}")
    await client.change_presence(activity=discord.Game(name="/help"))

@tree.command(name="ping", description="Muestra la latencia del bot")
async def ping(interaction: discord.Interaction):
    latency = round(client.latency * 1000)
    await interaction.response.send_message(f"Pong! Latencia: **{latency}ms**")

@tree.command(name="saludar", description="Saluda a un usuario")
async def saludar(interaction: discord.Interaction, usuario: discord.Member = None):
    usuario = usuario or interaction.user
    await interaction.response.send_message(f"Hola, {usuario.mention}!")

@tree.command(name="info", description="Muestra informacion del servidor")
async def info(interaction: discord.Interaction):
    servidor = interaction.guild
    embed = discord.Embed(title=f"Info de {servidor.name}", color=discord.Color.blue())
    embed.add_field(name="Miembros", value=servidor.member_count)
    embed.add_field(name="Canales", value=len(servidor.channels))
    await interaction.response.send_message(embed=embed)

@tree.command(name="limpiar", description="Borra mensajes del canal")
@app_commands.checks.has_permissions(manage_messages=True)
async def limpiar(interaction: discord.Interaction, cantidad: int = 5):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"Se borraron **{cantidad}** mensajes.", ephemeral=True)

@tree.command(name="anuncio", description="Envia un anuncio a un canal especifico")
@app_commands.checks.has_permissions(administrator=True)
async def anuncio(interaction: discord.Interaction, canal: discord.TextChannel, mensaje: str):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(description=mensaje, color=discord.Color.red())
    embed.set_author(name="Anuncio")
    await canal.send(embed=embed)
    await interaction.followup.send(f"Anuncio enviado a {canal.mention}", ephemeral=True)

@tree.command(name="mensaje-ticket", description="Envia un mensaje embed dentro de un ticket abierto")
@app_commands.checks.has_permissions(administrator=True)
async def mensaje_ticket(interaction: discord.Interaction, mensaje: str):
    if not interaction.channel.name.startswith("ticket-"):
        await interaction.response.send_message("Este comando solo se puede usar dentro de un ticket.", ephemeral=True)
        return
    embed = discord.Embed(description=mensaje, color=discord.Color.gold())
    embed.set_author(name="Mensaje del Staff")
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Mensaje enviado.", ephemeral=True)

@tree.command(name="hola-bot", description="Habla con el bot como si fuera una persona")
async def hola_bot(interaction: discord.Interaction, mensaje: str):
    if interaction.channel.name != "comandos":
        await interaction.response.send_message("Este comando solo se puede usar en el canal #comandos.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    mensaje_lower = mensaje.lower()
    if any(p in mensaje_lower for p in ["hola", "hey", "buenas", "saludos"]):
        respuesta = f"Hola {interaction.user.mention}! Como estas? En que te puedo ayudar?"
    elif any(p in mensaje_lower for p in ["como estas", "que tal"]):
        respuesta = f"Estoy genial {interaction.user.mention}! Gracias por preguntar. Y tu?"
    elif any(p in mensaje_lower for p in ["adios", "chao", "bye", "hasta luego"]):
        respuesta = f"Hasta luego {interaction.user.mention}! Fue un placer hablar contigo."
    elif any(p in mensaje_lower for p in ["gracias", "thank"]):
        respuesta = f"De nada {interaction.user.mention}! Para eso estoy."
    elif any(p in mensaje_lower for p in ["quien eres", "que eres"]):
        respuesta = f"Soy **Hurban Bot**, el bot oficial de este servidor. Estoy aqui para ayudarte!"
    elif any(p in mensaje_lower for p in ["ayuda", "help", "comandos"]):
        respuesta = f"Claro {interaction.user.mention}! Puedes usar /ping, /info, /anuncio, /panel-ticket y muchos mas."
    elif any(p in mensaje_lower for p in ["aburrido", "aburrida"]):
        respuesta = f"Yo nunca me aburro {interaction.user.mention}! Siempre estoy monitoreando el servidor."
    elif any(p in mensaje_lower for p in ["amor", "te quiero", "te amo"]):
        respuesta = f"Yo tambien te quiero {interaction.user.mention}! Eres el mejor."
    elif any(p in mensaje_lower for p in ["chiste", "cuentame"]):
        chistes = [
            "Por que el libro de matematicas esta triste? Porque tiene demasiados problemas.",
            "Por que los pajaros vuelan hacia el sur? Porque caminar seria muy lejos!",
            "Que le dice un semaforo a otro? No me mires que me estoy cambiando!"
        ]
        respuesta = random.choice(chistes)
    else:
        respuestas_generales = [
            f"Interesante lo que dices, {interaction.user.mention}! Cuentame mas.",
            f"Eso es genial {interaction.user.mention}!",
            f"No estoy seguro de entenderte {interaction.user.mention}, puedes explicarme mejor?",
            f"Me parece muy bien {interaction.user.mention}!",
            f"Que interesante {interaction.user.mention}! No lo habia pensado asi."
        ]
        respuesta = random.choice(respuestas_generales)
    await interaction.channel.send(respuesta)
    await interaction.followup.send("Listo.", ephemeral=True)

# ── Anti Link ──────────────────────────────────────────────
canales_antilink = set()

@tree.command(name="antilink", description="Activa o desactiva el anti-link en un canal")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(canal="Canal donde aplicar el anti-link", activar="True para activar, False para desactivar")
async def antilink(interaction: discord.Interaction, canal: discord.TextChannel, activar: bool):
    if activar:
        canales_antilink.add(canal.id)
        await interaction.response.send_message(f"Anti-link activado en {canal.mention}", ephemeral=True)
    else:
        canales_antilink.discard(canal.id)
        await interaction.response.send_message(f"Anti-link desactivado en {canal.mention}", ephemeral=True)

# ── Anti Spam ──────────────────────────────────────────────
spam_control = {}

@tree.command(name="antispam", description="Activa o desactiva el anti-spam en el servidor")
@app_commands.checks.has_permissions(administrator=True)
async def antispam(interaction: discord.Interaction, activar: bool):
    config_spam = config.get(interaction.guild.id, {})
    config_spam["antispam"] = activar
    config[interaction.guild.id] = config_spam
    estado = "activado" if activar else "desactivado"
    await interaction.response.send_message(f"Anti-spam {estado}.", ephemeral=True)

# ── Malas palabras ─────────────────────────────────────────
MALAS_PALABRAS = [
    "mierda", "puta", "puto", "idiota", "imbecil", "pendejo",
    "cabron", "gay", "maricon", "maldito", "estupido", "culo",
    "joder", "cono", "verga", "chinga", "pinche", "gilipollas",
    "bastardo", "hdp", "ctm", "conchatumadre", "webon", "wey",
    "mamaguevo", "come mierda", "hijo de puta"
]

usuarios_aislados = set()

@client.event
async def on_message(message):
    if message.author.bot:
        return

    # Anti spam
    guild_config = config.get(message.guild.id, {})
    if guild_config.get("antispam"):
        autor_id = message.author.id
        ahora = asyncio.get_event_loop().time()
        if autor_id not in spam_control:
            spam_control[autor_id] = []
        spam_control[autor_id] = [t for t in spam_control[autor_id] if ahora - t < 5]
        spam_control[autor_id].append(ahora)
        if len(spam_control[autor_id]) >= 5:
            await message.delete()
            rol_aislado = discord.utils.get(message.guild.roles, name="Aislado")
            if not rol_aislado:
                rol_aislado = await message.guild.create_role(name="Aislado")
                for channel in message.guild.channels:
                    await channel.set_permissions(rol_aislado, send_messages=False, speak=False)
            await message.author.add_roles(rol_aislado)
            usuarios_aislados.add(autor_id)
            embed_spam = discord.Embed(
                title="Usuario Aislado por Spam",
                description=f"{message.author.mention} fue aislado 5 minutos por hacer spam.",
                color=discord.Color.orange()
            )
            await message.channel.send(embed=embed_spam, delete_after=10)
            canal_adv = discord.utils.get(message.guild.text_channels, name="advertencia")
            if canal_adv:
                embed_adv = discord.Embed(title="Advertencia - Spam Detectado", color=discord.Color.orange())
                embed_adv.add_field(name="Usuario", value=f"{message.author.mention} ({message.author.name})", inline=True)
                embed_adv.add_field(name="Duracion", value="5 minutos", inline=True)
                embed_adv.add_field(name="Motivo", value="Envio mas de 5 mensajes en 5 segundos.", inline=False)
                embed_adv.set_thumbnail(url=message.author.display_avatar.url)
                embed_adv.set_footer(text="El aislamiento se levantara automaticamente en 5 minutos.")
                await canal_adv.send(embed=embed_adv)
            spam_control[autor_id] = []
            await asyncio.sleep(300)
            await message.author.remove_roles(rol_aislado)
            usuarios_aislados.discard(autor_id)
            return

    # Anti link
    if message.channel.id in canales_antilink:
        if "http://" in message.content or "https://" in message.content or "discord.gg" in message.content:
            await message.delete()
            aviso = await message.channel.send(f"{message.author.mention} no se permiten links aqui.")
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
                title="Usuario Aislado",
                description=f"{message.author.mention} fue aislado por **{minutos} minutos** por usar lenguaje inapropiado.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed_canal, delete_after=10)
            canal_adv = discord.utils.get(message.guild.text_channels, name="advertencia")
            if canal_adv:
                embed_adv = discord.Embed(title="Advertencia - Usuario Aislado", color=discord.Color.red())
                embed_adv.add_field(name="Usuario", value=f"{message.author.mention} ({message.author.name})", inline=True)
                embed_adv.add_field(name="Duracion", value=f"{minutos} minutos", inline=True)
                embed_adv.add_field(name="Canal", value=message.channel.mention, inline=True)
                embed_adv.add_field(name="Motivo", value=f"Se detecto la palabra prohibida **{palabra}** en su mensaje.", inline=False)
                embed_adv.add_field(name="Explicacion", value="El servidor no permite el uso de lenguaje ofensivo, vulgar o discriminatorio. El usuario ha sido aislado temporalmente por violar las normas del servidor.", inline=False)
                embed_adv.set_thumbnail(url=message.author.display_avatar.url)
                embed_adv.set_footer(text=f"El aislamiento se levantara automaticamente en {minutos} minutos.")
                await canal_adv.send(embed=embed_adv)
            await asyncio.sleep(segundos)
            await message.author.remove_roles(rol_aislado)
            usuarios_aislados.discard(message.author.id)
            break

# ── Configuracion ──────────────────────────────────────────
config = {}

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
    embed.set_footer(text=f"Bienvenidas en {canal_bienvenida.name} | Despedidas en {canal_despedida.name}")
    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
    await canal.send(embed=embed)
    await interaction.response.send_message("Panel de bienvenida creado y canales configurados.", ephemeral=True)

@client.event
async def on_member_join(member):
    guild_config = config.get(member.guild.id)
    if guild_config:
        canal = client.get_channel(guild_config["bienvenida"])
        if canal:
            embed = discord.Embed(
                title="Bienvenido!",
                description=f"Bienvenido al servidor, {member.mention}! Ya somos **{member.guild.member_count}** miembros.",
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
                title="Hasta luego!",
                description=f"**{member.name}** ha abandonado el servidor.",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await canal.send(embed=embed)

class VerificarBoton(discord.ui.View):
    def __init__(self, rol_id):
        super().__init__(timeout=None)
        self.rol_id = rol_id

    @discord.ui.button(label="Verificarme", style=discord.ButtonStyle.green, custom_id="verificar")
    async def verificar(self, interaction: discord.Interaction, button: discord.ui.Button):
        rol = interaction.guild.get_role(self.rol_id)
        if rol in interaction.user.roles:
            await interaction.response.send_message("Ya estas verificado.", ephemeral=True)
        else:
            await interaction.user.add_roles(rol)
            await interaction.response.send_message(f"Verificado! Ahora tienes el rol **{rol.name}**.", ephemeral=True)

@tree.command(name="panel-verificacion", description="Crea un panel de verificacion con boton")
@app_commands.checks.has_permissions(administrator=True)
async def panel_verificacion(
    interaction: discord.Interaction,
    canal: discord.TextChannel,
    rol: discord.Role,
    titulo: str,
    descripcion: str
):
    embed = discord.Embed(title=titulo, description=descripcion, color=discord.Color.green())
    embed.set_footer(text="Toca el boton para verificarte")
    await canal.send(embed=embed, view=VerificarBoton(rol.id))
    await interaction.response.send_message("Panel de verificacion creado.", ephemeral=True)

class CerrarTicket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Cerrar Ticket", style=discord.ButtonStyle.red, custom_id="cerrar_ticket")
    async def cerrar_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Cerrando ticket en 5 segundos...", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketBoton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Abrir Ticket", style=discord.ButtonStyle.blurple, custom_id="abrir_ticket")
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
            title="Ticket Abierto",
            description=f"Hola {interaction.user.mention}, el staff te atendera pronto. Para cerrar el ticket usa el boton de abajo.",
            color=discord.Color.blue()
        )
        await canal_ticket.send(embed=embed, view=CerrarTicket())
        await interaction.response.send_message(f"Ticket creado: {canal_ticket.mention}", ephemeral=True)

@tree.command(name="panel-ticket", description="Crea un panel de tickets")
@app_commands.checks.has_permissions(administrator=True)
async def panel_ticket(
    interaction: discord.Interaction,
    canal: discord.TextChannel,
    titulo: str,
    descripcion: str
):
    embed = discord.Embed(title=titulo, description=descripcion, color=discord.Color.blue())
    embed.set_footer(text="Toca el boton para abrir un ticket")
    await canal.send(embed=embed, view=TicketBoton())
    await interaction.response.send_message("Panel de tickets creado.", ephemeral=True)

# ── Musica ─────────────────────────────────────────────────
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

YDL_OPTIONS = {
    'format': 'bestaudio',
    'noplaylist': True,
    'quiet': True
}

colas = {}

def get_cola(guild_id):
    if guild_id not in colas:
        colas[guild_id] = []
    return colas[guild_id]

@tree.command(name="play", description="Reproduce una cancion en el canal de voz")
async def play(interaction: discord.Interaction, cancion: str):
    if not interaction.user.voice:
        await interaction.response.send_message("Debes estar en un canal de voz.", ephemeral=True)
        return
    await interaction.response.defer()
    canal_voz = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client
    if not voice_client:
        voice_client = await canal_voz.connect()
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(f"ytsearch:{cancion}", download=False)
        if 'entries' in info:
            info = info['entries'][0]
        url = info['url']
        titulo = info['title']
        duracion = info.get('duration', 0)
        mins = duracion // 60
        segs = duracion % 60
    if voice_client.is_playing():
        get_cola(interaction.guild.id).append((url, titulo))
        embed = discord.Embed(title="Agregado a la cola", description=f"**{titulo}**", color=discord.Color.blue())
        await interaction.followup.send(embed=embed)
        return
    voice_client.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS))
    embed = discord.Embed(title="Reproduciendo ahora", description=f"**{titulo}**", color=discord.Color.green())
    embed.add_field(name="Duracion", value=f"{mins}:{segs:02d}")
    embed.add_field(name="Pedido por", value=interaction.user.mention)
    await interaction.followup.send(embed=embed)

@tree.command(name="skip", description="Salta la cancion actual")
async def skip(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await interaction.response.send_message("Cancion saltada.", ephemeral=True)
    else:
        await interaction.response.send_message("No hay musica reproduciendose.", ephemeral=True)

@tree.command(name="stop", description="Para la musica y desconecta el bot")
async def stop(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client:
        colas[interaction.guild.id] = []
        await voice_client.disconnect()
        await interaction.response.send_message("Musica detenida.", ephemeral=True)
    else:
        await interaction.response.send_message("El bot no esta en un canal de voz.", ephemeral=True)

@tree.command(name="cola", description="Muestra la cola de canciones")
async def cola(interaction: discord.Interaction):
    cola_actual = get_cola(interaction.guild.id)
    if not cola_actual:
        await interaction.response.send_message("La cola esta vacia.", ephemeral=True)
        return
    embed = discord.Embed(title="Cola de canciones", color=discord.Color.blue())
    for i, (_, titulo) in enumerate(cola_actual, 1):
        embed.add_field(name=f"{i}.", value=titulo, inline=False)
    await interaction.response.send_message(embed=embed)

TOKEN = os.getenv("DISCORD_TOKEN")
client.run(TOKEN)
