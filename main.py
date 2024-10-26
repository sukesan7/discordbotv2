import discord
from discord.ext import commands
from commands import setup_commands
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

# Intents for the discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# Bot Prefix
bot = commands.Bot(command_prefix=".", intents=intents)

# Setup commands
setup_commands(bot)

# Send the latest NBA and NFL data to the specific channels
async def send_latest_nba_data():
    nba_odds_channel = bot.get_channel(DISCORD_CHANNEL_ID_NBA_ODDS)
    nba_news_channel = bot.get_channel(DISCORD_CHANNEL_ID_NBA_NEWS)

    odds_embed = await fetch_latest_nba_odds()
    news_embed = await fetch_latest_nba_news()

    # Check and send NBA odds
    if isinstance(odds_embed, str):
        odds_embed = discord.Embed(title="Error Fetching NBA Odds", description=odds_embed, color=discord.Color.red())
    if nba_odds_channel:
        await nba_odds_channel.send(embed=odds_embed)

    # Check and send NBA news
    if isinstance(news_embed, str):
        news_embed = discord.Embed(title="Error Fetching NBA News", description=news_embed, color=discord.Color.red())
    if nba_news_channel:
        await nba_news_channel.send(embed=news_embed)

async def send_latest_nfl_data():
    nfl_odds_channel = bot.get_channel(DISCORD_CHANNEL_ID_NFL_ODDS)
    nfl_news_channel = bot.get_channel(DISCORD_CHANNEL_ID_NFL_NEWS)

    odds_embed = await fetch_latest_nfl_odds()
    news_embed = await fetch_latest_nfl_news()

    # Check and send NFL odds
    if isinstance(odds_embed, str):
        odds_embed = discord.Embed(title="Error Fetching NFL Odds", description=odds_embed, color=discord.Color.red())
    if nfl_odds_channel:
        await nfl_odds_channel.send(embed=odds_embed)

    # Check and send NFL news
    if isinstance(news_embed, str):
        news_embed = discord.Embed(title="Error Fetching NFL News", description=news_embed, color=discord.Color.red())
    if nfl_news_channel:
        await nfl_news_channel.send(embed=news_embed)

# Start the discord bot
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

    # Add a delay to ensure the bot is fully ready
    await asyncio.sleep(5)

    # Send the latest data initially
    await send_latest_nba_data()
    await send_latest_nfl_data()

    print("Initial NBA and NFL news has been sent.")

    # Start NBA and NFL updates
    start_nba_updates(bot)
    start_nfl_updates(bot)

    print("NBA and NFL update loops have started.")

# Run the discord bot
if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
