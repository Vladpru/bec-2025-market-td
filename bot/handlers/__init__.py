from . import start
from . import registration, about_event, main_menu

def setup_routers(dp):
    dp.include_routers(
        start.router,
        registration.router,
        about_event.router,
        main_menu.router,
    )