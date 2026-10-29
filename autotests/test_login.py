import pytest
from selenium.webdriver.common.by import By

from pages.auth_pages import LoginPage, RegisterPage

counter = {"n": 0}


def new_user(driver, server):
    counter["n"] += 1
    name = "login_user_%d" % counter["n"]
    RegisterPage(driver, server).register(login=name)
    return name


PASSWORD = RegisterPage.DEFAULT["password"]


def test_l01_participant_login(driver, server):
    name = new_user(driver, server)
    page = LoginPage(driver, server)
    page.login(name, PASSWORD)
    page.wait_url_contains("/requests")
    assert name in driver.find_element(By.CSS_SELECTOR, ".logout button").text


def test_l02_admin_login_goes_to_panel(driver, server):
    page = LoginPage(driver, server)
    page.login("admin", "Admin2026!")
    page.wait_url_contains("/admin")


@pytest.mark.parametrize("login,password", [("nobody_here", "Parol2026"), ("admin", "wrong-password"), ("admin", "ADMIN2026!")],
                         ids=["нет такого логина", "неверный пароль", "другой регистр пароля"])
def test_l03_wrong_credentials(driver, server, login, password):
    page = LoginPage(driver, server)
    page.login(login, password)
    assert "Неверный логин или пароль" in page.message()
    assert "/login" in driver.current_url


def test_l04_empty_fields_show_errors(driver, server):
    page = LoginPage(driver, server).open("/login")
    page.submit()
    assert set(page.wait_errors()) == {"login", "password"}


@pytest.mark.parametrize("login", ["admin' OR '1'='1", "admin'--", "' OR 1=1 --"], ids=["OR 1=1", "комментарий", "пустой логин"])
def test_l05_sql_injection_does_not_log_in(driver, server, login):
    page = LoginPage(driver, server).open("/login")
    driver.execute_script("document.querySelector('input[name=login]').removeAttribute('maxlength')")
    page.type_into("login", login)
    page.type_into("password", "что-угодно")
    page.submit()
    assert "/admin" not in driver.current_url and "/requests" not in driver.current_url


def test_l06_lock_after_five_wrong_attempts(driver, server):
    name = new_user(driver, server)
    page = LoginPage(driver, server)
    for _ in range(5):
        page.login(name, "неверный-пароль")
    page.login(name, PASSWORD)
    assert "Слишком много попыток" in page.message()


def test_l07_logout_closes_access(driver, server):
    name = new_user(driver, server)
    page = LoginPage(driver, server)
    page.login(name, PASSWORD)
    page.wait_url_contains("/requests")
    driver.find_element(By.CSS_SELECTOR, ".logout button").click()
    page.wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, ".menu a[href='/login']"))
    driver.get(server + "/requests")
    page.wait_url_contains("/login")


@pytest.mark.parametrize("path", ["/requests", "/requests/new", "/admin/"], ids=["мои заявки", "новая заявка", "панель"])
def test_l08_guest_is_sent_to_login(driver, server, path):
    driver.get(server + path)
    assert "/login" in driver.current_url


def test_l09_participant_has_no_access_to_admin_panel(driver, server):
    name = new_user(driver, server)
    LoginPage(driver, server).login(name, PASSWORD)
    driver.get(server + "/admin/")
    assert "Ошибка 403" in driver.page_source


def test_l10_password_is_not_visible_in_field(driver, server):
    page = LoginPage(driver, server).open("/login")
    assert page.field("password").get_attribute("type") == "password"


def test_l11_login_name_is_case_insensitive(driver, server):
    page = LoginPage(driver, server)
    page.login("ADMIN", "Admin2026!")
    page.wait_url_contains("/admin")
