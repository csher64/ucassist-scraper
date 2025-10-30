"""Utilities for scraping UC Assist service listings with Selenium."""

from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import chromedriver_autoinstaller
import json


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
        try:
            for link in driver.find_elements(By.XPATH, "//a"):
                if link.get_attribute("innerText") == "View Details":
                    service_links.append(link)
        except StaleElementReferenceException:
            service_links = []
            continue
    return service_links


def extract_service_data(driver: webdriver, service_link: WebElement) -> dict:
    """Click a service link and collect key/value data from the details view."""
    while True:
        try:
            service_link.click()
            break
        except ElementClickInterceptedException:
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", service_link
            )
            continue

    keys = []
    while not keys:
        for key in driver.find_elements(
            By.XPATH, "//div[contains(@class, 'cbFormLabelCell')]"
        ):
            keys.append(key.get_attribute("innerText"))

    values = []
    while not values:
        for i, element in enumerate(
            driver.find_elements(By.XPATH, "//*[contains(@class, 'cbFormDataCell')]")
        ):
            img = element.find_elements(By.TAG_NAME, "img")
            if not img:
                innerText = element.get_attribute("innerText")
                if keys[i] in (
                    "Keyword(s) Associate With Service",
                    "Counties Available",
                ):
                    innerText = innerText.split("\n")
                values.append(innerText)
            else:
                values.append(img[0].get_attribute("src"))

    while True:
        try:
            back_button = driver.find_element(
                By.XPATH, "//input[contains(@class, 'cbBackButton')]"
            )
            back_button.click()
            driver.execute_script("document.body.style.zoom='10%'")
            break
        except ElementClickInterceptedException:
            driver.execute_script("document.body.style.zoom='50%'")
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", back_button
            )
            continue

    return dict(zip(keys, values))


def scrape_page(driver: webdriver, page_number: int) -> list[dict]:
    """Scrape all services on the current page, returning their detail dictionaries."""
    while True:
        try:
            service_links = get_service_links(driver=driver)
            data = []
            for i in range(0, len(service_links)):
                data.append(
                    extract_service_data(
                        driver=driver, service_link=get_service_links(driver=driver)[i]
                    )
                )
                print(f"\033[34mScraped page {page_number}, service {i + 1}.\033[0m")
            break
        except StaleElementReferenceException:
            continue
        except IndexError:
            break
    return data


def click_next_page(driver: webdriver) -> None:
    """Navigate to the next page of service listings."""
    while True:
        try:
            next_button = driver.find_element(
                By.XPATH, "//*[@data-cb-name='JumpToNext']"
            )
            next_button.click()
            break
        except (StaleElementReferenceException, ElementClickInterceptedException):
            continue
        except:
            return True
    return False


def save_data(data: list[dict], filename: str) -> None:
    """Persist the scraped data to a JSON file."""
    with open(filename, "w") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    print(f"\033[32mData successfully saved to {filename}!\033[0m")


def clean_data(data: list[dict]):
    """Clean the extracted data."""
    cleaned_data = []
    for record in data:
        for key, value in record.items():
            if value == " ":
                record[key] = None
        cleaned_data.append(record)
    return cleaned_data


def main() -> None:
    """Scrape every search-result page and write the combined data set to disk."""
    driver = get_driver()
    driver.get("https://ucassist.org/search-launch/")

    while True:
        try:
            search_button = driver.find_element(By.XPATH, "//input[@name='searchID']")
            search_button.click()
            break
        except NoSuchElementException:
            continue

    data = []
    complete = False
    page_number = 1
    while not complete:
        driver.execute_script("window.scrollTo(0, 0);")
        page_data = []
        page_data = scrape_page(driver=driver, page_number=page_number)
        page_number += 1
        data.extend(page_data)
        complete = click_next_page(driver=driver)

    save_data(data=clean_data(data), filename="ucassist_data.json")


if __name__ == "__main__":
    main()
