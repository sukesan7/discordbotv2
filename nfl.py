import discord
from discord.ext import tasks
import requests
import json

NFL_SCORES_URL = "http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
NFL_NEWS_URL = "http://site.api.espn.com/apis/site/v2/sports/football/nfl/news"
DISCORD_CHANNEL_ID_NFL = 1298131671542927371  # Replace with your NFL channel ID

def start_nfl_updates(bot):
    """Start NFL updates when the bot is ready."""

    @tasks.loop(minutes=10)
    async def fetch_nfl_scores():
        """Fetch and update NFL scores to the specified Discord channel."""
        try:
            response = requests.get(NFL_SCORES_URL)
            data = response.json()
            games = data.get('events', [])

            if not games:
                print("No NFL games found in the API response.")
                return

            for game in games:
                home_team = game['competitions'][0]['competitors'][0]['team']['displayName']
                away_team = game['competitions'][0]['competitors'][1]['team']['displayName']
                home_score = game['competitions'][0]['competitors'][0]['score']
                away_score = game['competitions'][0]['competitors'][1]['score']
                status = game['status']['type']['name']

                description = f"{home_team} vs {away_team}\nScore: {home_score} - {away_score}\nStatus: {status}"

                embed = discord.Embed(
                    title=f"NFL Score Update: {home_team} vs {away_team}",
                    description=description,
                    color=discord.Color.blue()
                )

                channel = bot.get_channel(DISCORD_CHANNEL_ID_NFL)
                await channel.send(embed=embed)

        except Exception as e:
            print(f"Error fetching NFL scores: {e}")

    @tasks.loop(minutes=10)
    async def fetch_nfl_news():
        """Fetch and update NFL news to the specified Discord channel."""
        try:
            response = requests.get(NFL_NEWS_URL)
            data = response.json()
            articles = data.get('articles', [])

            if not articles:
                print("No NFL news found in the API response.")
                return

            for article in articles[:5]:  # Limit to the top 5 news articles
                title = article.get('headline', 'No title')
                description = article.get('description', 'No description available')
                link = article.get('links', {}).get('web', {}).get('href', 'No link available')

                embed = discord.Embed(
                    title=title,
                    description=description,
                    url=link,
                    color=discord.Color.orange()
                )

                channel = bot.get_channel(DISCORD_CHANNEL_ID_NFL)
                await channel.send(embed=embed)
        
        except Exception as e:
            print(f"Error fetching NFL news: {e}")

    # Start the loops when the bot is ready
    @bot.event
    async def on_ready():
        fetch_nfl_scores.start()
        fetch_nfl_news.start()
        print("NFL updates have started.")
