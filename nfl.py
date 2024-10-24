from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_nfl_injury_report():
    try:
        # Set up Selenium WebDriver (use the path to your driver if not in PATH)
        driver = webdriver.Chrome()  # or webdriver.Firefox() if using Firefox
        driver.get("https://www.rotowire.com/football/injury-report.php")

        # Wait for the table to load (adjust the timeout as needed)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
        )

        # Find the table containing the injury report
        table = driver.find_element(By.CSS_SELECTOR, "table")
        rows = table.find_elements(By.CSS_SELECTOR, "tr")[1:]  # Skip the header row

        message = "**NFL Injury Reports:**\n"
        for row in rows:
            cells = row.find_elements(By.CSS_SELECTOR, "td")
            player = cells[0].text.strip() if len(cells) > 0 else "Unknown"
            team = cells[1].text.strip() if len(cells) > 1 else "Unknown"
            position = cells[2].text.strip() if len(cells) > 2 else "Unknown"
            injury = cells[3].text.strip() if len(cells) > 3 else "Unknown"
            status = cells[4].text.strip() if len(cells) > 4 else "Unknown"
            return_timeline = cells[5].text.strip() if len(cells) > 5 else "N/A"

            message += f"{player} ({team}, {position}): {status}, {injury}. Return: {return_timeline}\n"

        driver.quit()
        return message
    except Exception as e:
        driver.quit()
        return f"Error fetching NFL injury report: {e}"
