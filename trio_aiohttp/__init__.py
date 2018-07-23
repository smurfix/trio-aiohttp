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

async def run_app(app, *, host=None, port=None, path=None, sock=None,
            shutdown_timeout=60.0, ssl_context=None,
            print=print, backlog=128, access_log_class=aiohttp.helpers.AccessLogger,
            access_log_format=aiohttp.helpers.AccessLogger.LOG_FORMAT,
            access_log=aiohttp.log.access_logger,
            reuse_address=None, reuse_port=None):
    """Run an app locally"""

    async with trio_asyncio.open_loop() as loop:

        if inspect.iscoroutine(app):
            app = await app

        runner = web.AppRunner(app, handle_signals=False,
                        access_log_class=access_log_class,
                        access_log_format=access_log_format,
                        access_log=access_log)

        await loop.run_asyncio(runner.setup)

        sites = []

        try:
            if host is not None:
                if isinstance(host, (str, bytes, bytearray, memoryview)):
                    sites.append(web.TCPSite(runner, host, port,
                                        shutdown_timeout=shutdown_timeout,
                                        ssl_context=ssl_context,
                                        backlog=backlog,
                                        reuse_address=reuse_address,
                                        reuse_port=reuse_port))
                else:
                    for h in host:
                        sites.append(web.TCPSite(runner, h, port,
                                            shutdown_timeout=shutdown_timeout,
                                            ssl_context=ssl_context,
                                            backlog=backlog,
                                            reuse_address=reuse_address,
                                            reuse_port=reuse_port))
            elif path is None and sock is None or port is not None:
                sites.append(web.TCPSite(runner, port=port,
                                    shutdown_timeout=shutdown_timeout,
                                    ssl_context=ssl_context, backlog=backlog,
                                    reuse_address=reuse_address,
                                    reuse_port=reuse_port))

            if path is not None:
                if isinstance(path, (str, bytes, bytearray, memoryview)):
                    sites.append(web.UnixSite(runner, path,
                                        shutdown_timeout=shutdown_timeout,
                                        ssl_context=ssl_context,
                                        backlog=backlog))
                else:
                    for p in path:
                        sites.append(web.UnixSite(runner, p,
                                            shutdown_timeout=shutdown_timeout,
                                            ssl_context=ssl_context,
                                            backlog=backlog))

            if sock is not None:
                if not isinstance(sock, Iterable):
                    sites.append(web.SockSite(runner, sock,
                                        shutdown_timeout=shutdown_timeout,
                                        ssl_context=ssl_context,
                                        backlog=backlog))
                else:
                    for s in sock:
                        sites.append(web.SockSite(runner, s,
                                            shutdown_timeout=shutdown_timeout,
                                            ssl_context=ssl_context,
                                            backlog=backlog))
            for site in sites:
                await loop.run_asyncio(site.start)
            if print:  # pragma: no branch
                names = sorted(str(s.name) for s in runner.sites)
                print("======== Running on {} ========\n"
                    "(Press CTRL+C to quit)".format(', '.join(names)))
            await trio.sleep(math.inf)
        finally:
            await loop.run_asyncio(runner.cleanup)
        if hasattr(loop, 'shutdown_asyncgens'):
            await loop.run_asyncio(loop.shutdown_asyncgens)


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

    trio.run(run_app,app)
