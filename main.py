import discord
from discord.ext import tasks, commands

from nba import NBA  # Import the new NBA class
from nfl import get_nfl_injury_report  # Assuming the NFL scraping function exists

from security import DISCORD_TOKEN, NBA_CHANNEL_ID, NFL_CHANNEL_ID

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

# Create an instance of the NBA class
nba = NBA(bot)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    nba.scrape_nba.start()  # Start the NBA scraping task
    check_nfl_injuries.start()  # Start the NFL scraping task (assuming function exists)

@tasks.loop(minutes=30)
async def check_nfl_injuries():
    channel = bot.get_channel(NFL_CHANNEL_ID)
    if channel:
        nfl_report = get_nfl_injury_report()  # Assuming the function exists
        await channel.send(nfl_report)

async def main():
    # Load slash commands from the commands module (if applicable)
    # await bot.load_extension('commands')
    # Run the bot
    await bot.start(DISCORD_TOKEN)

# Run the bot using asyncio.run for proper event loop management
import asyncio
asyncio.run(main())