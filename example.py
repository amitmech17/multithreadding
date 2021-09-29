import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import csv
from anticaptchaofficial.imagecaptcha import *
import requests
import shutil
import random
import os
import threading
from selenium.common.exceptions import NoSuchElementException
from multiprocessing.dummy import Pool as ThreadPool

Anti_key = ''


def card_data():
    card_data = []
    file_content = []
    with open('cards.csv') as csv_file:
        if os.path.isfile("./completed_list.txt"):
            with open("./completed_list.txt") as f:
                file_content = f.readlines()
            file_content = [i.split(",")[0].strip() for i in file_content]
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                line_count += 1
            else:
                if row[0].strip() == "":
                    continue
                if row[0].strip() in file_content:
                    continue
                card_data.append(row)
                line_count += 1
        return card_data


def check_exists_of_pay_button(driver):
    try:
        driver.find_element_by_id('gvDTLS_btnPAY_0')
    except NoSuchElementException:
        return False
    return True


def check_exists_of_success(driver):
    try:
        driver.find_element_by_xpath("//div[@class='f1-step active']")
    except NoSuchElementException:
        return False
    return False


def captcha_solve(driver):
    img_name = "data_{}.png".format(random.randint(10000, 100000))
    with open(img_name, 'wb') as file:
        file.write(driver.find_element_by_id('imgcapcha').screenshot_as_png)
    solver = imagecaptcha()
    solver.set_verbose(1)
    solver.set_key(Anti_key)
    captcha_text = solver.solve_and_return_solution("./{}".format(img_name))
    print(captcha_text)
    os.remove("./{}".format(img_name))
    if captcha_text != 0:
        print("captcha text " + captcha_text)
    else:
        print("task finished with error " + solver.error_code)
    driver.find_element_by_id('txtCaptcha').clear()
    driver.find_element_by_id('txtCaptcha').send_keys(captcha_text)
    driver.find_element_by_id('btnproceed').click()
    result = check_exists_of_pay_button(driver)
    if result:
        return True
    else:
        t = solver.report_incorrect_image_captcha()
        return False


def paytm_flow(driver, card, expiry, cvv, pin):
    driver.find_element_by_xpath("//div[@class='pos-r']//input[@type='tel']").clear()
    driver.find_element_by_xpath("//div[@class='pos-r']//input[@type='tel']").send_keys(card)
    expiry = expiry.split("/")
    mm = expiry[0].strip()
    yy = expiry[1].strip()
    expiry_date = "{}-{}02".format(expiry[0].strip(), expiry[1].strip()[::-1])
    print("expiry date {}".format(expiry_date))
    driver.find_element_by_id('mm').send_keys(mm)
    driver.find_element_by_id('yy').send_keys(yy)
    driver.find_element_by_xpath("//input[@type='password']").send_keys(cvv)
    driver.find_element_by_xpath("//span[contains(@class,'ib vm _1rtn')]").click()
    driver.find_element_by_xpath("//span[contains(text(),'ATM PIN')]").click()
    driver.find_element_by_id("expDate").send_keys(expiry_date)
    # 07-4202
    driver.find_element_by_id("pin").send_keys(pin)
    driver.find_element_by_id("submitButtonIdForPin").click()
    time.sleep(2)
    return check_exists_of_success(driver)


def web_automate(list = [],*args):
    card = list[0]
    cvv = list[1]
    expiry = list[2]
    pin = list[3]
    amount = list[4]
    account = list[5]
    try:
        time.sleep(5)
        options = Options()
        # options.add_argument('--headless')
        options.add_argument('--no-sandbox') # required when running as root user. otherwise you would get no sandbox errors.
        options.add_argument("--start-maximized")
        driver = webdriver.Chrome(executable_path='../ltc/chromedriver', options=options)
        driver.implicitly_wait(25)
        driver.get("https://reporting.idfcfirstbank.com/QuickPay/QPInfo_Customer.aspx")
        driver.find_element_by_id('txtAgreementNo').clear()
        driver.find_element_by_id('txtAgreementNo').send_keys(account)
        for i in range(5):
            if captcha_solve(driver):
                break
            else:
                continue
        driver.find_element_by_id('gvDTLS_btnPAY_0').click()
        driver.find_element_by_id('txtAMT').send_keys(amount)
        payment_options = driver.find_elements_by_xpath("//div[@class='col-md-3']")
        for pay in payment_options:
            if 'paytm' in pay.text.lower():
                pay.click()
        driver.find_element_by_id('btnProceed').click()
        driver.find_element_by_id('ChkbxpmtCNF').click()
        driver.find_element_by_id('btnProceed').click()
        driver.find_element_by_xpath("//span[contains(text(),'Debit Card')]").click()
        for j in range(5):
            if paytm_flow(driver, card, expiry, cvv, pin):
                break
            else:
                continue
        receipt_data = driver.find_elements_by_xpath("//div[@class='clearfix']")
        print("success")
        try:
            txn = driver.find_element_by_id('lblTranRefNo').text
            with open("./completed_list.txt", 'a+') as f:
                f.write('{}, {}, {}, {}, {}, {}, Done, {}\n'.format(card, cvv, expiry, pin, amount, account, txn))
            driver.quit()
        except:
            print("error")
            with open("./completed_list.txt", 'a+') as f:
                f.write('{}, {}, {}, {}, {}, {}, Done\n'.format(card, cvv, expiry, pin, amount, account))
            driver.quit()
    except Exception as e:
        with open("failed_list.txt", 'a+') as f:
            f.write('{}, {}\n'.format(card, account))
        print('error in main : {}'.format(e))
        try:
            driver.quit()
        except:
            print("driver is not initiated")


card_data = card_data()
count = len(card_data)
print(count)
if count == 0:
    print("All done")
pool = ThreadPool(1)
results = pool.map(web_automate, card_data)
pool.close()
pool.join()



