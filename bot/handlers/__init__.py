from . import start

def setup_routers(dp):
    dp.include_routers(
        start.router,
    )