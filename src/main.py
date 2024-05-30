from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.common.exceptions import WebDriverException, NoSuchDriverException, TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import os
import re
from flask import Flask, jsonify

# Example usage
chrome_version = '124.0.6367.78'
extension_id = 'lgmpfmgeabnnlemejacfljbmonaomfmm'  # Replace with the actual extension ID
output_file = "extension.crx"

try:
    USER = os.environ['NODEPAY_USER']
    PASSW = os.environ['NODEPAY_PASS']
except KeyError:
    USER = ''
    PASSW = ''

try:
    ALLOW_DEBUG = os.environ['ALLOW_DEBUG'] == 'True'
except KeyError:
    ALLOW_DEBUG = False

if USER == '' or PASSW == '':
    print('Please set NODEPAY_USER and NODEPAY_PASS env variables')
    exit()

if ALLOW_DEBUG:
    print('Debugging is enabled! This will generate a screenshot and console logs on error!')

def download_crx(extension_id, output_file, chrome_version):
    url_template = "https://clients2.google.com/service/update2/crx?response=redirect&prodversion={}&acceptformat=crx2,crx3&x=id%3D{}%26uc"
    url = url_template.format(chrome_version, extension_id)
    headers = {
        'User-Agent': f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36"
    }
    response = requests.get(url, headers=headers, allow_redirects=True, stream=True)
    if response.status_code == 200:
        with open(output_file, 'wb') as file:
            file.write(response.content)
        print(f"Extension {extension_id} has been downloaded as {output_file}.")
    else:
        print(f"Failed to download the extension. Status code: {response.status_code}")

def generate_error_report(driver):
    if not ALLOW_DEBUG:
        return
    driver.save_screenshot('error.png')
    logs = driver.get_log('browser')
    with open('error.log', 'w') as f:
        for log in logs:
            f.write(str(log))
            f.write('\n')
    url = 'https://imagebin.ca/upload.php'
    files = {'file': ('error.png', open('error.png', 'rb'), 'image/png')}
    response = requests.post(url, files=files)
    print(response.text)
    print('Error report generated! Provide the above information to the developer for debugging purposes.')

print('Downloading extension...')
download_crx(extension_id, output_file, chrome_version)
print('Downloaded! Installing extension and driver manager...')

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-dev-shm-usage")
options.add_argument('--no-sandbox')
options.add_extension(output_file)

print('Installed! Starting...')
try:
    driver = webdriver.Chrome(options=options)
except (WebDriverException, NoSuchDriverException):
    print('Could not start with Manager! Trying to default to manual path...')
    try:
        driver_path = "/usr/bin/chromedriver"
        service = ChromeService(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=options)
    except (WebDriverException, NoSuchDriverException):
        print('Could not start with manual path! Exiting...')
        exit()

def set_desktop_resolution(driver, width=1920, height=1080):
    driver.set_window_size(width, height)

print('Started! Logging in...')
set_desktop_resolution(driver, 1920, 1080)
driver.get('https://app.nodepay.ai/')

sleep = 2
while True:
    try:
        # Wait for either the close button or the login form elements to be present
        close_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//button[@aria-label="Close"]'))
        )
        if close_button.is_displayed():
            close_button.click()
            print('Close button clicked! Proceeding with login.')
            continue  # Continue to check for login form elements
    except (TimeoutException, NoSuchElementException):
        # If the close button is not found, continue to check for the login form elements
        pass

    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="basic_user"]'))
        )
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="basic_password"]'))
        )
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[@type="submit"]'))
        )
        break
    except TimeoutException:
        time.sleep(1)
        print('Loading login form...')
        sleep += 1
        if sleep > 15:
            print('Could not load login form! Exiting...')
            generate_error_report(driver)
            driver.quit()
            exit()


user = driver.find_element(By.XPATH, '//*[@id="basic_user"]')
passw = driver.find_element(By.XPATH, '//*[@id="basic_password"]')
submit = driver.find_element(By.XPATH, '//*[@type="submit"]')

user.send_keys(USER)
passw.send_keys(PASSW)
submit.click()

sleep = 0
while True:
    try:
        e = driver.find_element(By.XPATH, '//*[contains(text(), "Dashboard")]')
        break
    except:
        time.sleep(1)
        print('Logging in...')
        sleep += 1
        if sleep > 30:
            print('Could not login! Double Check your username and password! Exiting...')
            generate_error_report(driver)
            driver.quit()
            exit()

print('Logged in! Waiting for connection...')
driver.get('chrome-extension://' + extension_id + '/index.html')
sleep = 0
while True:
    try:
        # Add an explicit wait here
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(@class, "rounded-lg") and contains(@href, "dashboard")]/span[contains(text(), "Open Dashboard")]'))
        )
        print('Found the "Open Dashboard" link!')
        break
    except Exception as e:
        time.sleep(1)
        print('Loading connection...', e)
        sleep += 1
        if sleep > 30:
            print('Could not load connection! Exiting...')
            generate_error_report(driver)
            driver.quit()
            exit()

print('Connected! Starting API...')

def get_data(driver):
    try:
        # Wait for the element indicating network quality to be present
        network_quality_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//span[contains(text(), 'Network Quality')]"))
        )
        network_quality = network_quality_element.text.split(":")[1].strip()
    except Exception as e:
        network_quality = False
        print(f'Could not get network quality: {e}')
        generate_error_report(driver)

    try:
        # Wait for the element indicating earnings to be present
        earnings_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//div[@class='h-[64px] bg-grey-primary rounded-lg py-3 px-6 flex flex-col items-center justify-between']/div/span[@class='text-16px font-bold mr-1 truncate']"))
        )
        epoch_earnings = earnings_element.text
    except Exception as e:
        epoch_earnings = False
        print(f'Could not get earnings: {e}')
        generate_error_report(driver)
        
    try:
        # Wait for the badge elements indicating connection status to be present
        badges = WebDriverWait(driver, 10).until(
            EC.visibility_of_all_elements_located((By.XPATH, "//span[@class='font-bold text-green']"))
        )
        connected = badges[0].text if badges else False  # Assuming you want the text of the first matching element
    except Exception as e:
        connected = False
        print(f'Could not get connection status: {e}')
        generate_error_report(driver)

    return {'connected': connected, 'network_quality': network_quality, 'epoch_earnings': epoch_earnings}

# Flask API
app = Flask(__name__)

@app.route('/')
def get_endpoint():
    try:
        data = get_data(driver)
        # Convert None values to False for JSON serialization
        for key in data:
            if data[key] is None:
                data[key] = False
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)

driver.quit()
