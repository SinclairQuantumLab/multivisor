"""Stable Supervisor protocol constants used by the Multivisor web process.

The web process talks to Supervisor through ZeroRPC and only needs these wire
values. Keeping them local avoids installing the platform-specific Supervisor
runtime into an otherwise independent web/CLI environment.
"""

# Supervisor 4.x XML-RPC fault code for an operation that failed.
FAULT_FAILED = 30

# Supervisor 4.x process states treated as active by Multivisor:
# STARTING=10, RUNNING=20, BACKOFF=30.
RUNNING_STATES = frozenset({10, 20, 30})
