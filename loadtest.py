import molotov
import os
import random
import uuid
from urllib.parse import urljoin
import aiohttp


SERVER_URL = 'http://127.0.0.1:8888/v1/'
AUTH = aiohttp.BasicAuth("user", "pass")


def build_task():
    suffix = str(uuid.uuid4())
    data = {"description": "Task description {0}".format(suffix),
            "status": random.choice(("todo", "doing")),}
    return data


@molotov.scenario()
async def test_kinto(session):
    collection_id = 'tasks-%s' % uuid.uuid4()
    collection_url = urljoin(SERVER_URL, '/buckets/default/collections/{}/records'.format(collection_id))
    task = build_task()

    async with session.get(SERVER_URL) as resp:
        res = await resp.json()

    async with session.post(collection_url, json={"data": task}, auth=AUTH) as resp:
        res = await resp.json()
