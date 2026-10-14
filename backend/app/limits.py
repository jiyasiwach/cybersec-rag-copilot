"""Shared rate limiter (own module so routers can import it without a circular import)."""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
