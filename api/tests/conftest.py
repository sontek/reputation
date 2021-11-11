import mock
import os
import pytest
import redis
from fastapi.testclient import TestClient

from baddies.server import app


@pytest.fixture(autouse=True)
def mock_settings_env_vars(redis_url):
    with mock.patch.dict(
        os.environ,
        {
            "REDIS_HOST": redis_url[0],
            "REDIS_PORT": str(redis_url[1]),
        }
    ):
        yield


def is_redis_responsive(ip, port):
    try:
        r = redis.Redis(
            host=ip,
            port=port,
            db=0,
        )
        r.set('ping', 'pong')
        return r.get('ping') == b'pong'
    except redis.exceptions.ConnectionError:
        return False


@pytest.fixture(scope="session")
def redis_url(docker_ip, docker_services):
    """Ensure that HTTP service is up and responsive."""
    # `port_for` takes a container port and returns the
    # corresponding host port
    port = docker_services.port_for("redis", 6379)
    # bug in pytest-docker hack for now
    docker_ip = os.environ.get('DOCKER_HOST_OVERRIDE', None) or docker_ip

    information = (docker_ip, port)
    docker_services.wait_until_responsive(
        timeout=30.0,
        pause=0.1,
        check=lambda: is_redis_responsive(*information)
    )
    return information


@pytest.fixture
def api_client():
    client = TestClient(app)
    return client
