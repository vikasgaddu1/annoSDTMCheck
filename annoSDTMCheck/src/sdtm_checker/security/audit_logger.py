"""
Security audit logging system for SDTM Annotation Checker.
"""

import json
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class AuditEvent:
    """Represents a security audit event."""
    timestamp: str
    event_type: str
    user: str
    action: str
    details: Dict[str, Any]
    status: str
    ip_address: Optional[str] = None


class AuditLogger:
    """Handles security audit logging."""

    def __init__(self, log_dir: str = "logs/audit"):
        """
        Initialize the audit logger.

        Args:
            log_dir: Directory to store audit logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_log_file = self._get_log_file()

    def _get_log_file(self) -> Path:
        """Get the current log file path based on date."""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"audit_{today}.json"

    def _ensure_log_file(self) -> None:
        """Ensure the log file exists and has proper format."""
        if not self.current_log_file.exists():
            with open(self.current_log_file, 'w') as f:
                json.dump([], f)

    def _load_events(self) -> list:
        """Load existing audit events from the log file."""
        self._ensure_log_file()
        try:
            with open(self.current_log_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(
                f"Invalid JSON in audit log file: {self.current_log_file}")
            return []

    def _save_events(self, events: list) -> None:
        """Save audit events to the log file."""
        try:
            with open(self.current_log_file, 'w') as f:
                json.dump(events, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save audit log: {e}")

    def log_event(
        self,
        event_type: str,
        user: str,
        action: str,
        details: Dict[str, Any],
        status: str = "success",
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log a security audit event.

        Args:
            event_type: Type of event (e.g., "config_change", "login", "file_access")
            user: Username or identifier of the user
            action: Description of the action performed
            details: Additional event details
            status: Event status (success/failure)
            ip_address: Optional IP address of the user
        """
        # Check if we need to rotate to a new log file
        if self.current_log_file != self._get_log_file():
            self.current_log_file = self._get_log_file()

        # Create audit event
        event = AuditEvent(
            timestamp=datetime.datetime.now().isoformat(),
            event_type=event_type,
            user=user,
            action=action,
            details=details,
            status=status,
            ip_address=ip_address
        )

        # Load existing events
        events = self._load_events()

        # Add new event
        events.append(asdict(event))

        # Save updated events
        self._save_events(events)

        # Also log to application logger
        log_msg = (
            f"Audit Event: {event_type} | User: {user} | "
            f"Action: {action} | Status: {status}"
        )
        if status == "success":
            logger.info(log_msg)
        else:
            logger.warning(log_msg)

    def get_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        event_type: Optional[str] = None,
        user: Optional[str] = None,
        status: Optional[str] = None
    ) -> list:
        """
        Retrieve audit events with optional filtering.

        Args:
            start_date: Filter events after this date (ISO format)
            end_date: Filter events before this date (ISO format)
            event_type: Filter by event type
            user: Filter by user
            status: Filter by status

        Returns:
            List of matching audit events
        """
        events = self._load_events()

        # Apply filters
        filtered_events = []
        for event in events:
            # Date filters
            if start_date and event["timestamp"] < start_date:
                continue
            if end_date and event["timestamp"] > end_date:
                continue

            # Other filters
            if event_type and event["event_type"] != event_type:
                continue
            if user and event["user"] != user:
                continue
            if status and event["status"] != status:
                continue

            filtered_events.append(event)

        return filtered_events

    def clear_events(self, before_date: Optional[str] = None) -> None:
        """
        Clear audit events, optionally before a specific date.

        Args:
            before_date: Clear events before this date (ISO format)
        """
        if before_date:
            events = self._load_events()
            events = [e for e in events if e["timestamp"] >= before_date]
            self._save_events(events)
        else:
            self._save_events([])
