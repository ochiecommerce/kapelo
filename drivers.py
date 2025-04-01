from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium_stealth import stealth
from getpass import getuser
from services import firefox_service, chrome_service

profile_paths: dict[str, dict[str, str]] = {
    "Windows": {
        "chrome": f"C:/Users/{getuser()}/AppData/Local/Google/Chrome/User Data",
        "firefox": f"C:/Users/{getuser()}/AppData/Roaming/Mozilla/Firefox/Profiles/vqpj2t2v.default-release",
    },
    "Linux": {
        "chrome": f"/home/{getuser()}/.config/chromium",
        "firefox": f"/home/{getuser()}/snap/firefox/common/.mozilla/firefox/8af5cbkt.ochiecommerce",
    },
}

def hide(driver):
    """hide a driver from being detected by automation detectors"""
    stealth(
        driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Linux",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    return driver


def chrome(profile="Profile 1") -> webdriver.Chrome:
    """
    returns chrome created with the default chrome profile on the host system.
    The driver is modified to ensure that it is not detected by the javascript running on chrome
    """
    
    service, profile_path = chrome_service()
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"user-data-dir={profile_path}")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(f"--profile-directory={profile}")
    driver = webdriver.Chrome(options=options, service=service)
    return hide(driver)
 
    


def firefox() -> webdriver.Firefox:
    """
    returns a firefox driver created with the default firefox profile on the host system
    """
    service, profile_path = firefox_service()
    # profile = webdriver.FirefoxProfile()#profile_path)
    # profile.set_preference("dom.webdriver.enabled", False)
    # profile.set_preference("media.autoplay.default", 0)
    # profile.set_preference("media.block-autoplay-until-in-foreground", False)
    # profile.set_preference("useAutomationExtension", False)
    # profile.set_preference("browser.link.open_newwindow", 3)
    # profile.set_preference("media.navigator.enabled", False)
    # profile.update_preferences()
    options = FirefoxOptions()
    #options.profile = profile
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Firefox(service=service)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return hide(driver)


def safari():
    options = webdriver.SafariOptions()
    driver = webdriver.Safari(options=options)
    return hide(driver)


def edge():
    options = webdriver.EdgeOptions()
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("start-maximized")
    # options.add_argument(r'--profile-directory=Profile 3')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    # options.add_argument(f'user-data-dir={profile_path}')
    driver = webdriver.Edge(options=options)
    # driver.execute_cdp_cmd('Network.setUserAgentOverride',{'userAgent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'})
    return hide(driver)
    return 


def ie():
    options = webdriver.IeOptions()
    driver = webdriver.Ie(options=options)
    return hide(driver)
