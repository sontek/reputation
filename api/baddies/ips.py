import ipaddress
import pytz
from datetime import datetime


def get_ipset_metadata(redis_client, key=None):
    # If we don't pass a key, return the list of keys
    if key is None:
        items = []
        keys = redis_client.keys(pattern="ip_set_metadata:*")
        for key in keys:
            metadata_key = key.decode('utf-8')
            result = redis_client.hgetall(metadata_key)
            items.append({
                "name": metadata_key.split(":")[-1],
                "date_last_modified": result[b'date_last_modified'].decode('utf-8')
            })
        return items
    else:
        metadata_key = f"ip_set_metadata:{key}"
        result = redis_client.hgetall(metadata_key)
        return result


def is_ip_blocked(redis_client, key, ip_address):
    addr = int(ipaddress.IPv4Address(ip_address))
    result = redis_client.zrangebyscore(
        f"ip_set:{key}",
        addr,
        '+inf',
        start=0,
        num=1,
        withscores=True,
    )
    if result:
        start = int(result[0][0].decode('utf-8'))
        end = int(result[0][1])

        if start <= addr and end >= addr:
            return True
        else:
            return False
    else:
        return False


def save_ipset(redis_client, key, file):
    lines_processed = 0

    file.seek(0)
    pipe = redis_client.pipeline()
    set_key = f"ip_set:{key}"
    pipe.delete(set_key)
    data = file.readlines()
    ranges = {}
    for line in data:
        line = line.decode('utf-8')
        if line.startswith("#"):
            continue

        ip = line.strip()

        if not ip:
            continue

        if '/' not in ip:
            addr = ipaddress.IPv4Address(ip)
            start = int(addr)
            end = start
        else:
            network = ipaddress.IPv4Network(ip)
            start = int(network[0])
            end = int(network[-1])

        lines_processed += 1
        ranges[f"{start}"] = end

    current_date = datetime.utcnow().replace(tzinfo=pytz.utc)
    metadata_key = f"ip_set_metadata:{key}"
    pipe.hset(metadata_key, mapping={
        "date_last_modified": current_date.isoformat()
    })
    pipe.zadd(set_key, ranges)
    pipe.execute()

    return {
        "lines_processed": lines_processed,
    }
