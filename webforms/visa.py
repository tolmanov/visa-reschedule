# Blatantly scrapped from https://gist.github.com/Svision/04202d93fb32d14f00ac746879820722
import logging
import time
import json
import random
from datetime import datetime, timedelta, date
from logging.config import dictConfig

import requests
from webforms import settings
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

details = settings.us_visa

USERNAME = details.email
PASSWORD = details.password
SCHEDULE = details.schedule
COUNTRY_CODE = details.country_code  # en-ca for Canada-English
FACILITY_ID = details.facility_id  # 94 for Toronto (others please use F12 to check)

DATE_FMT = "%Y-%m-%d"
# 2022-05-16 WARNING: DON'T CHOOSE DATE LATER THAN ACTUAL SCHEDULED
MY_SCHEDULE_DATE = details.scheduled_date
# MY_CONDITION = lambda month, day: int(month) == 11 and int(day) >= 5
BOOK_CONDITION = lambda dt: dt < details.book_date
NOTIFY_CONDITION = lambda dt: dt < datetime.today().date() + timedelta(days=details.days_notify)

SLEEP_TIME = 60  # recheck time interval

DATE_URL = f"https://ais.usvisa-info.com/{COUNTRY_CODE}/niv/schedule/{SCHEDULE}/appointment/days/{FACILITY_ID}.json?appointments[expedite]=false"
TIME_URL = f"https://ais.usvisa-info.com/{COUNTRY_CODE}/niv/schedule/{SCHEDULE}/appointment/times/{FACILITY_ID}.json?date=%%s&appointments[expedite]=false"
APPOINTMENT_URL = f"https://ais.usvisa-info.com/{COUNTRY_CODE}/niv/schedule/{SCHEDULE}/appointment"
EXIT = False

# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
dictConfig(settings.logging)
logger = logging.getLogger(settings.app_name)  # TODO: Figure out how to do via __name__


def login(driver):
    # Bypass reCAPTCHA
    driver.get(f"https://ais.usvisa-info.com/{COUNTRY_CODE}/niv")
    time.sleep(1)
    a = driver.find_element(By.XPATH, value='//a[@class="down-arrow bounce"]')
    a.click()
    time.sleep(1)

    logger.debug("start sign")
    href = driver.find_element(By.XPATH, value='//*[@id="header"]/nav/div[2]/div[1]/ul/li[3]/a')
    href.click()
    time.sleep(1)
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.NAME, "commit")))

    logger.debug("click bounce")
    a = driver.find_element(By.XPATH, value='//a[@class="down-arrow bounce"]')
    a.click()
    time.sleep(1)

    do_login_action(driver)


def do_login_action(driver):
    logger.debug("input email")
    user = driver.find_element(By.ID, value='user_email')
    user.send_keys(USERNAME)
    time.sleep(random.randint(1, 3))

    logger.debug("input pwd")
    pw = driver.find_element(By.ID, value='user_password')
    pw.send_keys(PASSWORD)
    time.sleep(random.randint(1, 3))

    logger.debug("click privacy")
    box = driver.find_element(By.CLASS_NAME, value='icheckbox')
    box.click()
    time.sleep(random.randint(1, 3))

    logger.debug("commit")
    btn = driver.find_element(By.NAME, value='commit')
    btn.click()
    time.sleep(random.randint(1, 3))

    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//a[contains(text(),'Continue')]")))
        logger.info("Login successfully!")
    except TimeoutError:
        logger.warning("Login failed!")
        login()


def get_date(driver):  #  -> List[date]:
    driver.get(DATE_URL)
    if not is_logined():
        login()
        return get_date()
    else:
        content = driver.find_element(By.TAG_NAME, value='pre').text
        content_obj = json.loads(content)
        return content_obj


def get_time(driver, dt: date) -> str:
    time_url = TIME_URL % dt.strftime(DATE_FMT)
    driver.get(time_url)
    content = driver.find_element(By.TAG_NAME, value='pre').text
    data = json.loads(content)
    time_str = data.get("available_times")[-1]
    logger.debug("Get time successfully!")
    return time_str


# BUGGY
def reschedule(driver, dt: date):
    global EXIT
    logger.info("Start Reschedule")

    time_str = get_time(driver, dt)
    driver.get(APPOINTMENT_URL)

    data = {
        "utf8": driver.find_element(By.NAME, value='utf8').get_attribute('value'),
        "authenticity_token": driver.find_element(By.NAME, value='authenticity_token').get_attribute('value'),
        "confirmed_limit_message": driver.find_element(By.NAME, value='confirmed_limit_message').get_attribute('value'),
        "use_consulate_appointment_capacity": driver.find_element(By.NAME,
                                                                  value='use_consulate_appointment_capacity').get_attribute(
            'value'),
        "appointments[consulate_appointment][facility_id]": FACILITY_ID,
        "appointments[consulate_appointment][date]": dt,
        "appointments[consulate_appointment][time]": time_str,
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36",
        "Referer": APPOINTMENT_URL,
        "Cookie": "_yatri_session=" + driver.get_cookie("_yatri_session")["value"]
    }

    r = requests.post(APPOINTMENT_URL, headers=headers, data=data)
    if (r.text.find('Successfully Scheduled') != -1):
        logger.debug("Successfully Rescheduled")
        EXIT = True
    else:
        logger.warning("ReScheduled Fail")
        logger.warning("POST REQUEST:\n")
        logger.warning(headers)
        logger.warning(data)
        logger.warning("")


def is_logined():
    content = driver.page_source
    if (content.find("error") != -1):
        return False
    return True


def print_date(dates):
    for d in dates:
        logger.debug("%s \t business_day: %s" % (d.get('date'), d.get('business_day')))
    logger.debug("\n")


last_seen = None


def get_available_date(dates) -> date:
    global last_seen

    def is_earlier(dt: date) -> bool:
        return MY_SCHEDULE_DATE > dt

    for d in dates:
        dt = datetime.strptime(d.get('date'), DATE_FMT).date()
        if is_earlier(dt) and dt != last_seen:
            if NOTIFY_CONDITION(dt):
                logger.warning(f"Available date: {dt} is too close. Consider booking manually.")
            elif BOOK_CONDITION(dt):
                last_seen = dt
                return dt


def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1200,900")
    options.add_argument('enable-logging')
    driver = webdriver.Chrome(options=options)

    login(driver)
    retry_count = 0
    while 1:
        if retry_count > 6:
            break
        try:
            logger.debug(datetime.today())
            logger.debug("------------------")

            dates = get_date(driver)[:5]
            print_date(dates)
            dt = get_available_date(dates)
            if dt:
                reschedule(driver, dt)

            if (EXIT):
                break

            time.sleep(SLEEP_TIME)
        except:
            retry_count += 1
            time.sleep(60 * 5)

if __name__ == "__main__":
    main()
