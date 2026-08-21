from contextlib import suppress

from gevent import Timeout
import zerorpc


def test_eventlistener_rpc_round_trip(supervisor_eventlistener):
    info = supervisor_eventlistener.read_info()

    assert info["running"]
    assert info["identification"] == "supervisor"
    assert info["supervisor_version"]


def test_eventlistener_forwards_process_events(supervisor_eventlistener):
    stream_client = zerorpc.Client(supervisor_eventlistener.address)
    command_client = zerorpc.Client(supervisor_eventlistener.address)
    events = stream_client.event_stream()

    try:
        with Timeout(10):
            assert next(events) == "First event to trigger connection. Please ignore me!"
            assert command_client.startProcess("event_probe", False)

            for event in events:
                if event["eventname"] == "PROCESS_STATE_RUNNING":
                    break
            else:
                raise AssertionError("event stream ended before PROCESS_STATE_RUNNING")

        assert event["payload"]["groupname"] == "event_probe"
        assert event["payload"]["processname"] == "event_probe"
        assert event["payload"]["process"]["statename"] == "RUNNING"
    finally:
        with suppress(Exception):
            command_client.stopProcess("event_probe", True)
        command_client.close()
        stream_client.close()
