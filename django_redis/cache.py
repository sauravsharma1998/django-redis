import functools
import warnings
import logging

from django.conf import settings
from django.core.cache.backends.base import BaseCache

from .util import load_class
from .exceptions import ConnectionInterrupted

django_redis_settings = getattr(settings, "CACHES", {})
if "OPTIONS" in django_redis_settings.get('default'):
    log_ignored_exceptions = django_redis_settings['default']['OPTIONS'].get('LOG_IGNORED_EXCEPTIONS')
    if log_ignored_exceptions == True:
        logger = logging.getLogger(django_redis_settings['default']['OPTIONS'].get('LOGGER', __name__))


DJANGO_REDIS_IGNORE_EXCEPTIONS = getattr(settings, "DJANGO_REDIS_IGNORE_EXCEPTIONS", False)
DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS = getattr(settings, "DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS", False)


def omit_exception(method):
    """
    Simple decorator that intercepts connection
    errors and ignores these if settings specify this.

    Note: this doesn't handle the `default` argument in .get().
    """

    @functools.wraps(method)
    def _decorator(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except ConnectionInterrupted as e:
            if self._ignore_exceptions or DJANGO_REDIS_IGNORE_EXCEPTIONS:

                if self._log_ignored_exceptions:
                    logger.error(str(e))

                #return default or None
                return kwargs.get('default', None)

            raise e.parent

    return _decorator


class RedisCache(BaseCache):
    def __init__(self, server, params):
        super(RedisCache, self).__init__(params)
        self._server = server
        self._params = params

        options = params.get("OPTIONS", {})
        self._client_cls = options.get("CLIENT_CLASS", "django_redis.client.DefaultClient")
        self._client_cls = load_class(self._client_cls)
        self._client = None

        self._ignore_exceptions = options.get("IGNORE_EXCEPTIONS", DJANGO_REDIS_IGNORE_EXCEPTIONS)
        self._log_ignored_exceptions = options.get("LOG_IGNORED_EXCEPTIONS", DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS)

    @property
    def client(self):
        """
        Lazy client connection property.
        """
        if self._client is None:
            self._client = self._client_cls(self._server, self._params, self)
        return self._client

    @omit_exception
    def set(self, *args, **kwargs):
        return self.client.set(*args, **kwargs)

    @omit_exception
    def incr_version(self, *args, **kwargs):
        return self.client.incr_version(*args, **kwargs)

    @omit_exception
    def add(self, *args, **kwargs):
        return self.client.add(*args, **kwargs)

    @omit_exception
    def get(self, key, default=None, version=None, client=None):
        return self.client.get(key, default=default, version=version,
                               client=client)

    @omit_exception
    def delete(self, *args, **kwargs):
        return self.client.delete(*args, **kwargs)

    @omit_exception
    def delete_pattern(self, *args, **kwargs):
        return self.client.delete_pattern(*args, **kwargs)

    @omit_exception
    def delete_many(self, *args, **kwargs):
        return self.client.delete_many(*args, **kwargs)

    @omit_exception
    def clear(self):
        return self.client.clear()

    @omit_exception
    def get_many(self, *args, **kwargs):
        return self.client.get_many(*args, **kwargs)

    @omit_exception
    def set_many(self, *args, **kwargs):
        return self.client.set_many(*args, **kwargs)

    @omit_exception
    def incr(self, *args, **kwargs):
        return self.client.incr(*args, **kwargs)

    @omit_exception
    def decr(self, *args, **kwargs):
        return self.client.decr(*args, **kwargs)

    @omit_exception
    def has_key(self, *args, **kwargs):
        return self.client.has_key(*args, **kwargs)

    @omit_exception
    def keys(self, *args, **kwargs):
        return self.client.keys(*args, **kwargs)

    @omit_exception
    def iter_keys(self, *args, **kwargs):
        return self.client.iter_keys(*args, **kwargs)

    @omit_exception
    def ttl(self, *args, **kwargs):
        return self.client.ttl(*args, **kwargs)

    @omit_exception
    def persist(self, *args, **kwargs):
        return self.client.persist(*args, **kwargs)

    @omit_exception
    def expire(self, *args, **kwargs):
        return self.client.expire(*args, **kwargs)

    @omit_exception
    def lock(self, *args, **kwargs):
        return self.client.lock(*args, **kwargs)

    @omit_exception
    def close(self, **kwargs):
        self.client.close(**kwargs)
