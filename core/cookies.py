from django.conf import settings

def set_access_cookie(response, token:str):
    response.set_cookie(
        key = settings.AUTH_COOKIE_ACCESS,
        value = token,
        httponly = True,
        secure = settings.AUTH_COOKIE_SECURE,
        samesite = settings.AUTH_COOKIE_SAMESITE,
        path="/"
    )

def set_refresh_cookie(response, token:str):
    response.set_cookie(
        key = settings.AUTH_COOKIE_REFRESH,
        value = token,
        httponly = True,
        secure = settings.AUTH_COOKIE_SECURE,
        samesite = settings.AUTH_COOKIE_SAMESITE,
        path = "/"
    )


def clear_auth_cookies(response):
    response.delete_cookie(settings.AUTH_COOKIE_ACCESS, path="/")
    response.delete_cookie(settings.AUTH_COOKIE_REFRESH, path="/")