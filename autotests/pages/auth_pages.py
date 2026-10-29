from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    def __init__(self, driver, base):
        self.driver = driver
        self.base = base
        self.wait = WebDriverWait(driver, 6)

    def open(self, path):
        self.driver.get(self.base + path)
        return self

    def field(self, name):
        return self.driver.find_element(By.NAME, name)

    def type_into(self, name, value):
        el = self.field(name)
        el.clear()
        if value:
            el.send_keys(value)

    def submit(self):
        self.driver.find_element(By.CSS_SELECTOR, "main form button[type=submit]").click()

    def errors(self):
        return {
            e.find_element(By.XPATH, "./ancestor::label//input").get_attribute("name"): e.text
            for e in self.driver.find_elements(By.CSS_SELECTOR, "label .err")
            if e.text
        }

    def wait_result(self, here):
        """ждём, пока страница либо сменится, либо покажет ошибку"""
        self.wait.until(lambda d: here not in d.current_url or d.find_elements(By.CSS_SELECTOR, "main .err"))

    def wait_url_contains(self, part):
        self.wait.until(EC.url_contains(part))

    def wait_errors(self):
        self.wait.until(lambda d: self.errors())
        return self.errors()


class RegisterPage(BasePage):
    DEFAULT = {
        "login": "marina_k",
        "full_name": "Хачатрян Марине Артаковна",
        "password": "Parol2026",
        "email": "marine@example.ru",
        "phone": "+79161234567",
    }

    def register(self, **values):
        data = dict(self.DEFAULT, **values)
        self.open("/register")
        for name, value in data.items():
            self.type_into(name, value)
        self.submit()
        self.wait_result("/register")


class LoginPage(BasePage):
    def login(self, login, password):
        self.open("/login")
        self.type_into("login", login)
        self.type_into("password", password)
        self.submit()
        self.wait_result("/login")

    def message(self):
        return self.driver.find_element(By.CSS_SELECTOR, "main .err").text
