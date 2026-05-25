import discord
from discord import app_commands
import os

intents = discord.Intents.default()
intents.members = True

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

@tree.command(name="anuncio", description="Envía un anuncio a todos los canales del servidor")
@app_commands.checks.has_permissions(administrator=True)
async def anuncio(interaction: discord.Interaction, mensaje: str):
    await interaction.response.defer()
    enviado = 0
    for canal in interaction.guild.text_channels:
        try:
            embed = discord.Embed(
                title="📢 Anuncio",
                description=mensaje,
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Anuncio de {interaction.user.name}")
            await canal.send(embed=embed)
            enviado += 1
        except:
            pass
    await interaction.followup.send(f"✅ Anuncio enviado a **{enviado}** canales.", ephemeral=True)
    
TOKEN = os.getenv("DISCORD_TOKEN")
client.run(TOKEN)
