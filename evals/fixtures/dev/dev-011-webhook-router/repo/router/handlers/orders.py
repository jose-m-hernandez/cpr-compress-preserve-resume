"""Handlers for the order event family."""


def handle_order_created(event):
    """Handle order.created and return the resulting order state."""
    return {"order_id": event.get("order_id"), "state": "created"}


def handle_order_cancelled(event):
    """Handle order.cancelled and return the resulting order state."""
    return {"order_id": event.get("order_id"), "state": "cancelled"}


def handle_order_refunded(event):
    """Handle order.refunded and return the order state with the refund amount."""
    return {
        "order_id": event.get("order_id"),
        "state": "refunded",
        "amount": event.get("amount"),
    }


HANDLERS = {
    "order.created": handle_order_created,
    "order.cancelled": handle_order_cancelled,
    "order.refunded": handle_order_refunded,
}
