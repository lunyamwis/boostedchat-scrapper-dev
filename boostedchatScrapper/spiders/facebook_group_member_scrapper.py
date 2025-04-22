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



def scrap_facebook_group_members(cookies_,group_url = "https://www.facebook.com/groups/1339224732945188/members"):
    """Define a main entry point."""

    # Handle input - Replace with your input method (e.g., command line arguments, config file)
    # Replace with the actual group URL
    
    cookies = convert_cookies(cookies_)
    driver_version = "132.0.6834.110"
    if not group_url:
        msg = 'Missing "group_url" attribute in input!'
        raise ValueError(msg)

    logging.info(f"Attempting to get Facebook group members from: {group_url}")

    member_data = []
    chrome_executable_path = '/opt/chrome/chrome-linux64/chrome'
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

        get_url(driver, group_url)
        time.sleep(5)

        time.sleep(5)

        # # Scroll down to load all members (optional, but often needed)
        # scroll_pause_time = 2
        # screen_height = driver.execute_script("return window.screen.height;")
        # i = 1

        # while True:
        #     # Scroll down to the bottom
        #     driver.execute_script(f"window.scrollTo(0, {screen_height*i});")
        #     i += 1
        #     time.sleep(scroll_pause_time)
        #     # Calculate new document height and compare with last document height
        #     scroll_height = driver.execute_script("return document.body.scrollHeight;")
        #     if (screen_height * i) > scroll_height:
        #         break

        # Extract member information (example using BeautifulSoup)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # import pdb;pdb.set_trace()
        members = soup.find_all("a","x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz xkrqix3 x1sur9pj xzsf02u x1pd3egz")
        # Print or process results
        logging.info(f'Scraped {len(members)} members successfully!')
        for member in members:
            member_info = {
                "name": member.text,
                "id": member.get_attribute_list("href")[0].split('/')[-2] if member.get_attribute_list("href") else None,
            }
            member_data.append(member_info)
            print(member)
        
        

    except Exception as e:
        logging.exception(f"An error occurred: {e}")

    finally:
        if driver:  # Check if the driver was initialized before quitting
            driver.quit()



    return member_data
    # send message
    # get_url(driver, f"https://www.facebook.com/messages/t/{user_id}")
    # message_box = driver.find_element(By.XPATH,"/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[1]/div/div/div/div/div/div[2]/div/div/div/div[2]/div/div/div[4]/div[2]/div/div[1]/div[1]")
    # message_box.send_keys("Hello, greetings!")
    # message_box.send_keys(Keys.ENTER)
# main()


