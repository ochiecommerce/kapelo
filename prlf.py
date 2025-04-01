from session_utils import Session
from drivers import chrome
from args import args

profiles: list[str] = []

if args.p:
    for profile in args.p:
        profiles.append(f'Profile {profile}')

else:
    profiles = ['Profile 1']

def sessions():
    for profile in profiles:
        driver = chrome(profile)
        session = Session(
            driver, "https://timebucks.com/publishers/index.php?pg=earn&tab=tasks_tasks"
        )
        yield session
