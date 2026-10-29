import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from pages.auth_pages import LoginPage, RegisterPage

counter = {"n": 0}


def unique(prefix="user"):
    counter["n"] += 1
    return "%s_%d" % (prefix, counter["n"])


def register_ok(driver, server, **values):
    page = RegisterPage(driver, server)
    values.setdefault("login", unique())
    page.register(**values)
    return page, values["login"]


def test_r01_valid_data(driver, server):
    page, _ = register_ok(driver, server)
    page.wait_url_contains("/login")
    assert "Регистрация прошла успешно" in driver.page_source


@pytest.mark.parametrize("login", ["abc", "a" * 20, "User_123"], ids=["3 символа", "20 символов", "буквы цифры подчёркивание"])
def test_r02_login_valid_boundaries(driver, server, login):
    page, _ = register_ok(driver, server, login=login)
    page.wait_url_contains("/login")


@pytest.mark.parametrize("login", ["ab", "", "логин", "ab cd", "a-b-c", "a@b.ru"],
                         ids=["2 символа", "пусто", "кириллица", "пробел", "дефис", "собака"])
def test_r03_login_invalid(driver, server, login):
    page, _ = register_ok(driver, server, login=login)
    errors = page.wait_errors()
    assert "login" in errors
    assert "/register" in driver.current_url


def test_r04_login_field_stops_at_20_characters(driver, server):
    page = RegisterPage(driver, server).open("/register")
    page.type_into("login", "z" * 25)
    assert len(page.field("login").get_attribute("value")) == 20


@pytest.mark.parametrize("password,ok", [("1234567", False), ("12345678", True), ("р" * 8, True), ("a" * 128, True)],
                         ids=["7 символов", "8 символов", "8 русских букв", "128 символов"])
def test_r05_password_length(driver, server, password, ok):
    page, _ = register_ok(driver, server, password=password)
    if ok:
        page.wait_url_contains("/login")
    else:
        assert "password" in page.wait_errors()


def test_r06_password_field_stops_at_128_characters(driver, server):
    page = RegisterPage(driver, server).open("/register")
    page.type_into("password", "b" * 140)
    assert len(page.field("password").get_attribute("value")) == 128


@pytest.mark.parametrize("email", ["marine", "marine@", "@example.ru", "marine@example", "mar ine@example.ru", "marine@example.r"],
                         ids=["без собаки", "без домена", "без имени", "без точки", "пробел", "зона 1 буква"])
def test_r07_email_invalid(driver, server, email):
    page, _ = register_ok(driver, server, email=email)
    assert "email" in page.wait_errors()


@pytest.mark.parametrize("email", ["marine@example.ru", "m.k-1@sub.example.com"], ids=["обычная", "с точкой и поддоменом"])
def test_r08_email_valid(driver, server, email):
    page, _ = register_ok(driver, server, email=email)
    page.wait_url_contains("/login")


@pytest.mark.parametrize("phone", ["+79161234567", "89161234567", "+7 916 123-45-67"], ids=["+7", "8", "с пробелами и дефисами"])
def test_r09_phone_valid(driver, server, phone):
    page, _ = register_ok(driver, server, phone=phone)
    page.wait_url_contains("/login")


@pytest.mark.parametrize("phone", ["+7916123456", "+791612345678", "9161234567", "+49161234567", "телефон", ""],
                         ids=["10 цифр", "12 цифр", "без кода", "другая страна", "буквы", "пусто"])
def test_r10_phone_invalid(driver, server, phone):
    page, _ = register_ok(driver, server, phone=phone)
    assert "phone" in page.wait_errors()


def test_r11_full_name_too_short(driver, server):
    page, _ = register_ok(driver, server, full_name="Ли")
    assert "full_name" in page.wait_errors()


def test_r12_empty_form_shows_all_errors(driver, server):
    page = RegisterPage(driver, server).open("/register")
    page.submit()
    assert set(page.wait_errors()) == {"login", "full_name", "password", "email", "phone"}


def test_r13_duplicate_login(driver, server):
    name = unique("dup")
    first, _ = register_ok(driver, server, login=name)
    first.wait_url_contains("/login")
    second, _ = register_ok(driver, server, login=name)
    assert "занят" in second.wait_errors()["login"]


def test_r14_login_differing_only_in_case_is_a_duplicate(driver, server):
    name = unique("Case")
    first, _ = register_ok(driver, server, login=name)
    first.wait_url_contains("/login")
    second, _ = register_ok(driver, server, login=name.lower())
    assert "login" in second.wait_errors()


def test_r15_html_in_name_is_shown_as_text_in_admin_panel(driver, server):
    name = unique("xss")
    page, _ = register_ok(driver, server, login=name, full_name="<b>Жирный</b> Иванов")
    page.wait_url_contains("/login")
    LoginPage(driver, server).login(name, RegisterPage.DEFAULT["password"])
    driver.get(server + "/requests/new")
    Select(driver.find_element(By.NAME, "event_id")).select_by_index(1)
    Select(driver.find_element(By.NAME, "room")).select_by_index(1)
    Select(driver.find_element(By.NAME, "payment")).select_by_index(1)
    driver.find_element(By.CSS_SELECTOR, "main form button[type=submit]").click()
    WebDriverWait(driver, 6).until(EC.url_contains("/requests"))
    driver.find_element(By.CSS_SELECTOR, ".logout button").click()
    WebDriverWait(driver, 6).until(lambda d: d.find_elements(By.CSS_SELECTOR, ".menu a[href='/login']"))
    LoginPage(driver, server).login("admin", "Admin2026!")
    driver.get(server + "/admin/")
    assert "&lt;b&gt;" in driver.page_source
    assert not driver.find_elements(By.CSS_SELECTOR, ".req-card b")
