import os
import sys
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from time import sleep
import re

chrome_profile = 'C:\\ChromeProfile'
options = webdriver.ChromeOptions()
options.add_argument('user-data-dir=%s' % chrome_profile)  # Path to your chrome profile
driver = webdriver.Chrome(chrome_options=options)
driver.implicitly_wait(10)


def click(ele):
    driver.execute_script('arguments[0].scrollIntoView();', ele)
    ActionChains(driver).move_to_element(ele).click().perform()


def find_by_text(text):
    return driver.find_element_by_xpath("//*[contains(text(), '%s')]" % text)


def find_by_css(css):
    return driver.find_element_by_css_selector(css)


def find_by_xpath(xpath):
    return driver.find_element_by_xpath(xpath)


def send_keys(keys):
    ActionChains(driver).send_keys(keys).perform()
