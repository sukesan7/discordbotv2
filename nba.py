import discord
from discord.ext import tasks
import requests
from security import ODDS_API_KEY, DISCORD_CHANNEL_ID_NBA_NEWS, DISCORD_CHANNEL_ID_NBA_ODDS

# --------------------------------------------------------------------------
# ------------------------------ Declarations ------------------------------
# --------------------------------------------------------------------------

NBA_SCORES_URL = "http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
NBA_NEWS_URL = "http://site.api.espn.com/apis/site/v2/sports/basketball/nba/news"
NBA_ODDS_URL = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds"

# Cache variables to store the last fetched data
last_odds_data = None
last_news_data = None

# -----------------------------------------------------------------------
# ------------------------------ Functions ------------------------------
# -----------------------------------------------------------------------

async def fetch_latest_nba_odds():
    """Fetch the latest NBA odds and compare with the last fetched data."""
    global last_odds_data
    try:
        params = {
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "american",
            "apiKey": ODDS_API_KEY
        }
        response = requests.get(NBA_ODDS_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if not data:
            return "No NBA odds data found."

        if data != last_odds_data:
            last_odds_data = data  # Update the cache if new data is found.
            embed = discord.Embed(title="NBA Odds", color=discord.Color.red())

            for game in data[:5]:  # Safely access the first 5 games
                home_team = game.get('home_team')
                away_team = game.get('away_team')
                bookmakers = game.get('bookmakers', [])

                if bookmakers and bookmakers[0].get('markets'):
                    outcomes = bookmakers[0]['markets'][0].get('outcomes', [])
                    home_odds = next((o['price'] for o in outcomes if o['name'] == home_team), 'N/A')
                    away_odds = next((o['price'] for o in outcomes if o['name'] == away_team), 'N/A')
                else:
                    home_odds, away_odds = 'N/A', 'N/A'

                commence_time = game.get('commence_time', 'N/A')

                description = (
                    f"Odds for {home_team} vs {away_team}\n"
                    f"Home: {home_team} ({home_odds})\n"
                    f"Away: {away_team} ({away_odds})\n"
                    f"Game Time: {commence_time}"
                )
                embed.add_field(name=f"{home_team} vs {away_team}", value=description, inline=False)

            return embed
        else:
            return None  # No new data found.

    except Exception as e:
        return f"Error fetching NBA odds: {e}"


async def fetch_latest_nba_news():
    """Fetch the latest NBA news and compare with the last fetched data."""
    global last_news_data
    try:
        response = requests.get(NBA_NEWS_URL)
        data = response.json()
        articles = data.get('articles', [])

        if articles != last_news_data:
            last_news_data = articles  # Update the cache if new data is found.
            embed = discord.Embed(title="NBA News", color=discord.Color.orange())
            for article in articles[:5]:
                title = article.get('headline', 'No title')
                description = article.get('description', 'No description available')
                link = article.get('links', {}).get('web', {}).get('href', 'No link available')

                embed.add_field(name=title, value=f"{description}\n[Read more]({link})", inline=False)

            return embed
        else:
            return None  # No new data found.

    except Exception as e:
        return f"Error fetching NBA news: {e}"

def start_nba_updates(bot):
    @tasks.loop(minutes=360)
    async def fetch_nba_data():
        print("NBA fetch loop is running...")
        try:
            nba_odds_channel = bot.get_channel(DISCORD_CHANNEL_ID_NBA_ODDS)
            nba_news_channel = bot.get_channel(DISCORD_CHANNEL_ID_NBA_NEWS)

            odds_embed = await fetch_latest_nba_odds()
            news_embed = await fetch_latest_nba_news()

            # Only send messages if there is new data
            if odds_embed:
                if isinstance(odds_embed, str):
                    odds_embed = discord.Embed(title="Error Fetching NBA Odds", description=odds_embed, color=discord.Color.red())
                await nba_odds_channel.send(embed=odds_embed)

            if news_embed:
                if isinstance(news_embed, str):
                    news_embed = discord.Embed(title="Error Fetching NBA News", description=news_embed, color=discord.Color.red())
                await nba_news_channel.send(embed=news_embed)

        except Exception as e:
            print(f"Error fetching NBA data: {e}")

    # Start the loop if it isn't already running
    if not fetch_nba_data.is_running():
        fetch_nba_data.start()
        print("NBA updates loop has started.")


async def fetch_latest_nba_scores():
    """Fetch the latest NBA scores from the ESPN API."""
    try:
        response = requests.get(NBA_SCORES_URL)
        response.raise_for_status()
        data = response.json()
        games = data.get('events', [])

        if not games:
            return "No NBA games found."

        embed = discord.Embed(title="NBA Scores", color=discord.Color.blue())
        for game in games[:5]:  # Limit to the top 5 games
            home_team = game['competitions'][0]['competitors'][0]['team']['displayName']
            away_team = game['competitions'][0]['competitors'][1]['team']['displayName']
            home_score = game['competitions'][0]['competitors'][0]['score']
            away_score = game['competitions'][0]['competitors'][1]['score']
            status = game['status']['type']['name']

            description = (
                f"{home_team} vs {away_team}\n"
                f"Score: {home_score} - {away_score}\n"
                f"Status: {status}"
            )
            embed.add_field(name=f"{home_team} vs {away_team}", value=description, inline=False)

        return embed

    except Exception as e:
        return f"Error fetching NBA scores: {e}"


async def send_nba_scores_to_channel(channel):
    """Send the latest NBA scores to a specific channel."""
    scores_embed = await fetch_latest_nba_scores()
    if scores_embed:
        if isinstance(scores_embed, str):
            scores_embed = discord.Embed(
                title="Error Fetching NBA Scores", 
                description=scores_embed, 
                color=discord.Color.red()
            )
        await channel.send(embed=scores_embed)