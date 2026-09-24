from unittest.mock import Mock

import zmq

from multivisor.multivisor import Supervisor


def test_reconnect_closes_stale_socket_without_lingering(monkeypatch):
    stale_client = Mock()
    replacement_client = Mock()
    client_factory = Mock(return_value=replacement_client)
    monkeypatch.setattr("multivisor.multivisor.zerorpc.Client", client_factory)

    supervisor = Supervisor.__new__(Supervisor)
    supervisor.address = "tcp://offline-supervisor:9002"
    supervisor.log = Mock()
    supervisor.server = stale_client

    supervisor.reconnect()

    stale_client._events._socket.setsockopt.assert_called_once_with(
        zmq.LINGER, 0
    )
    stale_client.close.assert_called_once_with()
    client_factory.assert_called_once_with(
        supervisor.address, timeout=5, heartbeat=5
    )
    assert supervisor.server is replacement_client
