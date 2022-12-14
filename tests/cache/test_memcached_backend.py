import os
import ssl
from threading import Thread
import time
from unittest import mock
from unittest import TestCase
import weakref

import pytest

from dogpile.cache import make_region
from dogpile.cache.backends.memcached import GenericMemcachedBackend
from dogpile.cache.backends.memcached import MemcachedBackend
from dogpile.cache.backends.memcached import PylibmcBackend
from . import eq_
from ._fixtures import _GenericBackendTest
from ._fixtures import _GenericMutexTest
from ._fixtures import _GenericSerializerTest


MEMCACHED_PORT = os.getenv("DOGPILE_MEMCACHED_PORT", "11211")
MEMCACHED_URL = "127.0.0.1:%s" % MEMCACHED_PORT
expect_memcached_running = bool(os.getenv("DOGPILE_MEMCACHED_PORT"))

TLS_CONTEXT = ssl.create_default_context(cafile="tests/tls/ca-root.crt")
TLS_MEMCACHED_PORT = os.getenv("DOGPILE_TLS_MEMCACHED_PORT", "11212")
TLS_MEMCACHED_URL = "localhost:%s" % TLS_MEMCACHED_PORT
expect_tls_memcached_running = bool(os.getenv("DOGPILE_TLS_MEMCACHED_PORT"))

LOCK_TIMEOUT = 1


class _TestMemcachedConn(object):
    @classmethod
    def _check_backend_available(cls, backend):
        try:
            client = backend._create_client()
            client.set("x", "y")
            assert client.get("x") == "y"
        except Exception:
            if not expect_memcached_running:
                pytest.skip(
                    "memcached is not running or "
                    "otherwise not functioning correctly"
                )
            else:
                raise


class _TestTLSMemcachedConn(object):
    @classmethod
    def _check_backend_available(cls, backend):
        try:
            client = backend._create_client()
            client.set("x", "y")
            assert client.get("x") == "y"
        except Exception:
            if not expect_tls_memcached_running:
                pytest.skip(
                    "TLS memcached is not running or "
                    "otherwise not functioning correctly"
                )
            else:
                raise


class _NonDistributedMemcachedTest(_TestMemcachedConn, _GenericBackendTest):
    region_args = {"key_mangler": lambda x: x.replace(" ", "_")}
    config_args = {"arguments": {"url": MEMCACHED_URL}}


class _NonDistributedTLSMemcachedTest(
    _TestTLSMemcachedConn, _GenericBackendTest
):
    region_args = {"key_mangler": lambda x: x.replace(" ", "_")}
    config_args = {
        "arguments": {"url": TLS_MEMCACHED_URL, "tls_context": TLS_CONTEXT}
    }


class _DistributedMemcachedWithTimeoutTest(
    _TestMemcachedConn, _GenericBackendTest
):
    region_args = {"key_mangler": lambda x: x.replace(" ", "_")}
    config_args = {
        "arguments": {
            "url": MEMCACHED_URL,
            "distributed_lock": True,
            "lock_timeout": LOCK_TIMEOUT,
        }
    }


class _DistributedMemcachedTest(_TestMemcachedConn, _GenericBackendTest):
    region_args = {"key_mangler": lambda x: x.replace(" ", "_")}
    config_args = {
        "arguments": {"url": MEMCACHED_URL, "distributed_lock": True}
    }


class _DistributedMemcachedMutexTest(_TestMemcachedConn, _GenericMutexTest):
    config_args = {
        "arguments": {"url": MEMCACHED_URL, "distributed_lock": True}
    }


class _DistributedMemcachedMutexWithTimeoutTest(
    _TestMemcachedConn, _GenericMutexTest
):
    config_args = {
        "arguments": {
            "url": MEMCACHED_URL,
            "distributed_lock": True,
            "lock_timeout": LOCK_TIMEOUT,
        }
    }


class PylibmcTest(_NonDistributedMemcachedTest):
    backend = "dogpile.cache.pylibmc"


class PylibmcDistributedTest(_DistributedMemcachedTest):
    backend = "dogpile.cache.pylibmc"


class PylibmcDistributedMutexTest(_DistributedMemcachedMutexTest):
    backend = "dogpile.cache.pylibmc"


class PylibmcSerializerTest(
    _GenericSerializerTest, _NonDistributedMemcachedTest
):
    backend = "dogpile.cache.pylibmc"


class BMemcachedTest(_NonDistributedMemcachedTest):
    backend = "dogpile.cache.bmemcached"


class BMemcachedDistributedWithTimeoutTest(
    _DistributedMemcachedWithTimeoutTest
):
    backend = "dogpile.cache.bmemcached"


class BMemcachedTLSTest(_NonDistributedTLSMemcachedTest):
    backend = "dogpile.cache.bmemcached"


class BMemcachedDistributedTest(_DistributedMemcachedTest):
    backend = "dogpile.cache.bmemcached"


class BMemcachedDistributedMutexTest(_DistributedMemcachedMutexTest):
    backend = "dogpile.cache.bmemcached"


class BMemcachedDistributedMutexWithTimeoutTest(
    _DistributedMemcachedMutexWithTimeoutTest
):
    backend = "dogpile.cache.bmemcached"


class BMemcachedSerializerTest(
    _GenericSerializerTest, _NonDistributedMemcachedTest
):
    backend = "dogpile.cache.bmemcached"


class PyMemcacheTest(_NonDistributedMemcachedTest):
    backend = "dogpile.cache.pymemcache"

    def test_pymemcache_enable_retry_client_not_set(self):
        with mock.patch("warnings.warn") as warn_mock:
            _ = make_region().configure(
                "dogpile.cache.pymemcache",
                arguments={"url": "foo", "retry_attempts": 2},
            )
            eq_(
                warn_mock.mock_calls[0],
                mock.call(
                    "enable_retry_client is not set; retry options "
                    "will be ignored"
                ),
            )


class PyMemcacheDistributedWithTimeoutTest(
    _DistributedMemcachedWithTimeoutTest
):
    backend = "dogpile.cache.pymemcache"


class PyMemcacheTLSTest(_NonDistributedTLSMemcachedTest):
    backend = "dogpile.cache.pymemcache"


class PyMemcacheDistributedTest(_DistributedMemcachedTest):
    backend = "dogpile.cache.pymemcache"


class PyMemcacheDistributedMutexTest(_DistributedMemcachedMutexTest):
    backend = "dogpile.cache.pymemcache"


class PyMemcacheDistributedMutexWithTimeoutTest(
    _DistributedMemcachedMutexWithTimeoutTest
):
    backend = "dogpile.cache.pymemcache"


class PyMemcacheSerializerTest(
    _GenericSerializerTest, _NonDistributedMemcachedTest
):
    backend = "dogpile.cache.pymemcache"


class PyMemcacheRetryTest(_NonDistributedMemcachedTest):
    backend = "dogpile.cache.pymemcache"
    config_args = {
        "arguments": {
            "url": MEMCACHED_URL,
            "enable_retry_client": True,
            "retry_attempts": 3,
        }
    }


class MemcachedTest(_NonDistributedMemcachedTest):
    backend = "dogpile.cache.memcached"


class MemcachedDistributedTest(_DistributedMemcachedTest):
    backend = "dogpile.cache.memcached"


class MemcachedDistributedMutexTest(_DistributedMemcachedMutexTest):
    backend = "dogpile.cache.memcached"


class MemcachedSerializerTest(
    _GenericSerializerTest, _NonDistributedMemcachedTest
):
    backend = "dogpile.cache.pylibmc"


class MockGenericMemcachedBackend(GenericMemcachedBackend):
    def _imports(self):
        pass

    def _create_client(self):
        return MockClient(self.url)


class MockMemcacheBackend(MemcachedBackend):
    def _imports(self):
        pass

    def _create_client(self):
        return MockClient(self.url)


class MockPylibmcBackend(PylibmcBackend):
    def _imports(self):
        pass

    def _create_client(self):
        return MockClient(
            self.url, binary=self.binary, behaviors=self.behaviors
        )


class MockClient(object):
    clients = set()

    def __init__(self, *arg, **kw):
        self.arg = arg
        self.kw = kw
        self.canary = []
        self._cache = {}
        self.clients.add(weakref.ref(self, MockClient._remove))

    @classmethod
    def _remove(cls, ref):
        cls.clients.remove(ref)

    @classmethod
    def number_of_clients(cls):
        return len(cls.clients)

    def get(self, key):
        return self._cache.get(key)

    def set(self, key, value, **kw):
        self.canary.append(kw)
        self._cache[key] = value

    def delete(self, key):
        self._cache.pop(key, None)


class PylibmcArgsTest(TestCase):
    def test_binary_flag(self):
        backend = MockPylibmcBackend(arguments={"url": "foo", "binary": True})
        eq_(backend._create_client().kw["binary"], True)

    def test_url_list(self):
        backend = MockPylibmcBackend(arguments={"url": ["a", "b", "c"]})
        eq_(backend._create_client().arg[0], ["a", "b", "c"])

    def test_url_scalar(self):
        backend = MockPylibmcBackend(arguments={"url": "foo"})
        eq_(backend._create_client().arg[0], ["foo"])

    def test_behaviors(self):
        backend = MockPylibmcBackend(
            arguments={"url": "foo", "behaviors": {"q": "p"}}
        )
        eq_(backend._create_client().kw["behaviors"], {"q": "p"})

    def test_set_time(self):
        backend = MockPylibmcBackend(
            arguments={"url": "foo", "memcached_expire_time": 20}
        )
        backend.set("foo", "bar")
        eq_(backend._clients.memcached.canary, [{"time": 20}])

    def test_set_min_compress_len(self):
        backend = MockPylibmcBackend(
            arguments={"url": "foo", "min_compress_len": 20}
        )
        backend.set("foo", "bar")
        eq_(backend._clients.memcached.canary, [{"min_compress_len": 20}])

    def test_no_set_args(self):
        backend = MockPylibmcBackend(arguments={"url": "foo"})
        backend.set("foo", "bar")
        eq_(backend._clients.memcached.canary, [{}])


class MemcachedArgstest(TestCase):
    def test_set_time(self):
        backend = MockMemcacheBackend(
            arguments={"url": "foo", "memcached_expire_time": 20}
        )
        backend.set("foo", "bar")
        eq_(backend._clients.memcached.canary, [{"time": 20}])

    def test_set_min_compress_len(self):
        backend = MockMemcacheBackend(
            arguments={"url": "foo", "min_compress_len": 20}
        )
        backend.set("foo", "bar")
        eq_(backend._clients.memcached.canary, [{"min_compress_len": 20}])


class LocalThreadTest(TestCase):
    def setUp(self):
        import gc

        gc.collect()
        eq_(MockClient.number_of_clients(), 0)

    def test_client_cleanup_1(self):
        self._test_client_cleanup(1)

    def test_client_cleanup_3(self):
        self._test_client_cleanup(3)

    def test_client_cleanup_10(self):
        self._test_client_cleanup(10)

    def _test_client_cleanup(self, count):
        backend = MockGenericMemcachedBackend(arguments={"url": "foo"})
        canary = []

        flag = [False]

        def f(delay):
            backend._clients.memcached
            canary.append(MockClient.number_of_clients())
            while not flag[0]:
                time.sleep(0.02)

        threads = [Thread(target=f, args=(count - i,)) for i in range(count)]
        for t in threads:
            t.start()
        flag[0] = True
        for t in threads:
            t.join()
        eq_(canary, [i + 1 for i in range(count)])

        import gc

        gc.collect()
        eq_(MockClient.number_of_clients(), 0)
