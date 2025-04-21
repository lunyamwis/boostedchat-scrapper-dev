import logging
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup
import time
import tenacity

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
true, null = True, None
false = False
from typing import List, Dict, Any

def convert_cookies(input_cookies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    output_cookies = []
    for cookie in input_cookies:
        converted_cookie = {
            "name": cookie.get("name"),
            "value": cookie.get("value"),
            "domain": cookie.get("domain"),
            "path": cookie.get("path"),
            "secure": cookie.get("secure", False),
            "httpOnly": cookie.get("httpOnly", False),
            "expires": None  # Always set to None as per your example
        }
        output_cookies.append(converted_cookie)
    return output_cookies



def send_first_message(cookies_, user_id):
    """Define a main entry point."""

    # Handle input - Replace with your input method (e.g., command line arguments, config file)
    
    cookies = convert_cookies(cookies_)
    driver_version = "132.0.6834.110"
    driver = None  # Initialize driver outside the try block


    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    # Set Chrome executable path
    #options.binary_location = chrome_executable_path

    # Add a retry mechanism to WebDriver initialization
    def initialize_driver():
        driver = None
        try:
            driver = webdriver.Chrome(options=options)

        except Exception as e:
            logging.warning(f"Failed to initialize WebDriver: ")
            try:
                driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager(
                latest_release_url='https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json',
                driver_version=driver_version).install()), options=options)
                print(f"successfully bumped up the version to {driver_version}")
            except Exception as err:
                print(err)
            raise
        return driver

    try:
        driver = initialize_driver()
        #import pdb;pdb.set_trace()

        # Navigate to Facebook
        driver.get("https://www.facebook.com")
        time.sleep(2)

        # Add cookies
        if cookies:
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    logging.warning(f"Failed to set cookie {cookie.get('name')}: {e}")


        # Refresh the page after adding cookies
        driver.refresh()
        time.sleep(2)

        # Add a retry mechanism to driver.get
        def get_url(driver, url):
            driver.get(url)

        
        time.sleep(5)
        get_url(driver, f"https://www.facebook.com/messages/t/{user_id}")
        time.sleep(5)
        try:
            continue_ = driver.find_element(By.XPATH,"/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[1]/div/div/div/div/div/div[2]/div/div/div/div[2]/div/div[2]/div/div/div")
            continue_.click()
            time.sleep(5)
        except Exception as e:
            logging.warning(f"Failed to click continue button: {e}")
        
        try:
            message_box = driver.find_element(By.XPATH,"/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[1]/div/div/div/div/div/div[2]/div/div/div/div[2]/div/div/div[4]/div[2]/div/div[1]/div[1]")
            message_box.send_keys("go ahead!")
            message_box.send_keys(Keys.ENTER)

            # Save results to Apify dataset
            logging.info(f'Successfully reached out!')
        except Exception as e:
            logging.warning(f"Unsuccessful in sending message: {e}")
        

    except Exception as e:
        logging.exception(f"An error occurred: {e}")

    finally:
        if driver:  # Check if the driver was initialized before quitting
            driver.quit()

    # send message
    
# main()


