"""SqliteSaver checkpoint persistence tests — D-09."""
import os
import tempfile
import sqlite3
import pytest
from langgraph.checkpoint.sqlite import SqliteSaver


class TestCheckpointer:
    """D-09: SqliteSaver persists checkpoint across restart."""

    async def test_checkpointer_persistence(self):
        """Write checkpoint, recreate connection, verify checkpoint exists."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            # First connection: write a checkpoint
            conn1 = sqlite3.connect(db_path, check_same_thread=False)
            saver1 = SqliteSaver(conn1)

            # Create a test checkpoint
            test_config = {"configurable": {"thread_id": "test-thread-1"}}
            test_checkpoint = {
                "v": 1,
                "ts": "2026-01-01T00:00:00Z",
                "id": "checkpoint-1",
                "parent_id": None,
                "channel_values": {"user_input": "test"},
            }
            # SqliteSaver.put writes a checkpoint
            saver1.put(test_config, test_checkpoint, {})

            # Close first connection
            conn1.close()

            # Second connection: read the checkpoint
            conn2 = sqlite3.connect(db_path, check_same_thread=False)
            saver2 = SqliteSaver(conn2)

            # Verify checkpoint exists
            configs = list(saver2.list(test_config))
            assert len(configs) > 0, "No checkpoints found after reconnection"

            conn2.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
