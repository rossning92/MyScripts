from selenium import webdriver

options = webdriver.ChromeOptions()
options.add_argument("user-data-dir=C:\\Path") #Path to your chrome profile
w = webdriver.Chrome(executable_path="C:\\Users\\chromedriver.exe", chrome_options=options)