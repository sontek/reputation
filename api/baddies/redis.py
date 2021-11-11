import redis
from functools import lru_cache

redis_client = None


@lru_cache()
def get_client(host, port, db=0):
    r = redis.Redis(
        host=host,
        port=port,
        db=db,
    )
    return r
