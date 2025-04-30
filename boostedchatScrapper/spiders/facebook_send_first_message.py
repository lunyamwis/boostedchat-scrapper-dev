import logging
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
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



def send_first_message(cookies_=None, user_id=None,username=None,message=None):
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
        get_url(driver, f"https://www.facebook.com/messages/new")
        # import pdb;pdb.set_trace()


        time.sleep(5)

        try:
            # Wait for the message box to be present
            # input_box = WebDriverWait(driver, 10).until(
            #     EC.presence_of_element_located((By.XPATH,"/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[1]/div[2]/div/div/div/div[1]/input"))
            # )
            # input_box.click()
            input_box = driver.find_element(By.XPATH,"/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[1]/div[2]/div/div/div/div[1]/input")
            driver.execute_script("arguments[0].click();", input_box)
            input_box.send_keys(username)
            # input_box.send_keys(Keys.ENTER)
            time.sleep(5)
            logging.info(f"Successfully inserted contact!")
        except Exception as e:
            logging.warning(f"Failed to insert contact: {e}")
        
        try:
            # Wait until the element is clickable (up to 10 seconds)
            # element = WebDriverWait(driver, 10).until(
            #     EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[2]/div/div/div[1]/div[1]/ul/li[1]/ul/div[1]/li'))
            # )
            # element.click()
            span_element = driver.find_element(By.XPATH,"/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[2]/div/div/div[1]/div[1]/ul/li/ul/div[1]/li/a/div[1]/div[2]/div/div/div/span/span/span")
            driver.execute_script("arguments[0].click();", span_element)
            time.sleep(5)
            # Perform the click action
            logging.info("Element clicked successfully!")
            # mainframe = WebDriverWait(driver, 10).until(
            #     EC.presence_of_element_located((By.XPATH,"/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div[2]/div[1]/div/div/div/div/div/div/div/div/div/div/div[1]/div[2]/div[2]/div"))  
            # )
            # mainframe.click()input_box = WebDriverWait(driver, 10).until(
            #     EC.presence_of_element_located((By.XPATH,"/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[1]/div[2]/div/div/div/div[1]/input"))
            
            actions = ActionChains(driver)
            actions.send_keys(Keys.ENTER).perform()
            logging.info("Mainframe clicked successfully!")
            driver.get_screenshot_as_file("myfile.png")
        except Exception as e:
            logging.warning(f"Error: {e}")
        
        try:
            # Wait for the message box to be present
            message_textbox = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH,"/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div[2]/div[2]/div/div/div/div/div[4]/div[2]/div/div[1]/div[1]"))
            )
            # message_box = driver.find_element(By.XPATH,"/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[1]/div/div/div/div/div/div[2]/div/div/div/div[2]/div/div/div[4]/div[2]/div/div[1]/div[1]")
            # message_textbox.click()
            message_textbox.send_keys(message)
            message_textbox.send_keys(Keys.ENTER)
            logging.info(f"Successfully sent message!")
            time.sleep(5)
        except Exception as e:
            logging.warning(f"Failed to find message box: {e}")
            
        
        # try:
        #     continue_ = driver.find_element(By.XPATH,"/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[1]/div/div/div/div/div/div[2]/div/div/div/div[2]/div/div[2]/div/div/div")
        #     continue_.click()
        #     time.sleep(5)
        # except Exception as e:
        #     logging.warning(f"Failed to click continue button: {e}")
        
        # try:
        #     time.sleep(5)
        #     message_box = driver.find_element(By.XPATH,"/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[1]/div/div/div/div/div/div[2]/div/div/div/div[2]/div/div/div[4]/div[2]/div/div[1]/div[1]")
        #     message_box.send_keys("go ahead!")
        #     message_box.send_keys(Keys.ENTER)

        #     # Save results to Apify dataset
        #     logging.info(f'Successfully reached out!')
        # except Exception as e:
        #     logging.warning(f"Unsuccessful in sending message: {e}")

        
        
        
        

    except Exception as e:
        logging.exception(f"An error occurred: {e}")

    finally:
        if driver:  # Check if the driver was initialized before quitting
            driver.quit()

    # send message
    
# main()


