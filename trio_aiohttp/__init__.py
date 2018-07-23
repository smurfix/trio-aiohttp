#!/usr/bin/python3
"""Top-level package for trio-aiohttp."""

import trio
import trio_asyncio
import aiohttp
from aiohttp import web, hdrs
import math
import inspect
import json

from functools import partial

#from ._version import __version__

class _WebSocketResponse:
    """A websocket with a Trio-based public interface"""
    def __init__(self, *args, **kw):
        self._wsr = web.WebSocketResponse(*args, **kw)

    async def send_str(self, data, compress=None):
        await trio_asyncio.run_asyncio(partial(self._wsr.send_str, data, compress=compress))

    async def send_bytes(self, data, compress=None):
        await trio_asyncio.run_asyncio(partial(self._wsr.send_bytes, data, compress=compress))

    async def send_json(self, *a, **k):
        await trio_asyncio.run_asyncio(partial(self._wsr.send_json, *a,**k))

    async def close(self, *a, **k):
        await trio_asyncio.run_asyncio(partial(self._wsr.close, *a, **k))

    def __aiter__(self):
        return trio_asyncio.run_iterator(self._wsr)


async def _aio_ws_handler(request, handler):
    # asyncio!
    ws = _WebSocketResponse()
    await ws._wsr.prepare(request)
    try:
        await handler(ws)
    finally:
        await ws._wsr.close()
    return ws._wsr

def websocket(path, handler, **kwargs):
    handler = trio_asyncio.aio2trio(handler)
    return web.RouteDef(hdrs.METH_GET, path, lambda r:_aio_ws_handler(r, handler), kwargs)

def route(method, path, handler, **kwargs):
    return web.RouteDef(method, path, trio_asyncio.aio2trio(handler), kwargs)

def head(path, handler, **kwargs):
    return route(hdrs.METH_HEAD, path, handler, **kwargs)

def get(path, handler, *, name=None, allow_head=True, **kwargs):
    return route(hdrs.METH_GET, path, handler, name=name,
                 allow_head=allow_head, **kwargs)

def post(path, handler, **kwargs):
    return route(hdrs.METH_POST, path, handler, **kwargs)

def put(path, handler, **kwargs):
    return route(hdrs.METH_PUT, path, handler, **kwargs)

def patch(path, handler, **kwargs):
    return route(hdrs.METH_PATCH, path, handler, **kwargs)

def delete(path, handler, **kwargs):
    return route(hdrs.METH_DELETE, path, handler, **kwargs)

def view(path, handler, **kwargs):
    return route(hdrs.METH_ANY, path, handler, **kwargs)

if __name__ == "__main__":
    # sample code exercising some of what we have so far
    async def handle(request):
        name = request.match_info.get('name', "Anonymous")
        text = "Hello, " + name
        await trio.sleep(1)
        return web.Response(text=text)

    async def work(ws):
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    msg = json.loads(msg.data)
                except Exception as exc:
                    msg = dict(str=msg.data,exc=str(exc))
                await ws.send_json(dict(got=msg))
            elif msg.type in {aiohttp.WSMsgType.CLOSED,aiohttp.WSMsgType.CLOSING}:
                break
            else:
                await ws.send_json(dict(got=str(msg)))

    app = web.Application()
    app.add_routes([get('/', handle),
                    websocket('/_ws', work),
                    get('/{name}', handle),
                    ])

    async def main():
        async with trio_asyncio.open_loop():
            runner = web.AppRunner(app)
            await trio_asyncio.run_asyncio(runner.setup)
            site = web.TCPSite(runner, 'localhost', 8080)
            await trio_asyncio.run_asyncio(site.start)
            await trio.sleep(math.inf)

    trio.run(main)

