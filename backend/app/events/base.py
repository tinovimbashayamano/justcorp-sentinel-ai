"""Synchronous domain-event infrastructure."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, TypeVar
from uuid import uuid4


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    """Base class for application domain events."""

    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


EventT = TypeVar("EventT", bound=DomainEvent)
EventHandler = Callable[[EventT], None]


class EventHandlerExecutionError(RuntimeError):
    """Raised when one or more event handlers fail."""

    def __init__(
        self,
        event: DomainEvent,
        errors: list[Exception],
    ) -> None:
        self.event = event
        self.errors = errors

        super().__init__(
            f"{len(errors)} handler(s) failed while processing "
            f"{type(event).__name__}."
        )


class SynchronousEventBus:
    """
    Lightweight in-process event bus.

    This implementation is suitable for the current modular-monolith
    architecture. It can later be replaced by Redis, RabbitMQ or Kafka while
    preserving the event dataclasses and handler interfaces.
    """

    def __init__(self) -> None:
        self._handlers: dict[
            type[DomainEvent],
            list[Callable[[DomainEvent], None]],
        ] = defaultdict(list)

    def subscribe(
        self,
        event_type: type[EventT],
        handler: EventHandler[EventT],
    ) -> None:
        """Register a handler for an event type."""

        handlers = self._handlers[event_type]

        if handler not in handlers:
            handlers.append(handler)

    def unsubscribe(
        self,
        event_type: type[EventT],
        handler: EventHandler[EventT],
    ) -> None:
        """Remove a previously registered handler."""

        handlers = self._handlers.get(event_type)

        if not handlers:
            return

        if handler in handlers:
            handlers.remove(handler)

    def publish(
        self,
        event: DomainEvent,
        *,
        raise_on_error: bool = True,
    ) -> list[Exception]:
        """
        Publish an event to all registered handlers.

        The return value contains any handler exceptions. By default an
        EventHandlerExecutionError is raised after every handler has had an
        opportunity to execute.
        """

        handlers = list(self._handlers.get(type(event), []))
        errors: list[Exception] = []

        for handler in handlers:
            try:
                handler(event)
            except Exception as exc:
                errors.append(exc)

        if errors and raise_on_error:
            raise EventHandlerExecutionError(event, errors)

        return errors

    def handler_count(
        self,
        event_type: type[DomainEvent],
    ) -> int:
        """Return the number of handlers registered for an event type."""

        return len(self._handlers.get(event_type, []))

    def clear(self) -> None:
        """Remove all event subscriptions."""

        self._handlers.clear()
