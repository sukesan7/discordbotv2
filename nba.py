import requests
from bs4 import BeautifulSoup

def get_nba_injury_report():
    try:
        url = "https://www.rotowire.com/basketball/injury-report.php"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the table that holds the injury report
        table = soup.find('table')  # Adjust this if there's a specific class or id for the injury table

        # Check if the table exists
        if table is None:
            return "Error: Could not find the injury report table. The page structure might have changed."

        # Get all rows in the table, skipping the header row
        rows = table.find_all('tr')[1:]

        message = "**NBA Injury Reports:**\n"
        for row in rows:
            cells = row.find_all('td')

            # Extracting details from each cell
            player = cells[0].get_text(strip=True) if len(cells) > 0 else "Unknown"
            team = cells[1].get_text(strip=True) if len(cells) > 1 else "Unknown"
            position = cells[2].get_text(strip=True) if len(cells) > 2 else "Unknown"
            injury = cells[3].get_text(strip=True) if len(cells) > 3 else "Unknown"
            status = cells[4].get_text(strip=True) if len(cells) > 4 else "Unknown"
            return_timeline = cells[5].get_text(strip=True) if len(cells) > 5 else "N/A"

            message += f"{player} ({team}, {position}): {status}, {injury}. Return: {return_timeline}\n"

        return message
    except Exception as e:
        return f"Error fetching NBA injury report: {e}"
