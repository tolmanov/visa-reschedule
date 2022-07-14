# Blatantly scrapped from https://gist.github.com/Svision/04202d93fb32d14f00ac746879820722
import logging
import time
import json
import random
from datetime import datetime, timedelta, date

import requests
import schedule
from lazy_object_proxy import Proxy

from webforms import settings
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from webforms.service.notify import notify
from webforms.url import UrlGenerator

GLOBAL_MIN_DATE = None
DATE_FMT = "%Y-%m-%d"

# MY_CONDITION = lambda month, day: int(month) == 11 and int(day) >= 5
BOOK_CONDITION = lambda dt: dt < settings.us_visa.book_date  # This is lazy loaded so it won't invoke settings here
NOTIFY_CONDITION = lambda dt: dt < datetime.today().date() + timedelta(days=settings.us_visa.days_notify)

SLEEP_TIME = 60  # recheck time interval

url_generator = Proxy(UrlGenerator)

EXIT = False

# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
logger = logging.getLogger(__name__)  # TODO: Figure out how to do via __name__


class BookingError(Exception):
    pass


def login(driver):
    # Bypass reCAPTCHA
    driver.get(f"https://ais.usvisa-info.com/{url_generator.country_code}/niv")
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
    user.send_keys(settings.us_visa.email)
    time.sleep(random.randint(1, 3))

    logger.debug("input pwd")
    pw = driver.find_element(By.ID, value='user_password')
    pw.send_keys(settings.us_visa.password)
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
        logger.info("Logged in successfully!")
    except TimeoutError:
        logger.warning("Login failed!")
        login()


def get_date(driver):  # -> List[date]:
    driver.get(url_generator.date_url)
    if not is_logged_in(driver):
        login(driver)
        return get_date(driver)
    else:
        content = driver.find_element(By.TAG_NAME, value='pre').text
        content_obj = json.loads(content)
        return content_obj


def get_time(driver, dt: date) -> str:
    time_url = url_generator.time_url % dt.strftime(DATE_FMT)
    driver.get(time_url)
    content = driver.find_element(By.TAG_NAME, value='pre').text
    data = json.loads(content)
    try:
        time_str = data.get("available_times")[-1]
    except IndexError:
        raise BookingError(f"No time retrieved from link {time_url}. ")
    logger.debug("Get time successfully!")
    return time_str


# BUGGY
def reschedule(driver, dt: date):
    global EXIT
    logger.info("Start Reschedule")

    try:
        time_str = get_time(driver, dt)
    except BookingError:
        logger.exception("Reschedule error")
        return
    date_str = dt.strftime(DATE_FMT)
    driver.get(url_generator.appointment_url)

    data = {
        "utf8": driver.find_element(By.NAME, value='utf8').get_attribute('value'),
        "authenticity_token": driver.find_element(By.NAME, value='authenticity_token').get_attribute('value'),
        "confirmed_limit_message": driver.find_element(By.NAME, value='confirmed_limit_message').get_attribute('value'),
        "use_consulate_appointment_capacity": driver.find_element(By.NAME,
                                                                  value='use_consulate_appointment_capacity').get_attribute(
            'value'),
        "appointments[consulate_appointment][facility_id]": url_generator.facility_id,
        "appointments[consulate_appointment][date]": date_str,
        "appointments[consulate_appointment][time]": time_str,
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36",
        "Referer": url_generator.appointment_url,
        "Cookie": "_yatri_session=" + driver.get_cookie("_yatri_session")["value"]
    }

    r = requests.post(url_generator.appointment_url, headers=headers, data=data)
    if (r.text.find('Successfully Scheduled') != -1):
        logger.debug("Successfully Rescheduled")
        EXIT = True
    else:
        logger.warning("ReScheduled Fail")
        logger.warning("POST REQUEST:\n")
        logger.warning(headers)
        logger.warning(data)
        logger.warning("")


def is_logged_in(driver):
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
    global GLOBAL_MIN_DATE

    def is_earlier(dt: date) -> bool:
        return settings.us_visa.scheduled_date > dt

    min_date = None
    for d in dates:
        dt = datetime.strptime(d.get('date'), DATE_FMT).date()
        min_date = min(dt, min_date or dt)
        if is_earlier(dt) and dt != last_seen:
            notify.send(f"{dt} is available for booking!")
            if BOOK_CONDITION(dt) and not NOTIFY_CONDITION(dt):
                logger.info(f"Date available: {dt}. Booking now.")
                last_seen = dt
                return dt
    if min_date:
        if min_date != GLOBAL_MIN_DATE:
            GLOBAL_MIN_DATE = min_date
            logger.info(f"Earliest available date is {min_date}, Skipping")


def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1200,900")
    options.add_argument('enable-logging')
    driver = webdriver.Chrome(options=options)

    login(driver)

    def run_program(_driver):
        try:
            dates = get_date(_driver)[:5]
            dt = get_available_date(dates)
            if dt:
                reschedule(_driver, dt)
        except Exception as e:
            logger.exception("Exception occurred. Retry...")

    ss = schedule.every(30).seconds.do(lambda: run_program(driver))
    while True:
        schedule.run_pending()


if __name__ == "__main__":
    main()
