from discord.ext import commands, tasks
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import time

class NBA:
    def __init__(self, bot):
        self.bot = bot
        self.injury_url = "https://www.rotowire.com/basketball/injury-report.php"
        self.news_url = "https://www.rotowire.com/basketball/news/"  # Replace with actual news URL
        self.channel_id_injuries = 123456789012345678  # Replace with your channel ID for NBA injuries
        self.channel_id_news = 987654321098765432  # Replace with your channel ID for NBA news

    @commands.Cog.listener()
    async def on_ready(self):
        self.driver = webdriver.Chrome(ChromeDriverManager().install())
        self.driver.get(self.injury_url)
        self.last_injury_data = self.get_injury_data()
        print(f"NBA: Connected and ready to scrape!")

    def get_injury_data(self):
        time.sleep(5)  # Adjust wait time as needed
        self.driver.get(self.injury_url)
        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        # Assuming the injury data is within a table with a specific class
        injury_table = soup.find("table", class_="injury-table")  # Replace with the actual class name

        if injury_table:
            injury_rows = injury_table.find_all("tr")
            injury_data = []
            for row in injury_rows:
                cells = row.find_all("td")
                if len(cells) >= 3:  # Ensure there are at least 3 columns
                    injury_data.append(f"{cells[0].text.strip()} - {cells[1].text.strip()} - {cells[2].text.strip()}")
            return injury_data
        else:
            return []  # If the table is not found, return an empty list

    async def check_for_updates(self):
        current_data = self.get_injury_data()
        if current_data != self.last_injury_data:
            self.last_injury_data = current_data
            channel = self.bot.get_channel(self.channel_id_injuries)
            await channel.send("**New NBA injuries reported!**")
            for injury in current_data:
                await channel.send(injury)
        # Add logic for scraping and posting NBA news (similar to injury data)

    @tasks.loop(minutes=10)  # Adjust scraping interval as needed
    async def scrape_nba(self):
        await self.check_for_updates()

    async def cog_load(self):
        self.scrape_nba.start()

    async def cog_unload(self):
        self.scrape_nba.cancel()
        self.driver.quit()

setup = NBA