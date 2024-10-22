import discord
from discord import app_commands

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
    
    async def setup_hook(self):
        await self.tree.sync()

client = MyClient()

# Example command to get server information
@client.tree.command(name="serverinfo", description="Displays information about the server.")
async def server_info(interaction: discord.Interaction):
    server = interaction.guild
    message = f"Server Name: {server.name}\nTotal Members: {server.member_count}"
    await interaction.response.send_message(message)

# Example command to send an embedded message
@client.tree.command(name="embed", description="Sends an embedded message.")
async def send_embed(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Example Embed",
        description="This is an embedded message.",
        color=0x3498db
    )
    embed.set_footer(text="Powered by discord.py")
    await interaction.response.send_message(embed=embed)

# Additional commands can be added here...

# create the following:
# - new file for channel ids
# - nfl injury reports
# - nfl / nba news reports
# - soccer injury reports + news reports
# - find host for discord bot
# - test

