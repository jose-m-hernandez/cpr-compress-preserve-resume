"""Conversion factors: unit -> (dimension, factor to the base unit)."""

FACTORS = {
    "m": ("length", 1.0),
    "km": ("length", 1000.0),
    "mi": ("length", 1609.344),
    "ft": ("length", 0.3048),
    "kg": ("mass", 1.0),
    "g": ("mass", 0.001),
    "lb": ("mass", 0.45359237),
}

TEMPERATURE = ("C", "F", "K")
