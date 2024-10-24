import discord
from discord.ext import commands
import yt_dlp
import asyncio
import requests
import datetime

# --------------- Define the ESPN URLs for NBA and NFL searching
espn_urls = {
    'nba': 'http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard',
    'nba_teams': 'http://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams',
    'nfl': 'http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard',
    'nfl_teams': 'http://site.api.espn.com/apis/site/v2/sports/football/nfl/teams'
}

# Music bot settings
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -c:a libopus -b:a 128k -application lowdelay'
}
YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'True', 'default_search': 'ytsearch'}

queue = [] #list to hold songs

def setup_commands(bot): #setup the commands

    # --------------- Server info command
    @bot.command(name='serverinfo')
    async def server_info(ctx):
        guild = ctx.guild
        await ctx.send(f'Server name: {guild.name}\nTotal members: {guild.member_count}')

    # --------------- Info command
    @bot.command(name='info')
    async def server_info(ctx):
        guild = ctx.guild
        await ctx.send(f'This discord bot was created by .ss7 for sportsbetting. It is still under construction')

    # --------------- User info command
    @bot.command(name='userinfo')
    async def user_info(ctx, member: discord.Member = None):
        member = member or ctx.author
        await ctx.send(f'User: {member.name}\nJoined at: {member.joined_at}\nID: {member.id}')

    # --------------- Play music command
    @bot.command(name='play')
    async def play(ctx, *, search):
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            return await ctx.send("User is not in a voice channel.")
        
        # Connect to the voice channel if not already connected
        if not ctx.voice_client:
            await voice_channel.connect()
        
        # Download and queue the song
        async with ctx.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)
                if 'entries' in info:
                    info = info['entries'][0]  # Take the first result from the search
                url = info['url']
                title = info['title']
                queue.append((url, title))
                await ctx.send(f'Added to queue: **{title}**')

        # Play the song if nothing else is currently playing
        if not ctx.voice_client.is_playing():
            await play_next(ctx)

    # --------------- Function to play the next song in the queue
    async def play_next(ctx):
        if queue:
            url, title = queue.pop(0)
            try:
                source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
                ctx.voice_client.play(
                    source, 
                    after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
                )
                await ctx.send(f'Now playing: **{title}**')
            except Exception as e:
                await ctx.send(f"An error occurred while playing {title}: {e}")
                print(f"Error: {e}")
                # Attempt to play the next song if an error occurs
                await play_next(ctx)
        else:
            await ctx.send("The queue is empty.")

    # --------------- Skip command to skip the current track
    @bot.command(name='skip')
    async def skip(ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("The track has been skipped.")

    # --------------- Queue command to display the list of queued songs
    @bot.command(name='queue')
    async def show_queue(ctx):
        if not queue:
            return await ctx.send("The queue is empty.")

        embed = discord.Embed(title="Music Queue", color=discord.Color.red())
        for idx, (_, title) in enumerate(queue, start=1):
            embed.add_field(name=f"{idx}. {title}", value='\u200b', inline=False)
        
        await ctx.send(embed=embed)

    # --------------- Pause command to pause the current track
    @bot.command(name='pause')
    async def pause(ctx):
        """Pause the currently playing track."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()  # Pauses the current track
            await ctx.send("The current track has been paused.")
        else:
            await ctx.send("There is no track currently playing to pause.")

    # --------------- Resume command to resume the current track
    @bot.command(name='resume')
    async def resume(ctx):
        """Resume the currently paused track."""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()  # Resumes the paused track
            await ctx.send("The paused track has been resumed.")
        else:
            await ctx.send("There is no track currently paused to resume.")


    # --------------- Stop command to stop the current track
    @bot.command(name='stop')
    async def stop(ctx):
        """Stop the currently playing track."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()  # Stops the current track
            await ctx.send("The current track has been stopped.")
        else:
            await ctx.send("There is no track currently playing.")

    # --------------- Disconnect command to make the bot leave the voice channel
    @bot.command(name='disconnect')
    async def disconnect(ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("Disconnected from the voice channel.")
        else:
            await ctx.send("The bot is not connected to any voice channel.")

    # --------------- Help command to show all available commands
    bot.remove_command('commands')  # Remove the default help command
    @bot.command(name='commands')
    async def help_command(ctx):
        """Display a list of available commands."""
        embed = discord.Embed(
            title="Available Commands",
            description="Here are the commands you can use with this bot:",
            color=discord.Color.red()
        )
        
        embed.add_field(name=".serverinfo", value="Displays information about the server.", inline=False)
        embed.add_field(name=".userinfo [user]", value="Displays information about a user.", inline=False)
        embed.add_field(name=".play [song name or URL]", value="Plays the specified song in the voice channel.", inline=False)
        embed.add_field(name=".stop", value="Stops the currently playing track.", inline=False)
        embed.add_field(name=".pause", value="Pauses the currently playing track.", inline=False)
        embed.add_field(name=".resume", value="Resumes the currently paused track.", inline=False)
        embed.add_field(name=".queue", value="Shows the current music queue.", inline=False)
        embed.add_field(name=".skip", value="Skips the currently playing track.", inline=False)
        embed.add_field(name=".matches [YYYY-MM-DD]", value="Finds games played for both NFL and NBA on a specific date.", inline=False)
        embed.add_field(name=".search [sport] [team name]", value="Searches for a specific team to display information.", inline=False)

        await ctx.send(embed=embed)

    # --------------- Matches command to display games for both NBA and NFL on a given date
    @bot.command(name='matches')
    async def matches(ctx, date: str = None):
        """
        Fetches matches for both NBA and NFL for a given date.
        If no date is provided, prompts the user for the correct format.
        """
        if date is None:
            await ctx.send("Please provide a date in the correct format: YYYY-MM-DD.")
            return

        # Validate the date format
        try:
            datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            await ctx.send("Invalid date format. Please use YYYY-MM-DD.")
            return

        # Embed setup
        embed = discord.Embed(
            title=f"Matches for {date}",
            description="Here are the matches for NBA and NFL on the selected date:",
            color=discord.Color.red()
        )
        embed.set_footer(text="Provided by ESPN API")

        # NBA matches
        nba_url = f"http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date.replace('-', '')}"
        try:
            nba_response = requests.get(nba_url).json()
            nba_scores = nba_response.get('events', [])

            if nba_scores:
                nba_matches = ""
                for game in nba_scores:
                    competitions = game.get('competitions', [])
                    if competitions:
                        competition = competitions[0]
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
            await ctx.send(f"Error fetching matches for NBA: {e}")
            return

        # NFL matches
        nfl_url = f"http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={date.replace('-', '')}"
        try:
            nfl_response = requests.get(nfl_url).json()
            nfl_scores = nfl_response.get('events', [])

            if nfl_scores:
                nfl_matches = ""
                for game in nfl_scores:
                    competitions = game.get('competitions', [])
                    if competitions:
                        competition = competitions[0]
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
            await ctx.send(f"Error fetching matches for NFL: {e}")
            return

        # Send the embed message
        await ctx.send(embed=embed)



    # --------------- Search command to fetch and display information about a specific team
    @bot.command()
    async def search(ctx, sport: str = None, *, team_name: str = None):
        # Show available sports if no sport is provided
        if sport is None:
            await ctx.send(
                embed=discord.Embed(
                    title="Available Sports",
                    description="To search for a team, use the format:\n"
                                "`/search <sport> <team_name>`\n\n"
                                "Available Sports:\n"
                                "- NBA\n"
                                "- NFL",
                    color=discord.Color.red()
                )
            )
            return

        # Validate sport input
        if sport.lower() not in ["nba", "nfl"]:
            await ctx.send("Invalid sport. Please use 'NBA' or 'NFL'.")
            return

        # Show available teams if sport is provided but team name is missing
        if team_name is None:
            await show_available_teams(ctx, sport.lower())
            return

        # If a team name is provided, fetch the team's information
        if sport.lower() == "nba":
            await search_nba_team(ctx, team_name.lower())
        elif sport.lower() == "nfl":
            await search_nfl_team(ctx, team_name.lower())

    async def show_available_teams(ctx, sport):
        if sport == "nba":
            # Fetch NBA teams
            teams_response = requests.get("http://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams")
            teams_data = teams_response.json()
            teams_list = [team['team']['displayName'].split()[-1].lower() for team in teams_data['sports'][0]['leagues'][0]['teams']]
            teams_string = "\n".join(teams_list)

            await ctx.send(
                embed=discord.Embed(
                    title="Available NBA Teams",
                    description=teams_string if teams_string else "No teams found.",
                    color=discord.Color.blue()
                )
            )

        elif sport == "nfl":
            # Fetch NFL teams
            teams_response = requests.get("http://site.api.espn.com/apis/site/v2/sports/football/nfl/teams")
            teams_data = teams_response.json()
            teams_list = [team['team']['displayName'].split()[-1].lower() for team in teams_data['sports'][0]['leagues'][0]['teams']]
            teams_string = "\n".join(teams_list)

            await ctx.send(
                embed=discord.Embed(
                    title="Available NFL Teams",
                    description=teams_string if teams_string else "No teams found.",
                    color=discord.Color.green()
                )
            )

    async def search_nba_team(ctx, team_name):
        # Fetch NBA team data
        teams_response = requests.get("http://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams")
        teams_data = teams_response.json()
        
        # Find the team
        team_info = None
        teams_list = teams_data['sports'][0]['leagues'][0]['teams']
        for team in teams_list:
            if team['team']['displayName'].lower() == team_name.lower() or team_name.lower() in team['team']['displayName'].lower():
                team_info = team['team']
                break

        if not team_info:
            await ctx.send(f"No team found with the name: {team_name}")
            return

        # Fetch the NBA scoreboard data
        scores_response = requests.get("http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard")
        scores_data = scores_response.json()

        # Initialize lists for past games and upcoming match
        past_games = []
        upcoming_match = None

        # Iterate through games in the scoreboard
        for game in scores_data.get('events', []):
            home_team = game['competitions'][0]['competitors'][0]
            away_team = game['competitions'][0]['competitors'][1]
            if home_team['team']['id'] == team_info['id'] or away_team['team']['id'] == team_info['id']:
                if game['status']['type']['completed']:
                    past_games.append(f"{home_team['team']['displayName']} {home_team['score']} - {away_team['team']['displayName']} {away_team['score']}")
                else:
                    upcoming_match = f"{home_team['team']['displayName']} vs {away_team['team']['displayName']}"

        # Create the embed message
        embed = discord.Embed(title=f"{team_info['displayName']} - {team_info['location']}", color=discord.Color.red())

        # Add past games to the embed
        if past_games:
            games_summary = "\n".join(past_games)
        else:
            games_summary = "No past games available."

        embed.add_field(name="Recent Games", value=games_summary, inline=False)
        
        # Next match info
        if upcoming_match:
            embed.add_field(name="Next Match", value=upcoming_match, inline=False)
        else:
            embed.add_field(name="Next Match", value="No upcoming matches", inline=False)

        await ctx.send(embed=embed)

    async def search_nfl_team(ctx, team_name):
        # Fetch NFL team data
        teams_response = requests.get("http://site.api.espn.com/apis/site/v2/sports/football/nfl/teams")
        teams_data = teams_response.json()
        
        # Find the team
        team_info = None
        teams_list = teams_data['sports'][0]['leagues'][0]['teams']
        for team in teams_list:
            if team['team']['displayName'].lower() == team_name.lower() or team_name.lower() in team['team']['displayName'].lower():
                team_info = team['team']
                break

        if not team_info:
            await ctx.send(f"No team found with the name: {team_name}")
            return

        # Fetch the NFL scoreboard data
        scores_response = requests.get("http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard")
        scores_data = scores_response.json()

        # Initialize lists for past games and upcoming match
        past_games = []
        upcoming_match = None

        # Iterate through games in the scoreboard
        for game in scores_data.get('events', []):
            home_team = game['competitions'][0]['competitors'][0]
            away_team = game['competitions'][0]['competitors'][1]
            if home_team['team']['id'] == team_info['id'] or away_team['team']['id'] == team_info['id']:
                if game['status']['type']['completed']:
                    past_games.append(f"{home_team['team']['displayName']} {home_team['score']} - {away_team['team']['displayName']} {away_team['score']}")
                else:
                    upcoming_match = f"{home_team['team']['displayName']} vs {away_team['team']['displayName']}"

        # Create the embed message
        embed = discord.Embed(title=f"{team_info['displayName']} - {team_info['location']}", color=discord.Color.red())

        # Add past games to the embed
        if past_games:
            games_summary = "\n".join(past_games)
        else:
            games_summary = "No past games available."

        embed.add_field(name="Recent Games", value=games_summary, inline=False)
        
        # Next match info
        if upcoming_match:
            embed.add_field(name="Next Match", value=upcoming_match, inline=False)
        else:
            embed.add_field(name="Next Match", value="No upcoming matches", inline=False)

        await ctx.send(embed=embed)

    # can add future commands below in same format
  

