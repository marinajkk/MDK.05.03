import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from pages.auth_pages import LoginPage, RegisterPage

counter = {"n": 0}


def logged_in_user(driver, server):
    counter["n"] += 1
    name = "req_user_%d" % counter["n"]
    RegisterPage(driver, server).register(login=name)
    LoginPage(driver, server).login(name, RegisterPage.DEFAULT["password"])
    return name


def fill_request(driver, event_text, seats="2"):
    Select(driver.find_element(By.NAME, "event_id")).select_by_visible_text(event_text) if event_text else None
    Select(driver.find_element(By.NAME, "room")).select_by_index(1)
    Select(driver.find_element(By.NAME, "payment")).select_by_index(1)
    field = driver.find_element(By.NAME, "seats")
    driver.execute_script("arguments[0].type = 'text'", field)
    field.clear()
    field.send_keys(seats)


def event_names(driver):
    return [o.text for o in Select(driver.find_element(By.NAME, "event_id")).options if o.get_attribute("value")]


def test_q01_request_for_upcoming_event(driver, server):
    logged_in_user(driver, server)
    driver.get(server + "/requests/new")
    first = event_names(driver)[0]
    fill_request(driver, first)
    driver.find_element(By.CSS_SELECTOR, "main form button[type=submit]").click()
    WebDriverWait(driver, 6).until(EC.url_contains("/requests"))
    assert "Заявка отправлена" in driver.page_source


def test_q02_past_events_are_not_offered(driver, server):
    logged_in_user(driver, server)
    driver.get(server + "/requests/new")
    assert not any("Данные и ИИ" in name for name in event_names(driver))


def test_q03_request_for_past_event_is_rejected(driver, server):
    logged_in_user(driver, server)
    driver.get(server + "/requests/new")
    select = driver.find_element(By.NAME, "event_id")
    driver.execute_script(
        "const o = document.createElement('option'); o.value = '5'; o.text = 'Данные и ИИ'; arguments[0].appendChild(o)", select)
    fill_request(driver, "Данные и ИИ")
    driver.find_element(By.CSS_SELECTOR, "main form button[type=submit]").click()
    time.sleep(1.5)
    assert "Заявка отправлена" not in driver.page_source


def test_q04_unusual_digit_in_seats_is_an_error_not_a_crash(driver, server):
    logged_in_user(driver, server)
    driver.get(server + "/requests/new")
    fill_request(driver, event_names(driver)[0], seats="\u00b2")
    driver.find_element(By.CSS_SELECTOR, "main form button[type=submit]").click()
    time.sleep(1.5)
    assert "Internal Server Error" not in driver.page_source
