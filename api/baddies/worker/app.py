import os
import requests
import datetime
from dateutil.parser import parse as parsedate
from celery import Celery
from celery.schedules import crontab
from ..settings import get_settings
from ..redis import get_client
from ..ips import get_ipset_metadata

settings = get_settings()

API = settings.config['API_ORIGIN']
HOST = settings.config['REDIS_HOST']
PORT = settings.config['REDIS_PORT']
DB = settings.config['REDIS_DATABASE']


celery_app = Celery(
    'tasks',
    broker=f'redis://{HOST}:{PORT}/{DB}',
)


def update_file(file, url):
    response = requests.get(url)
    #with open(f'/tmp/{file}', 'wb') as f:
    response = requests.put(
        f"http://{API}/lists/{file}",
        files={
            "file": (
                "filename",
                response.content,
                "text",
            )
        }
    )
    print(response.json())


@celery_app.task
def download_file(file):
    r = get_client(
        HOST,
        PORT,
        DB,
    )
    url = f"https://iplists.firehol.org/files/{file}.netset"
    print(f"{file}: Checking server date...")
    response = requests.head(url)
    server_date = parsedate(response.headers['last-modified'])
    metadata = get_ipset_metadata(r, key=file)

    if not metadata:
        print(f"{file}: No metadata in Redis, updating now")
        update_file(file, url)
    else:
        print(f"{file}: Server Last modified {server_date}...")
        redis_date = parsedate(
            metadata[b'date_last_modified'].decode('utf-8')
        )
        print(f"{file}: Redis Last modified {redis_date}...")
        if redis_date < server_date:
            print(
                f"{file}: Redis date is earlier than server date, updating..."
            )
            update_file(file, url)
        else:
            print(f"{file}: We have the latest, not updating")


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        60.0,
        download_file.s('firehol_level1'),
        name='Download firehol_level1'
    )

    sender.add_periodic_task(
        60.0,
        download_file.s('firehol_level2'),
        name='Download firehol_level2'
    )

    sender.add_periodic_task(
        60.0,
        download_file.s('firehol_level3'),
        name='Download firehol_level3'
    )

    sender.add_periodic_task(
        60.0,
        download_file.s('firehol_level4'),
        name='Download firehol_level4'
    )

    sender.add_periodic_task(
        60.0,
        download_file.s('firehol_webserver'),
        name='Download firehol_webserver'
    )
