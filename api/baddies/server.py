from fastapi import (
    FastAPI,
    File,
    UploadFile,
    Header,
    Depends,
)
from fastapi.middleware.cors import CORSMiddleware
from .settings import Settings, get_settings
from .redis import get_client
from .ips import save_ipset, is_ip_blocked, get_ipset_metadata

app = FastAPI()

# TODO: figure out how to load this lazily...
# origins = [f"http://{settings.Config.API_ORIGIN}"]
origins = []

# limit file uploads to 50mb
MAX_SIZE: int = 50 * 1_024 ** 2

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def valid_content_length(
    content_length: int = Header(..., lt=MAX_SIZE)
):
    return content_length


@app.put("/lists/{key}")
async def create_file(
    key: str,
    file: UploadFile = File(...),
    file_size: int = Depends(valid_content_length),
    settings: Settings = Depends(get_settings),
):
    r = get_client(
        settings.config['REDIS_HOST'],
        settings.config['REDIS_PORT'],
        settings.config['REDIS_DATABASE'],
    )
    result = save_ipset(r, key, file.file)
    return result


@app.get("/lists")
async def get(
    settings: Settings = Depends(get_settings),
):
    r = get_client(
        settings.config['REDIS_HOST'],
        settings.config['REDIS_PORT'],
        settings.config['REDIS_DATABASE'],
    )
    data = get_ipset_metadata(r)
    return data


@app.get("/verify")
async def verify(
    lists: str,
    ip_address: str,
    settings: Settings = Depends(get_settings),
):
    r = get_client(
        settings.config['REDIS_HOST'],
        settings.config['REDIS_PORT'],
    )
    for key in lists.split(","):
        result = is_ip_blocked(
            r,
            key,
            ip_address,
        )
        if result:
            return {
                "is_bad": True,
                "reason": key,
            }

    return {
        'is_bad': False,
    }
