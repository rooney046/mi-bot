import discord
from discord import app_commands
import os
import asyncio
import datetime

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

MALAS_PALABRAS = ["mierda", "puta", "idiota", "imbecil", "pendejo", "cabron"]

@client.event
async def on_message(message):
    if message.author.bot:
        return
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

config = {}

@tree.command(name="configurar", description="Configura los canales de bienvenida y despedida")
@app_commands.checks.has_permissions(administrator=True)
async def configurar(interaction: discord.Interaction, bienvenida: discord.TextChannel, despedida: discord.TextChannel):
    config[interaction.guild.id] = {"bienvenida": bienvenida.id, "despedida": despedida.id}
    embed = discord.Embed(title="✅ Configuración guardada", color=discord.Color.green())
    embed.add_field(name="👋 Bienvenida", value=bienvenida.mention)
    embed.add_field(name="👋 Despedida", value=despedida.mention)
    await interaction.response.send_message(embed=embed, ephemeral=True)

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

TOKEN = os.getenv("DISCORD_TOKEN")
client.run(TOKEN)
