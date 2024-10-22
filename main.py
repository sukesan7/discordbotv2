import discord
from discord.ext import tasks
from nba import get_nba_injury_report
from nfl import get_nfl_injury_report
from commands import MyClient
from security import DISCORD_TOKEN, DISCORD_CHANNEL_ID

client = MyClient()

@tasks.loop(hours=12)
async def post_injury_reports():
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        nba_report = get_nba_injury_report()
        nfl_report = get_nfl_injury_report()
        await channel.send(nba_report)
        await channel.send(nfl_report)

@client.event
async def on_ready():
    post_injury_reports.start()
    print(f'Logged in as {client.user}')

client.run(DISCORD_TOKEN)
