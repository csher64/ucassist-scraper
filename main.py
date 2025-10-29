"""Utilities for scraping UC Assist service listings with Selenium."""

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import chromedriver_autoinstaller
import json
import time


def get_driver() -> webdriver:
    """Configure and return a Selenium WebDriver instance."""
    chromedriver_autoinstaller.install()
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--headless=new")
    return webdriver.Chrome(options=options)


def get_service_links(driver: webdriver) -> list[WebElement]:
    """Return all visible 'View Details' links on the current search results page."""
    service_links = []
    while not service_links:
        for link in driver.find_elements(By.XPATH, "//a"):
            if link.get_attribute("innerText") == "View Details":
                service_links.append(link)
    return service_links


def extract_service_data(driver: webdriver, service_link: WebElement) -> dict:
    """Click a service link and collect key/value data from the details view."""
    service_link.click()

    keys = []
    while not keys:
        for key in driver.find_elements(
            By.XPATH, "//div[contains(@class, 'cbFormLabelCell')]"
        ):
            keys.append(key.get_attribute("innerText"))

    values = []
    while not values:
        for element in driver.find_elements(
            By.XPATH, "//*[contains(@class, 'cbFormDataCell')]"
        ):
            img = element.find_elements(By.TAG_NAME, "img")
            if not img:
                innerText = element.get_attribute("innerText")
                if "\n" in innerText:
                    innerText = innerText.split("\n")
                values.append(innerText)
            else:
                values.append(img[0].get_attribute("src"))

    back_button = driver.find_element(
        By.XPATH, "//input[contains(@class, 'cbBackButton')]"
    )
    back_button.click()

    return dict(zip(keys, values))


def scrape_page(driver: webdriver, page_number: int) -> list[dict]:
    """Scrape all services on the current page, returning their detail dictionaries."""
    service_links = get_service_links(driver=driver)

    data = []
    for i in range(0, len(service_links)):
        print(
            f"\r\033[34mScraping page {page_number}, service {i + 1}... \033[0m", end=""
        )
        while True:
            try:
                data.append(
                    extract_service_data(
                        driver=driver, service_link=get_service_links(driver=driver)[i]
                    )
                )
                break
            except StaleElementReferenceException:
                continue
    return data


def save_data(data: dict, filename: str) -> None:
    """Persist the scraped data to a JSON file."""
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)
    print(f"\r\033[32mData successfully saved to {filename}!\033[0m")


def main() -> None:
    """Scrape every search-result page and write the combined data set to disk."""
    driver = get_driver()
    driver.get("https://ucassist.org/search-launch/")

    search_button = driver.find_element(By.XPATH, "//input[@name='searchID']")
    search_button.click()

    data = []

    complete = False
    page_number = 1
    while not complete:
        driver.execute_script("document.body.style.zoom='10%'")
        data.extend(scrape_page(driver=driver, page_number=page_number))
        while True:
            try:
                next_button = driver.find_element(
                    By.XPATH, "//*[@data-cb-name='JumpToNext']"
                )
                next_button.click()
                page_number += 1
                break
            except NoSuchElementException:
                complete = True
                break
            except StaleElementReferenceException:
                continue
        time.sleep(1)

    save_data(data=data, filename="ucassist_data.json")


if __name__ == "__main__":
    main()
