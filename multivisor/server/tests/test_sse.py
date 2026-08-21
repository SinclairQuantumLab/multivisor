from types import SimpleNamespace

from multivisor.server import web


class StubDispatcher:
    def __init__(self):
        self.clients = []

    def add_listener(self, client):
        self.clients.append(client)

    def remove_listener(self, client):
        self.clients.remove(client)


def test_sse_stream_sends_heartbeats_events_and_removes_listener():
    dispatcher = StubDispatcher()
    events = web.iter_sse_events(dispatcher, heartbeat_interval=0.001)

    assert next(events) == web.SSE_HEARTBEAT
    assert len(dispatcher.clients) == 1

    assert next(events) == web.SSE_HEARTBEAT

    event = 'data: {"event": "PROCESS_STATE_RUNNING"}\n\n'
    dispatcher.clients[0].put(event)
    assert next(events) == event

    events.close()
    assert dispatcher.clients == []


def test_sse_response_disables_caching_and_nginx_buffering(monkeypatch):
    dispatcher = StubDispatcher()
    monkeypatch.setattr(web.app, "dispatcher", dispatcher, raising=False)
    monkeypatch.setattr(
        web.app,
        "multivisor",
        SimpleNamespace(use_authentication=False),
        raising=False,
    )

    with web.app.test_client() as client:
        response = client.get("/api/stream", buffered=False)
        try:
            assert response.status_code == 200
            assert response.mimetype == "text/event-stream"
            assert response.headers["Cache-Control"] == "no-cache"
            assert response.headers["X-Accel-Buffering"] == "no"
            assert next(response.response) == web.SSE_HEARTBEAT.encode()
        finally:
            response.close()

    assert dispatcher.clients == []
