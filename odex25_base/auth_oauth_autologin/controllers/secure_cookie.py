from werkzeug.wrappers import Response

_original_set_cookie = Response.set_cookie

# #  - 1.3.14 : Cookie without SECURE Flag
# #  - 1.3.10 : Cookie Configuration


def patched_set_cookie(
        self, key, value="", max_age=None, expires=None, path="/", domain=None,
        secure=None, httponly=False, samesite=None):
    # Force Secure, HttpOnly, and SameSite=Lax for all cookies
    secure = True  # Enforce Secure flag
    httponly = True  # Enforce HttpOnly flag
    samesite = samesite or 'Lax'  # Default to Lax

    return _original_set_cookie(
        self, key, value=value, max_age=max_age, expires=expires,
        path=path, domain=domain, secure=secure, httponly=httponly, samesite=samesite)


Response.set_cookie = patched_set_cookie