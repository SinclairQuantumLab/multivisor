from multivisor.supervisor_protocol import FAULT_FAILED, RUNNING_STATES


def test_supervisor_protocol_constants_match_supervisor_4():
    assert FAULT_FAILED == 30
    assert RUNNING_STATES == {10, 20, 30}
