"""Exporting the rota as CSV for the front desk."""
import csv
import io

from rota.availability import DAYS


def write_csv(rota, handle):
    """Write the rota to an open text file as CSV, one row per day.

    The columns are `day` and `people`; people on the same day are joined
    with "; " so each day stays in a single cell. Open the file with
    newline="" so the csv module controls line endings.
    """
    writer = csv.writer(handle)
    writer.writerow(["day", "people"])
    for day in DAYS:
        writer.writerow([day, "; ".join(rota.get(day, []))])


def rota_to_csv(rota):
    """Return the rota as a CSV string."""
    buffer = io.StringIO(newline="")
    write_csv(rota, buffer)
    return buffer.getvalue()
