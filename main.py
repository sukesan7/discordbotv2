import discord
from discord.ext import commands
from nba import start_nba_updates, fetch_latest_nba_odds, fetch_latest_nba_news
from nfl import start_nfl_updates, fetch_latest_nfl_odds, fetch_latest_nfl_news
import asyncio
from security import (
    DISCORD_TOKEN,
    DISCORD_CHANNEL_ID_NBA_NEWS,
    DISCORD_CHANNEL_ID_NBA_ODDS,
    DISCORD_CHANNEL_ID_NFL_NEWS,
    DISCORD_CHANNEL_ID_NFL_ODDS,
)

# Intents setup for the bot
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# Initialize the bot
bot = commands.Bot(command_prefix="/", intents=intents)

async def load_extensions():
    """Load all necessary extensions (Cogs)."""
    await bot.load_extension('commands')  # Ensure `commands.py` Cog is loaded

# Send the latest NBA data to the specified channels
async def send_latest_nba_data():
    nba_odds_channel = bot.get_channel(DISCORD_CHANNEL_ID_NBA_ODDS)
    nba_news_channel = bot.get_channel(DISCORD_CHANNEL_ID_NBA_NEWS)

    odds_embed = await fetch_latest_nba_odds()
    news_embed = await fetch_latest_nba_news()

    # Send NBA odds
    if isinstance(odds_embed, str):
        odds_embed = discord.Embed(title="Error Fetching NBA Odds", description=odds_embed, color=discord.Color.red())
    if nba_odds_channel:
        await nba_odds_channel.send(embed=odds_embed)

    # Send NBA news
    if isinstance(news_embed, str):
        news_embed = discord.Embed(title="Error Fetching NBA News", description=news_embed, color=discord.Color.red())
    if nba_news_channel:
        await nba_news_channel.send(embed=news_embed)

# Send the latest NFL data to the specified channels
async def send_latest_nfl_data():
    nfl_odds_channel = bot.get_channel(DISCORD_CHANNEL_ID_NFL_ODDS)
    nfl_news_channel = bot.get_channel(DISCORD_CHANNEL_ID_NFL_NEWS)

    odds_embed = await fetch_latest_nfl_odds()
    news_embed = await fetch_latest_nfl_news()

    # Send NFL odds
    if isinstance(odds_embed, str):
        odds_embed = discord.Embed(title="Error Fetching NFL Odds", description=odds_embed, color=discord.Color.red())
    if nfl_odds_channel:
        await nfl_odds_channel.send(embed=odds_embed)

    # Send NFL news
    if isinstance(news_embed, str):
        news_embed = discord.Embed(title="Error Fetching NFL News", description=news_embed, color=discord.Color.red())
    if nfl_news_channel:
        await nfl_news_channel.send(embed=news_embed)

@bot.event
async def on_ready():
    """Event handler for when the bot is ready."""
    print(f'Logged in as {bot.user.name}')

    # Add a short delay to ensure the bot is fully initialized
    await asyncio.sleep(5)

    # Send initial NBA and NFL data
    await send_latest_nba_data()
    await send_latest_nfl_data()

    print("Initial NBA and NFL data sent.")

    # Start the periodic NBA and NFL updates
    start_nba_updates(bot)
    start_nfl_updates(bot)

    print("NBA and NFL update loops started.")

    # Sync application (slash) commands
    try:
        await bot.tree.sync()
        print("Slash commands synced successfully.")
    except Exception as e:
        print(f"Error syncing slash commands: {e}")

async def main():
    """Main function to start the bot."""
    async with bot:
        await load_extensions()  # Load the commands Cog
        await bot.start(DISCORD_TOKEN)  # Start the bot

if __name__ == '__main__':
    # Run the bot using asyncio's event loop
    asyncio.run(main())
