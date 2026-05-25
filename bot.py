import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como: {bot.user}")
    await bot.change_presence(activity=discord.Game(name="!help"))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if "hola" in message.content.lower():
        await message.channel.send(f"¡Hola, {message.author.mention}! 👋")
    await bot.process_commands(message)

@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Latencia: **{latency}ms**")

@bot.command(name="saludar")
async def saludar(ctx, miembro: discord.Member = None):
    miembro = miembro or ctx.author
    await ctx.send(f"¡Hola, {miembro.mention}! 🎉")

@bot.command(name="info")
async def info(ctx):
    servidor = ctx.guild
    embed = discord.Embed(title=f"📋 Info de {servidor.name}", color=discord.Color.blue())
    embed.add_field(name="Miembros", value=servidor.member_count)
    embed.add_field(name="Canales", value=len(servidor.channels))
    await ctx.send(embed=embed)

@bot.command(name="limpiar")
@commands.has_permissions(manage_messages=True)
async def limpiar(ctx, cantidad: int = 5):
    await ctx.channel.purge(limit=cantidad + 1)
    msg = await ctx.send(f"🗑️ Se borraron **{cantidad}** mensajes.")
    await msg.delete(delay=3)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ No tienes permisos para usar este comando.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ No encontré ese usuario.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ Falta un argumento.")

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
