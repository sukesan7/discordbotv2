import discord
from discord.ext import tasks
import requests
import json

NBA_SCORES_URL = "http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
NBA_NEWS_URL = "http://site.api.espn.com/apis/site/v2/sports/basketball/nba/news"
DISCORD_CHANNEL_ID_NBA = 1298131694565462068  # Replace with your NBA channel ID

def start_nba_updates(bot):
    """Start NBA updates when the bot is ready."""
    
    @tasks.loop(minutes=10)
    async def fetch_nba_scores():
        """Fetch and update NBA scores to the specified Discord channel."""
        try:
            response = requests.get(NBA_SCORES_URL)
            data = response.json()
            games = data.get('events', [])

            if not games:
                print("No NBA games found in the API response.")
                return

            for game in games:
                home_team = game['competitions'][0]['competitors'][0]['team']['displayName']
                away_team = game['competitions'][0]['competitors'][1]['team']['displayName']
                home_score = game['competitions'][0]['competitors'][0]['score']
                away_score = game['competitions'][0]['competitors'][1]['score']
                status = game['status']['type']['name']

                description = f"{home_team} vs {away_team}\nScore: {home_score} - {away_score}\nStatus: {status}"
                
                embed = discord.Embed(
                    title=f"NBA Score Update: {home_team} vs {away_team}",
                    description=description,
                    color=discord.Color.blue()
                )

                channel = bot.get_channel(DISCORD_CHANNEL_ID_NBA)
                await channel.send(embed=embed)
        
        except Exception as e:
            print(f"Error fetching NBA scores: {e}")

    @tasks.loop(minutes=10)
    async def fetch_nba_news():
        """Fetch and update NBA news to the specified Discord channel."""
        try:
            response = requests.get(NBA_NEWS_URL)
            data = response.json()
            articles = data.get('articles', [])

            if not articles:
                print("No NBA news found in the API response.")
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

                channel = bot.get_channel(DISCORD_CHANNEL_ID_NBA)
                await channel.send(embed=embed)
        
        except Exception as e:
            print(f"Error fetching NBA news: {e}")

    # Start the loops when the bot is ready
    @bot.event
    async def on_ready():
        fetch_nba_scores.start()
        fetch_nba_news.start()
        print("NBA updates have started.")

