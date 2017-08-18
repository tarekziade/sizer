import molotov


@molotov.scenario()
async def test_kinto(session):
    async with session.get('http://127.0.0.1:8888/v1/') as resp:
        await resp.json()
