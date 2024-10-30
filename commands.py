import discord
from discord.ext import commands
from discord import app_commands, Color, Embed, Interaction, TextChannel
import yt_dlp
import asyncio
import requests
import datetime
from nba import fetch_latest_nba_odds, fetch_latest_nba_news
from nba import send_nba_scores_to_channel as nba_scores
from nfl import fetch_latest_nfl_odds, fetch_latest_nfl_news
from nfl import send_nfl_scores_to_channel as nfl_scores
import openai
from security import OPENAI_API_KEY, DISCORD_CHANNEL_ID_PICKS
from predictions import generate_predictions_for_today


# --------------------------------------------------------------------------
# ------------------------------ Declarations ------------------------------
# --------------------------------------------------------------------------

# --------------- Setup OpenAI API Key
openai.api_key = OPENAI_API_KEY
PICKS_CHANNEL_NAME = "picks"

# --------------- Define the ESPN URLs for NBA and NFL searching
espn_urls = {
    'nba': 'http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard',
    'nba_teams': 'http://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams',
    'nfl': 'http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard',
    'nfl_teams': 'http://site.api.espn.com/apis/site/v2/sports/football/nfl/teams'
}

# --------------- Settings for the music bot
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -c:a libopus -b:a 128k -application lowdelay'
}
YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'True', 'default_search': 'ytsearch'}

# --------------- Queue for the music bot 
queue = [] 

# ----- Cog for role button
class RoleButton(discord.ui.View):
    def __init__(self, role_id):
        super().__init__(timeout=None)  # No timeout so the button stays active.
        self.role_id = role_id

    @discord.ui.button(label="Notify Me!", style=discord.ButtonStyle.primary)
    async def notify_me_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(self.role_id)

        if not role:
            await interaction.response.send_message("Role not found.", ephemeral=True)
            return

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"Removed {role.name} role.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"Added {role.name} role.", ephemeral=True)


# ----------------------------------------------------------------------------
# ------------------------------ Commands Below ------------------------------
# ----------------------------------------------------------------------------

class SportsBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ask", description="Ask a question to GPT-3 and get a response.")
    async def ask_gpt(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer()
        try:
            response = await openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": question}]
            )
            answer = response['choices'][0]['message']['content']
            embed = discord.Embed(title="GPT Response", description=answer, color=discord.Color.blue())
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Error", 
                description=f"Could not fetch a response: {e}", 
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

    # --------------- Command for serverinfo
    @app_commands.command(name="serverinfo", description="Displays information about the server.")
    async def server_info(self, interaction: discord.Interaction):
        guild = interaction.guild

        embed = discord.Embed(
            title="Server Information",
            description=f"**Server name:** {guild.name}\n**Total members:** {guild.member_count}",
            color=discord.Color.red()
        )
        embed.set_footer(text="Last Call - Sports Bets")

        await interaction.response.send_message(embed=embed)

    # --------------- Command for bot information
    @app_commands.command(name="info", description="Displays information about the bot.")
    async def info(self, interaction: discord.Interaction):
        """Slash command to display bot information."""
        embed = discord.Embed(
            title="Bot Information",
            description="This Discord bot was created by .ss7 for sports betting. It is still under construction.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Last Call - Sports Bets")

        await interaction.response.send_message(embed=embed)

    # --------------- Command for user information
    @app_commands.command(name="userinfo", description="Displays information about a user.")
    async def user_info(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        embed = discord.Embed(title="User Information", color=discord.Color.red())
        embed.add_field(name="User", value=member.name, inline=False)
        embed.add_field(name="Joined at", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
        embed.add_field(name="ID", value=member.id, inline=False)
        embed.set_footer(text="Last Call - Sports Bets")
        await interaction.response.send_message(embed=embed)

    # --------------- Command to play music
    @app_commands.command(name="play", description="Play a song from YouTube.")
    async def play(self, interaction: discord.Interaction, search: str):
        voice_channel = interaction.user.voice.channel if interaction.user.voice else None
        if not voice_channel:
            return await interaction.response.send_message("You are not in a voice channel.")

        if not interaction.guild.voice_client:
            await voice_channel.connect()

        async with interaction.channel.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
                url, title = info['url'], info['title']
                queue.append((url, title))
                embed = discord.Embed(
                    title="Song Added to Queue",
                    description=f"**{title}** added to the queue.",
                    color=discord.Color.red()
                )
                embed.set_footer(text="Last Call - Sports Bets")
                await interaction.response.send_message(embed=embed)

            if not interaction.guild.voice_client.is_playing():
                await self.play_next(interaction)

    async def play_next(self, interaction: discord.Interaction):
        if queue:
            url, title = queue.pop(0)
            try:
                source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
                interaction.guild.voice_client.play(
                    source, 
                    after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(interaction), self.bot.loop)
                )
                embed = discord.Embed(
                    title="Now Playing",
                    description=f"**{title}**",
                    color=discord.Color.red()
                )
                embed.set_footer(text="Last Call - Sports Bets")
                await interaction.channel.send(embed=embed)
            except Exception as e:
                await interaction.channel.send(f"Error playing {title}: {e}")
                await self.play_next(interaction)
        else:
            await interaction.channel.send("The queue is empty.")

    # --------------- Command to skip the track
    @app_commands.command(name="skip", description="Skip the currently playing track.")
    async def skip(self, interaction: discord.Interaction):
        """Skip the currently playing track."""
        voice_client = interaction.guild.voice_client

        if voice_client and voice_client.is_playing():
            voice_client.stop()

            embed = discord.Embed(
                title="Track Skipped",
                description="The track has been skipped.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Last Call - Sports Bets")

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("There is no track currently playing.")

    # --------------- Command to check the queue of songs
    @app_commands.command(name="queue", description="Show the current music queue.")
    async def show_queue(self, interaction: discord.Interaction):
        """Show the current music queue."""
        if not self.queue:
            embed = discord.Embed(
                title="Music Queue",
                description="The queue is empty.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Last Call - Sports Bets")
            return await interaction.response.send_message(embed=embed)

        embed = discord.Embed(title="Music Queue", color=discord.Color.red())
        for idx, (_, title) in enumerate(self.queue, start=1):
            embed.add_field(name=f"{idx}. {title}", value='\u200b', inline=False)

        embed.set_footer(text="Last Call - Sports Bets")
        await interaction.response.send_message(embed=embed)

    # --------------- Command to pause the current song
    @app_commands.command(name="queue", description="Show the current music queue.")
    async def show_queue(self, interaction: discord.Interaction):
        """Show the current music queue."""
        if not self.queue:
            embed = discord.Embed(
                title="Music Queue",
                description="The queue is empty.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Last Call - Sports Bets")
            return await interaction.response.send_message(embed=embed)

        embed = discord.Embed(title="Music Queue", color=discord.Color.red())
        for idx, (_, title) in enumerate(self.queue, start=1):
            embed.add_field(name=f"{idx}. {title}", value='\u200b', inline=False)

        embed.set_footer(text="Last Call - Sports Bets")
        await interaction.response.send_message(embed=embed)

    # --------------- Command to resume the paused song
    @app_commands.command(name="resume", description="Resume the currently paused track.")
    async def resume(self, interaction: discord.Interaction):
        """Resume the currently paused track."""
        embed = discord.Embed(color=discord.Color.red())

        if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
            interaction.guild.voice_client.resume()  # Resumes the paused track
            embed.title = "Track Resumed"
            embed.description = "The paused track has been resumed."
        else:
            embed.title = "No Track Paused"
            embed.description = "There is no track currently paused to resume."

        embed.set_footer(text="Last Call - Sports Bets")
        await interaction.response.send_message(embed=embed)

    # --------------- Command to stop the current song
    @app_commands.command(name="stop", description="Stop the currently playing track.")
    async def stop(self, interaction: discord.Interaction):
        """Stop the currently playing track."""
        embed = discord.Embed(color=discord.Color.red())

        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()  # Stops the current track
            embed.title = "Track Stopped"
            embed.description = "The current track has been stopped."
        else:
            embed.title = "No Track Playing"
            embed.description = "There is no track currently playing."

        embed.set_footer(text="Last Call - Sports Bets")
        await interaction.response.send_message(embed=embed)

    # --------------- Command to disconnect the bot from the voice channel
    @app_commands.command(name="disconnect", description="Disconnect the bot from the voice channel.")
    async def disconnect(self, interaction: discord.Interaction):
        embed = discord.Embed(color=discord.Color.red())

        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            embed.title = "Disconnected"
            embed.description = "The bot has been disconnected from the voice channel."
        else:
            embed.title = "Not Connected"
            embed.description = "The bot is not connected to any voice channel."

        embed.set_footer(text="Last Call - Sports Bets")
        await interaction.response.send_message(embed=embed)

    # --------------- Help command to show all available commands
    @app_commands.command(name="commands", description="Display a list of available commands.")
    async def help_command(self, interaction: discord.Interaction):
        """Display a list of available commands."""
        embed = discord.Embed(
            title="Available Commands",
            description="Here are the commands you can use with this bot:",
            color=discord.Color.red()
        )

        embed.add_field(name="/serverinfo", value="Displays information about the server.", inline=False)
        embed.add_field(name="/userinfo <user>", value="Displays information about a user.", inline=False)
        embed.add_field(name="/play <song name or URL>", value="Plays the specified song in the voice channel.", inline=False)
        embed.add_field(name="/stop", value="Stops the currently playing track.", inline=False)
        embed.add_field(name="/pause", value="Pauses the currently playing track.", inline=False)
        embed.add_field(name="/resume", value="Resumes the currently paused track.", inline=False)
        embed.add_field(name="/queue", value="Shows the current music queue.", inline=False)
        embed.add_field(name="/skip", value="Skips the currently playing track.", inline=False)
        embed.add_field(name="/matches <YYYY-MM-DD>", value="Finds games played for both NFL and NBA on a specific date.", inline=False)
        embed.add_field(name="/search <sport> <team name>", value="Searches for a specific team to display information.", inline=False)
        embed.add_field(name="/odds <sport>", value="Shows the current odds for that sport.", inline=False)
        embed.add_field(name="/news <sport>", value="Shows the current news for that sport.", inline=False)
        embed.add_field(name="/scores", value="Will show the Live and Final scores for the NFL.", inline=False)

        embed.set_footer(text="Last Call - Sports Bets")
        await interaction.response.send_message(embed=embed)


    # ------------------------------------------------------------------------------------------------------------------------
    # --------------------------------------------- Commands for Search and Matches Below ------------------------------------
    # ------------------------------------------------------------------------------------------------------------------------

    # --------------- Command for finding matches provided the date
    @app_commands.command(name="matches", description="Fetch NBA and NFL matches for a given date.")
    @app_commands.describe(date="The date in YYYY-MM-DD format")
    async def matches(self, interaction: discord.Interaction, date: str):
        """
        Fetches matches for both NBA and NFL for a given date.
        """
        # Validate the date format
        try:
            datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            await interaction.response.send_message("Invalid date format. Please use YYYY-MM-DD.", ephemeral=True)
            return

        # Embed setup
        embed = discord.Embed(
            title=f"Matches for {date}",
            description="Here are the matches for NBA and NFL on the selected date:",
            color=discord.Color.red()
        )
        embed.set_footer(text="Last Call - Sports Bets")

        # Fetch NBA matches
        nba_url = f"http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date.replace('-', '')}"
        try:
            nba_response = requests.get(nba_url).json()
            nba_scores = nba_response.get('events', [])

            if nba_scores:
                nba_matches = ""
                for game in nba_scores:
                    competition = game.get('competitions', [])[0]
                    home_team = competition['competitors'][0]['team']['displayName']
                    away_team = competition['competitors'][1]['team']['displayName']
                    home_score = competition['competitors'][0]['score']
                    away_score = competition['competitors'][1]['score']
                    status = competition.get('status', {}).get('type', {}).get('description', 'Scheduled')
                    nba_matches += f"**{home_team}** {home_score} vs **{away_team}** {away_score} ({status})\n"
                embed.add_field(name="NBA", value=nba_matches, inline=False)
            else:
                embed.add_field(name="NBA", value="No NBA matches found for this date.", inline=False)

        except Exception as e:
            await interaction.response.send_message(f"Error fetching matches for NBA: {e}", ephemeral=True)
            return

        # Fetch NFL matches
        nfl_url = f"http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={date.replace('-', '')}"
        try:
            nfl_response = requests.get(nfl_url).json()
            nfl_scores = nfl_response.get('events', [])

            if nfl_scores:
                nfl_matches = ""
                for game in nfl_scores:
                    competition = game.get('competitions', [])[0]
                    home_team = competition['competitors'][0]['team']['displayName']
                    away_team = competition['competitors'][1]['team']['displayName']
                    home_score = competition['competitors'][0]['score']
                    away_score = competition['competitors'][1]['score']
                    status = competition.get('status', {}).get('type', {}).get('description', 'Scheduled')
                    nfl_matches += f"**{home_team}** {home_score} vs **{away_team}** {away_score} ({status})\n"
                embed.add_field(name="NFL", value=nfl_matches, inline=False)
            else:
                embed.add_field(name="NFL", value="No NFL matches found for this date.", inline=False)

        except Exception as e:
            await interaction.response.send_message(f"Error fetching matches for NFL: {e}", ephemeral=True)
            return

        await interaction.response.send_message(embed=embed)

    # --------------- Command to search through available sports and teams for information
    @app_commands.command(name="search", description="Search for a team in NBA or NFL.")
    @app_commands.describe(sport="The sport to search (NBA or NFL)", team_name="The team name to search")
    async def search(self, interaction: discord.Interaction, sport: str, team_name: str = None):
        """Search for a specific team or list available teams."""
        sport = sport.lower()
        if sport not in ["nba", "nfl"]:
            await interaction.response.send_message("Invalid sport. Please use 'NBA' or 'NFL'.", ephemeral=True)
            return

        if not team_name:
            await self.show_available_teams(interaction, sport)
            return

        if sport == "nba":
            await self.search_nba_team(interaction, team_name)
        elif sport == "nfl":
            await self.search_nfl_team(interaction, team_name)

    async def show_available_teams(self, interaction: discord.Interaction, sport: str):
        """Show available teams for NBA or NFL."""
        url = (
            "http://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"
            if sport == "nba" else
            "http://site.api.espn.com/apis/site/v2/sports/football/nfl/teams"
        )
        response = requests.get(url).json()
        teams = response['sports'][0]['leagues'][0]['teams']
        team_names = [team['team']['displayName'] for team in teams]
        description = "\n".join(team_names) if team_names else "No teams found."

        embed = discord.Embed(
            title=f"Available {sport.upper()} Teams",
            description=description,
            color=discord.Color.blue() if sport == "nba" else discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    async def search_nba_team(self, interaction: discord.Interaction, team_name: str):
        """Search and display NBA team information."""
        await self._search_team(interaction, team_name, "nba")

    async def search_nfl_team(self, interaction: discord.Interaction, team_name: str):
        """Search and display NFL team information."""
        await self._search_team(interaction, team_name, "nfl")

    async def _search_team(self, interaction: discord.Interaction, team_name: str, sport: str):
        """Fetch and display team details."""
        url = (
            "http://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"
            if sport == "nba" else
            "http://site.api.espn.com/apis/site/v2/sports/football/nfl/teams"
        )
        response = requests.get(url).json()
        teams = response['sports'][0]['leagues'][0]['teams']

        team_info = next(
            (team['team'] for team in teams if team_name.lower() in team['team']['displayName'].lower()), None
        )

        if not team_info:
            await interaction.response.send_message(f"No team found with the name: {team_name}", ephemeral=True)
            return

        # Fetch scoreboard data
        scoreboard_url = (
            "http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
            if sport == "nba" else
            "http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
        )
        scores_response = requests.get(scoreboard_url).json()

        past_games = []
        upcoming_match = None

        for game in scores_response.get('events', []):
            home_team = game['competitions'][0]['competitors'][0]
            away_team = game['competitions'][0]['competitors'][1]
            if home_team['team']['id'] == team_info['id'] or away_team['team']['id'] == team_info['id']:
                if game['status']['type']['completed']:
                    past_games.append(
                        f"{home_team['team']['displayName']} {home_team['score']} - {away_team['team']['displayName']} {away_team['score']}"
                    )
                else:
                    upcoming_match = f"{home_team['team']['displayName']} vs {away_team['team']['displayName']}"

        embed = discord.Embed(
            title=f"{team_info['displayName']} - {team_info['location']}",
            color=discord.Color.red()
        )

        embed.add_field(
            name="Recent Games",
            value="\n".join(past_games) if past_games else "No past games available.",
            inline=False
        )
        embed.add_field(
            name="Next Match",
            value=upcoming_match if upcoming_match else "No upcoming matches.",
            inline=False
        )

        await interaction.response.send_message(embed=embed)


    # ------------------------------------------------------------------------------------------------------------------------
    # --------------------------------------------- Odds and News Commands Below ---------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------------

    # --------------- Command to find the current odds for a desired sport
    @app_commands.command(name="odds", description="Fetch the latest odds for NBA or NFL.")
    @app_commands.describe(sport="Select the sport (NBA or NFL) to view the latest odds.")
    async def odds(self, interaction: discord.Interaction, sport: str):
        """Responds with the latest odds for the given sport."""
        sport = sport.lower()

        if sport not in ["nba", "nfl"]:
            embed = discord.Embed(
                title="Invalid Sport",
                description="Please use a valid sport: `nba` or `nfl`.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Fetch the odds data
        odds_embed = None
        if sport == "nba":
            odds_embed = await fetch_latest_nba_odds()
        elif sport == "nfl":
            odds_embed = await fetch_latest_nfl_odds()

        # Handle errors from the odds function
        if isinstance(odds_embed, str):
            odds_embed = discord.Embed(
                title=f"Error Fetching {sport.upper()} Odds",
                description=odds_embed,
                color=discord.Color.red()
            )

        # Send the odds embed to the user
        await interaction.response.send_message(embed=odds_embed)

    # --------------- Command to find the scores
    @app_commands.command(name="scores", description="Fetch and display the latest NBA and NFL scores.")
    async def scores(self, interaction: Interaction):
        """Fetch and send the latest NBA and NFL scores."""
        await interaction.response.defer()

        try:
            # Fetch NBA and NFL scores using the helper functions.
            nba_embed = await nba_scores(interaction.channel)
            nfl_embed = await nfl_scores(interaction.channel)

            # Send NBA scores if available.
            if nba_embed:
                await interaction.followup.send(embed=nba_embed)

            # Send NFL scores if available.
            if nfl_embed:
                await interaction.followup.send(embed=nfl_embed)

        except Exception as e:
            # Handle errors and provide feedback to the user.
            await interaction.followup.send(f"Error fetching scores: {str(e)}", ephemeral=True)


    # -------------------------------------------------------------------------------------------------------------
    # --------------------------------------------- Prediction Models ---------------------------------------------
    # -------------------------------------------------------------------------------------------------------------

    # --------------- Command for finding the news of a desired sport
    @app_commands.command(name="news", description="Fetch the latest news for a given sport.")
    @app_commands.describe(sport="The sport to fetch news for (nba or nfl).")
    async def news(self, interaction: discord.Interaction, sport: str):
        """Fetch the latest news for the given sport."""
        await interaction.response.defer()

        sport = sport.lower()

        if sport == "nba":
            news_embed = await fetch_latest_nba_news()
        elif sport == "nfl":
            news_embed = await fetch_latest_nfl_news()
        else:
            embed = discord.Embed(
                title="Invalid Sport",
                description="Please use 'nba' or 'nfl'.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        if isinstance(news_embed, str):
            news_embed = discord.Embed(
                title=f"Error Fetching {sport.upper()} News",
                description=news_embed,
                color=discord.Color.red()
            )

        await interaction.followup.send(embed=news_embed)

    # --------------- Command for predictions
    @app_commands.command(name="predict", description="Get today's NBA predictions.")
    async def predict(self, interaction: discord.Interaction):
        """Fetch and send NBA predictions for today."""
        await interaction.response.defer()  # Defer the response to handle delays

        try:
            # Generate predictions
            results = generate_predictions_for_today()
            nba_results = results.get("nba", "No NBA games today.")

            # Format and send the response
            embed = self.format_prediction_message("NBA", nba_results)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            # Handle any exceptions by sending an error message
            await interaction.followup.send(f"Error fetching predictions: {str(e)}", ephemeral=True)

    def format_prediction_message(self, sport, results):
        """Format the prediction results into a Discord embed."""
        embed = discord.Embed(title=f"{sport} Predictions for Today", color=discord.Color.blue())

        if isinstance(results, str):
            embed.description = results  # Display the error or message if no games are available
        else:
            # Loop through the predictions and add fields to the embed
            for result in results:
                home_team = result.get('HomeTeam')
                away_team = result.get('AwayTeam')
                moneyline_prediction = result.get('MoneylinePrediction', 'N/A')
                point_spread = result.get('PointSpread', 'N/A')

                embed.add_field(
                    name=f"{home_team} vs {away_team}",
                    value=(
                        f"**Moneyline:** {moneyline_prediction}\n"
                        f"**Point Spread:** {point_spread}"
                    ),
                    inline=False
                )

        embed.set_footer(text="These values are not real data. Showcase only.")
        return embed

    # --------------- Command for sending embedded messages):
    @app_commands.command(
        name="embed", 
        description="Create a custom embed message with a selectable color."
    )
    @app_commands.choices(
        color=[
            app_commands.Choice(name="Blue", value=0x3498db),
            app_commands.Choice(name="Red", value=0xe74c3c),
            app_commands.Choice(name="Green", value=0x2ecc71),
            app_commands.Choice(name="Yellow", value=0xf1c40f),
            app_commands.Choice(name="Purple", value=0x9b59b6),
            app_commands.Choice(name="Orange", value=0xe67e22)
        ]
    )
    async def embed(
        self, 
        interaction: Interaction, 
        title: str, 
        description: str, 
        channel: TextChannel, 
        color: app_commands.Choice[int]
    ):
        """Slash command to create a custom embed message with multi-line input."""
        await interaction.response.defer()

        # Replace "\n" with actual newlines to support multi-line input.
        description = description.replace("\\n", "\n")

        embed = Embed(
            title=title, 
            description=description, 
            color=Color(color.value)
        )
        embed.set_footer(text="Last Call - Sports Bets")

        # Send the embed to the specified channel
        await channel.send(embed=embed)
        await interaction.followup.send(f"Embed sent to {channel.mention}!")

    # --------------- Command for custom picks to a specific channel
    @app_commands.command(name="picks", description="Create betting picks for NBA or NFL.")
    async def picks(
        self, 
        interaction: discord.Interaction,
        sport: str,  # NBA or NFL
        bet_type: str,  # Parlay or Singles
        team_matchup: str,  # Team A vs Team B
        player1_name: str, 
        player1_points: int = None,
        player1_rebounds: int = None,
        player1_assists: int = None,
        player2_name: str = None,
        player2_points: int = None,
        player2_rebounds: int = None,
        player2_assists: int = None,
        player3_name: str = None,
        player3_points: int = None,
        player3_rebounds: int = None,
        player3_assists: int = None,
    ):
        """Create and post custom sports betting picks."""
        await interaction.response.defer()

        # Find the channel named 'picks'
        picks_channel = discord.utils.get(interaction.guild.text_channels, name=PICKS_CHANNEL_NAME)
        if not picks_channel:
            await interaction.followup.send(f"Channel named '{PICKS_CHANNEL_NAME}' not found.", ephemeral=True)
            return

        # Build the embed
        embed = discord.Embed(
            title=f"{sport.upper()} {bet_type.capitalize()}",
            description=f"**{team_matchup}**",
            color=discord.Color.blue()
        )

        # Add players and their stats if provided
        def format_player(player_name, points, rebounds, assists):
            """Helper to format player information."""
            stats = []
            if points is not None: stats.append(f"{points}+ Points")
            if rebounds is not None: stats.append(f"{rebounds}+ Rebounds")
            if assists is not None: stats.append(f"{assists}+ Assists")
            return f"{player_name}: {', '.join(stats)}" if stats else None

        player1_info = format_player(player1_name, player1_points, player1_rebounds, player1_assists)
        player2_info = format_player(player2_name, player2_points, player2_rebounds, player2_assists)
        player3_info = format_player(player3_name, player3_points, player3_rebounds, player3_assists)

        # Add player information to the embed
        for player_info in [player1_info, player2_info, player3_info]:
            if player_info:
                embed.add_field(name="Player", value=player_info, inline=False)

        # Send the embed to the picks channel
        await picks_channel.send(embed=embed)
        await interaction.followup.send(f"Picks sent to {picks_channel.mention}!", ephemeral=True)

    # --------------- Command for custom react role message
    @app_commands.command(name="react", description="Send an embed with a button to assign a role.")
    @app_commands.describe(channel="Select the channel where the message will be sent.")
    async def react(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Send a message with a role assignment button to a specific channel."""
        await interaction.response.defer()

        embed = discord.Embed(
            title="React Roles",
            description="Click the **Notify Me!** button below to receive notifications about our bets!",
            color=discord.Color.red()
        )
        embed.set_footer(text="Last Call - Sports Bets")

        role_id = 1301289697712013404  # Replace with your actual role ID.
        view = RoleButton(role_id)

        await channel.send(embed=embed, view=view)
        await interaction.followup.send(f"Message sent to {channel.mention}!", ephemeral=True)


# add the cog to the bot
async def setup(bot: commands.Bot):
    await bot.add_cog(SportsBot(bot))