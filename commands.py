import discord
from discord import app_commands

class MiscCommands(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='serverinfo', description="Displays information about the server.")
    async def server_info(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild:
            embed = discord.Embed(
                title=f"{guild.name} Info",
                description=f"ID: {guild.id}\nMembers: {guild.member_count}",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("This command can only be used in a server.")

    @app_commands.command(name='userinfo', description="Displays information about the user.")
    async def user_info(self, interaction: discord.Interaction):
        user = interaction.user
        embed = discord.Embed(
            title=f"{user.name}'s Info",
            description=f"ID: {user.id}\nUsername: {user.name}\nDiscriminator: {user.discriminator}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(MiscCommands(bot))
