#!/usr/bin/env python3
"""
Apply SSE endpoint patch to wbs_server.py
ORCH-005: Add SSE endpoint implementation
"""

import re
from pathlib import Path

def apply_sse_patch():
    """Apply SSE implementation to wbs_server.py"""

    server_file = Path(__file__).parent / "wbs_server.py"
    content = server_file.read_text()

    # Check if already patched
    if "SSE_CLIENTS" in content:
        print("✓ SSE already implemented in wbs_server.py")
        return True

    print("Applying SSE patch to wbs_server.py...")

    # Step 1: Add SSE globals and broadcast function after TERMINAL_LOG
    sse_globals = '''
# SSE (Server-Sent Events) connection management
SSE_CLIENTS: List = []
SSE_HEARTBEAT_INTERVAL = 30  # seconds
SSE_LOCK = __import__("threading").Lock()


def broadcast_sse_event(event_type: str, data: dict):
    """
    Broadcast state change event to all connected SSE clients.

    Args:
        event_type: Event type (e.g., "state_change", "packet_claimed", "packet_done")
        data: Event payload as dictionary
    """
    message = f"event: {event_type}\\ndata: {json.dumps(data)}\\n\\n"

    with SSE_LOCK:
        for client in SSE_CLIENTS[:]:  # Copy list to avoid modification during iteration
            try:
                client.wfile.write(message.encode())
                client.wfile.flush()
            except Exception:
                # Client disconnected, remove from list
                if client in SSE_CLIENTS:
                    SSE_CLIENTS.remove(client)


'''

    content = content.replace(
        'TERMINAL_LOG: List[Dict] = []\n\n\ndef _build_logger()',
        f'TERMINAL_LOG: List[Dict] = []\n{sse_globals}\ndef _build_logger()'
    )

    # Step 2: Add api_events method to Handler class (before log_message method)
    api_events_method = '''
    def api_events(self):
        """
        SSE endpoint for real-time state change notifications.

        Keeps connection open and streams events as they occur.
        Sends heartbeat every 30 seconds to keep connection alive.
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
                f"event: connection_opened\\ndata: {json.dumps({'timestamp': time.time()})}\\n\\n".encode()
            )
            self.wfile.flush()

            # Keep connection alive with heartbeat
            last_heartbeat = time.time()

            while True:
                # Send heartbeat if interval elapsed
                if time.time() - last_heartbeat >= SSE_HEARTBEAT_INTERVAL:
                    self.wfile.write(
                        f"event: heartbeat\\ndata: {json.dumps({'timestamp': time.time()})}\\n\\n".encode()
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

'''

    content = content.replace(
        '    def log_message(self, format, *args):',
        f'{api_events_method}\n    def log_message(self, format, *args):'
    )

    # Step 3: Add /api/events route to do_GET routes dict
    routes_pattern = r'(routes = \{[^}]+"/api/deps-graph": self\.api_deps_graph,)'
    content = re.sub(
        routes_pattern,
        r'\1\n            "/api/events": self.api_events,',
        content
    )

    # Write patched content
    server_file.write_text(content)

    print("✓ SSE endpoint added to wbs_server.py")
    print("✓ /api/events route registered")
    print("✓ broadcast_sse_event() function available")
    print("\nSSE implementation complete!")
    return True


if __name__ == "__main__":
    try:
        success = apply_sse_patch()
        exit(0 if success else 1)
    except Exception as e:
        print(f"✗ Error applying patch: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
