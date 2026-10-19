import json
import unittest

from factory import make_event
from router.dispatch import dispatch
from router.handlers import all_handlers
from router.handlers.orders import (
    handle_order_cancelled,
    handle_order_created,
    handle_order_refunded,
)
from router.registry import default_registry


class OrderHandlerTests(unittest.TestCase):
    def test_created_reports_state(self):
        result = handle_order_created(make_event("order.created", order_id="o1"))
        self.assertEqual(result, {"order_id": "o1", "state": "created"})

    def test_cancelled_reports_state(self):
        result = handle_order_cancelled(make_event("order.cancelled", order_id="o1"))
        self.assertEqual(result, {"order_id": "o1", "state": "cancelled"})

    def test_refunded_records_amount(self):
        event = make_event("order.refunded", order_id="o1", amount=1250)
        self.assertEqual(
            handle_order_refunded(event),
            {"order_id": "o1", "state": "refunded", "amount": 1250},
        )

    def test_all_handlers_includes_orders(self):
        expected = {"order.created", "order.cancelled", "order.refunded"}
        self.assertLessEqual(expected, set(all_handlers()))

    def test_default_registry_routes_order_events(self):
        body = json.dumps(make_event("order.created"))
        self.assertEqual(dispatch(body, default_registry(), now=110)[0], 200)

    def test_default_registry_keeps_ping(self):
        self.assertIsNotNone(default_registry().get("ping"))


if __name__ == "__main__":
    unittest.main()
