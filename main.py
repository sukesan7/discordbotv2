import discord
from discord.ext import commands
import os
from commands import setup_commands
from nba import start_nba_updates
from nfl import start_nfl_updates
from security import DISCORD_TOKEN, DISCORD_CHANNEL_ID_NBA, DISCORD_CHANNEL_ID_NFL
import asyncio
import wavelink

# discord intents
intents = discord.Intents.default()
intents.message_content = True  
intents.voice_states = True

# bot prefix (only recognize the "/")
bot = commands.Bot(command_prefix=".", intents=intents)

# Setup commands
setup_commands(bot)

# bot information
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    
    # nba and nfl update channels
    start_nba_updates(bot)
    start_nfl_updates(bot)

# run bot
if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
