import discord
from discord.ext import tasks
import requests
from security import ODDS_API_KEY, DISCORD_CHANNEL_ID_NFL_NEWS, DISCORD_CHANNEL_ID_NFL_ODDS

# --------------------------------------------------------------------------
# ------------------------------ Declarations ------------------------------
# --------------------------------------------------------------------------

NFL_SCORES_URL = "http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
NFL_NEWS_URL = "http://site.api.espn.com/apis/site/v2/sports/football/nfl/news"
NFL_ODDS_URL = f"https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"

# Cache variables to store the last fetched data
last_odds_data = None
last_news_data = None
last_scores_data = None

# -----------------------------------------------------------------------
# ------------------------------ Functions ------------------------------
# -----------------------------------------------------------------------

async def fetch_latest_nfl_odds():
    """Fetch the latest NFL odds and compare with the last fetched data."""
    global last_odds_data
    try:
        response = requests.get(f"{NFL_ODDS_URL}?apiKey={ODDS_API_KEY}&regions=us&markets=h2h,spreads")
        data = response.json()

        if not data:
            return "No NFL odds data found."

        if data != last_odds_data:
            last_odds_data = data  # Update the cache if new data is found.
            embed = discord.Embed(title="NFL Odds", color=discord.Color.green())
            for game in data[:5]:  # Limit to the top 5 games
                home_team = game['home_team']
                away_team = game['away_team']
                odds = game['bookmakers'][0]['markets'][0]['outcomes']
                home_odds = next((o['price'] for o in odds if o['name'] == home_team), 'N/A')
                away_odds = next((o['price'] for o in odds if o['name'] == away_team), 'N/A')
                commence_time = game['commence_time']

                description = f"Odds for {home_team} vs {away_team}\nHome: {home_team} ({home_odds})\nAway: {away_team} ({away_odds})\nGame Time: {commence_time}"
                embed.add_field(name=f"{home_team} vs {away_team}", value=description, inline=False)

            return embed
        else:
            return None  # No new data found.

    except Exception as e:
        return f"Error fetching latest NFL odds: {e}"

async def fetch_latest_nfl_news(ignore_cache=False):
    """Fetch the latest NFL news and compare with the last fetched data, unless ignore_cache is True."""
    global last_news_data
    try:
        response = requests.get(NFL_NEWS_URL)
        data = response.json()
        articles = data.get('articles', [])

        if not articles:
            return "No NFL news found."

        # Check if the articles are different from the last fetched data or if cache should be ignored
        if ignore_cache or articles != last_news_data:
            last_news_data = articles  # Update the cache if new data is found.
            embed = discord.Embed(title="NFL News", color=discord.Color.orange())

            for article in articles[:5]:  # Limit to the top 5 news articles
                title = article.get('headline', 'No title')
                description = article.get('description', 'No description available')
                link = article.get('links', {}).get('web', {}).get('href', 'No link available')

                embed.add_field(name=title, value=f"{description}\n[Read more]({link})", inline=False)

            # Ensure the embed has at least one field before sending
            if len(embed.fields) == 0:
                return "No new NFL news available at the moment."

            return embed
        else:
            return "No new NFL news available at the moment."

    except Exception as e:
        return f"Error fetching latest NFL news: {e}"

async def fetch_latest_nfl_scores():
    """Fetch the latest NFL scores and compare with the last fetched data."""
    global last_scores_data
    try:
        response = requests.get(NFL_SCORES_URL)
        data = response.json()
        games = data.get('events', [])

        if not games:
            return "No NFL games found."

        if games != last_scores_data:
            last_scores_data = games  # Update the cache if new data is found.
            embed = discord.Embed(title="NFL Scores", color=discord.Color.red())
            for game in games[:5]:  # Limit to the top 5 games
                home_team = game['competitions'][0]['competitors'][0]['team']['displayName']
                away_team = game['competitions'][0]['competitors'][1]['team']['displayName']
                home_score = game['competitions'][0]['competitors'][0]['score']
                away_score = game['competitions'][0]['competitors'][1]['score']
                status = game['status']['type']['name']

                description = f"{home_team} vs {away_team}\nScore: {home_score} - {away_score}\nStatus: {status}"
                embed.add_field(name=f"{home_team} vs {away_team}", value=description, inline=False)

            return embed
        else:
            return None  # No new data found.

    except Exception as e:
        return f"Error fetching NFL scores: {e}"

def start_nfl_updates(bot):
    """Start NFL updates with a scheduled task."""

    @tasks.loop(minutes=90)
    async def fetch_nfl_data():
        """Fetch and update NFL data to the specified Discord channels."""
        print("NFL fetch loop is running...")
        try:
            nfl_odds_channel = bot.get_channel(DISCORD_CHANNEL_ID_NFL_ODDS)
            nfl_news_channel = bot.get_channel(DISCORD_CHANNEL_ID_NFL_NEWS)

            odds_embed = await fetch_latest_nfl_odds()
            news_embed = await fetch_latest_nfl_news()
            # Removed automatic scores sending

            # Send odds
            if odds_embed:
                if isinstance(odds_embed, str):
                    odds_embed = discord.Embed(title="Error Fetching NFL Odds", description=odds_embed, color=discord.Color.red())
                await nfl_odds_channel.send(embed=odds_embed)

            # Send news
            if news_embed:
                if isinstance(news_embed, str):
                    news_embed = discord.Embed(title="Error Fetching NFL News", description=news_embed, color=discord.Color.red())
                await nfl_news_channel.send(embed=news_embed)

        except Exception as e:
            print(f"Error fetching NFL data: {e}")

    # Start the loop if it isn't already running
    if not fetch_nfl_data.is_running():
        fetch_nfl_data.start()
        print("NFL updates loop has started.")

async def send_scores_to_channel(channel):
    """Send the latest NFL scores to a specific channel."""
    scores_embed = await fetch_latest_nfl_scores()
    if scores_embed:
        if isinstance(scores_embed, str):
            scores_embed = discord.Embed(title="Error Fetching NFL Scores", description=scores_embed, color=discord.Color.red())
        await channel.send(embed=scores_embed)

