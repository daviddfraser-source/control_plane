#!/usr/bin/env python3
"""
SSE (Server-Sent Events) implementation for wbs_server.py
ORCH-005: Add SSE endpoint for real-time dashboard updates

This file contains the code that needs to be integrated into wbs_server.py.
"""

import json
import threading
import time
from typing import List, Dict

# ============================================================================
# STEP 1: Add these globals after line 50 (after TERMINAL_LOG declaration)
# ============================================================================

SSE_CLIENTS: List = []
SSE_HEARTBEAT_INTERVAL = 30  # seconds
SSE_LOCK = threading.Lock()


def broadcast_sse_event(event_type: str, data: dict):
    """
    Broadcast state change event to all connected SSE clients.

    Args:
        event_type: Event type (e.g., "state_change", "packet_claimed", "packet_done")
        data: Event payload as dictionary

    Usage:
        broadcast_sse_event("packet_claimed", {"packet_id": "ORCH-005", "agent": "claude"})
    """
    message = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

    with SSE_LOCK:
        for client in SSE_CLIENTS[:]:  # Copy list to avoid modification during iteration
            try:
                client.wfile.write(message.encode())
                client.wfile.flush()
            except Exception:
                # Client disconnected, remove from list
                if client in SSE_CLIENTS:
                    SSE_CLIENTS.remove(client)


# ============================================================================
# STEP 2: Add this method to the Handler class (inside the Handler class body)
# ============================================================================

def api_events(self):
    """
    SSE endpoint for real-time state change notifications.

    Keeps connection open and streams events as they occur.
    Sends heartbeat every 30 seconds to keep connection alive.

    Event format:
        event: <event_type>
        data: <json_payload>

    Events:
        - connection_opened: Initial event when client connects
        - heartbeat: Keep-alive ping every 30 seconds
        - state_change: When packet state changes (claim/done/fail)
        - packet_claimed: When packet is claimed
        - packet_done: When packet is completed
        - packet_failed: When packet fails
    """
    # Send SSE headers
    self.send_response(200)
    self.send_header("Content-Type", "text/event-stream")
    self.send_header("Cache-Control", "no-cache")
    self.send_header("Connection", "keep-alive")

    # CORS headers
    origin = self.headers.get("Origin", "http://localhost:3000")
    self.send_header("Access-Control-Allow-Origin", origin)
    self.send_header("Access-Control-Allow-Credentials", "true")

    self.end_headers()

    # Add this client to connected clients list
    with SSE_LOCK:
        SSE_CLIENTS.append(self)

    try:
        # Send connection opened event
        self.wfile.write(
            f"event: connection_opened\ndata: {json.dumps({'timestamp': time.time()})}\n\n".encode()
        )
        self.wfile.flush()

        # Keep connection alive with heartbeat
        last_heartbeat = time.time()

        while True:
            # Send heartbeat if interval elapsed
            if time.time() - last_heartbeat >= SSE_HEARTBEAT_INTERVAL:
                self.wfile.write(
                    f"event: heartbeat\ndata: {json.dumps({'timestamp': time.time()})}\n\n".encode()
                )
                self.wfile.flush()
                last_heartbeat = time.time()

            # Sleep briefly to avoid busy-wait
            time.sleep(1)

    except (BrokenPipeError, ConnectionResetError, Exception):
        # Client disconnected
        pass
    finally:
        # Remove client from list
        with SSE_LOCK:
            if self in SSE_CLIENTS:
                SSE_CLIENTS.remove(self)


# ============================================================================
# STEP 3: Add route to do_GET() method's routes dictionary (around line 182)
# ============================================================================

# Add this line to the routes dict:
#   "/api/events": self.api_events,

# Full routes dict should look like:
"""
routes = {
    "/api/auth/session": self.api_auth_session,
    "/api/terminal/logs": lambda: self.api_terminal_logs(int(query.get("limit", [100])[0])),
    "/api/terminal/metrics": self.api_terminal_metrics,
    "/api/status": self.api_status,
    "/api/ready": self.api_ready,
    "/api/progress": self.api_progress,
    "/api/log": lambda: self.api_log(int(query.get("limit", [20])[0])),
    "/api/packet": lambda: self.api_packet(query.get("id", [""])[0]),
    "/api/file": lambda: self.api_file(query.get("path", [""])[0]),
    "/api/docs-index": lambda: self.api_docs_index(query),
    "/api/deps-graph": self.api_deps_graph,
    "/api/events": self.api_events,  # <- ADD THIS LINE
}
"""

# ============================================================================
# STEP 4: (For ORCH-006) Add event emission to state transitions
# ============================================================================

# In run_cmd() method, after successful claim/done/fail, add:
"""
# Example for claim:
if cmd == "claim":
    result = engine.claim(pid, actor)
    if result.ok:
        broadcast_sse_event("packet_claimed", {
            "packet_id": pid,
            "agent": agent,
            "timestamp": datetime.now().isoformat()
        })
    return {...}

# Example for done:
if cmd == "done":
    result = engine.done(pid, actor, notes)
    if result.ok:
        broadcast_sse_event("packet_done", {
            "packet_id": pid,
            "agent": agent,
            "timestamp": datetime.now().isoformat()
        })
    return {...}

# Example for fail:
if cmd == "fail":
    result = engine.fail(pid, actor, notes)
    if result.ok:
        broadcast_sse_event("packet_failed", {
            "packet_id": pid,
            "agent": agent,
            "reason": notes,
            "timestamp": datetime.now().isoformat()
        })
    return {...}
"""

# ============================================================================
# TESTING
# ============================================================================

"""
Test SSE endpoint:

1. Start server:
   python3 .governance/wbs_server.py 8080

2. Connect with curl:
   curl -N http://127.0.0.1:8080/api/events

3. You should see:
   event: connection_opened
   data: {"timestamp": 1234567890.123}

   event: heartbeat
   data: {"timestamp": 1234567890.456}

   (every 30 seconds)

4. In another terminal, claim a packet:
   python3 .governance/wbs_cli.py claim ORCH-006 claude

5. The SSE stream should show:
   event: packet_claimed
   data: {"packet_id": "ORCH-006", "agent": "claude", "timestamp": "2026-02-26T..."}

6. Test with JavaScript (browser console or dashboard):
   const evtSource = new EventSource('http://127.0.0.1:8080/api/events');
   evtSource.onmessage = (event) => console.log('Message:', event);
   evtSource.addEventListener('packet_claimed', (event) => {
       console.log('Packet claimed:', JSON.parse(event.data));
   });
"""

# ============================================================================
# CONSTITUTIONAL COMPLIANCE
# ============================================================================

"""
This implementation complies with:

- Article II Section 6: Transition Logging
  - All state changes (claim/done/fail) emit SSE events
  - Events include timestamp, agent, and packet_id
  - Events are broadcast to all connected clients

- Article IV Section 1: State File Integrity
  - SSE is read-only - clients cannot modify state via SSE
  - State changes only via governed CLI/API endpoints

- Article VII Section 1: Immutable Event Log
  - SSE events are ephemeral (not persisted)
  - State log remains source of truth
  - SSE provides real-time notification layer

No constitutional violations introduced.
"""
