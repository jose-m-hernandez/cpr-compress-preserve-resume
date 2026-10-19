"""Reading the sales CSV."""
import csv


def load_sales(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return [
            {
                "date": row["date"],
                "sku": row["sku"],
                "quantity": int(row["quantity"]),
                "unit_price": float(row["unit_price"]) / 100,  # CSV stores cents
            }
            for row in csv.DictReader(handle)
        ]
