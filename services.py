import platform, subprocess, os as ost
from getpass import getuser
from selenium.webdriver.chrome.service import Service as c_service
from selenium.webdriver.firefox.service import Service as f_service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from utils import choose

extensions: dict[str, str] = {"Windows": ".exe", "Linux": ""}
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
os: str = platform.system()


def chrome_service() -> tuple:
    """
    returns a tuple of chromedriver service and chrome default profile path on the host system
    """
    profile_path: str = profile_paths[os]["chrome"]
    if os == "Windows":
        subprocess.run("taskkill /f /im chrome.exe", shell=True)
        
    elif os == "Linux":
        subprocess.run("pkill -f 'chromium'", shell=True)
        
    else:
        print("Unsupported operating system")

    service = None
    if platform.machine().lower() in ('x86_64','amd64', 'x64'):
        driver_path = ChromeDriverManager().install()
        driver_root_path = '/'.join(driver_path.split('/')[:-3])
        driver_versions = ost.listdir(driver_root_path)
        driver_versions.sort(reverse=True)
        selected_driver_version = driver_versions[0]
        if len(driver_versions) > 1:
            selected_driver_version = choose(driver_versions, "Select the chrome version to use")
        service = c_service(f"{driver_root_path}/{selected_driver_version}/{'/'.join(driver_path.split('/')[-2:])}")

    else:
        print(f"your {platform.machine()} machine is not supported by webdriver manager please install chromedriver and provide it's path")
        service = c_service('/usr/local/bin/chromedriver')

    return service, profile_path


def firefox_service() -> tuple:
    """
    returns a tuple of firefox service and firefox default profile path on the host system
    """
    service = f_service(
        GeckoDriverManager().install()
    )
    profile_path = profile_paths[os]["firefox"]
    return service, profile_path
