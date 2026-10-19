"""Alternative spellings of unit names, matched case-insensitively."""
from units.table import FACTORS, TEMPERATURE

_SPELLINGS = {
    "m": ("metre", "metres", "meter", "meters"),
    "km": ("kilometre", "kilometres", "kilometer", "kilometers"),
    "mi": ("mile", "miles"),
    "ft": ("foot", "feet"),
    "kg": ("kilogram", "kilograms", "kilogramme", "kilogrammes"),
    "g": ("gram", "grams", "gramme", "grammes"),
    "lb": ("lbs", "pound", "pounds"),
    "C": ("celsius",),
    "F": ("fahrenheit",),
    "K": ("kelvin",),
}

ALIASES = {
    name.lower(): unit
    for unit, spellings in _SPELLINGS.items()
    for name in (unit, *spellings)
}


def resolve(name):
    """Return the canonical unit for name, or name unchanged if unknown."""
    return ALIASES.get(name.lower(), name)
