import csv
import io
import unittest

from rota.availability import DAYS
from rota.export import rota_to_csv, write_csv


def read_rows(text):
    return list(csv.reader(io.StringIO(text, newline="")))


class ExportTests(unittest.TestCase):
    def test_header_then_one_row_per_day(self):
        rows = read_rows(rota_to_csv({"mon": ["ana", "bo"]}))
        self.assertEqual(rows[0], ["day", "people"])
        self.assertEqual([row[0] for row in rows[1:]], list(DAYS))

    def test_people_are_joined_in_one_cell(self):
        rows = read_rows(rota_to_csv({"mon": ["ana", "bo"], "tue": ["cy"]}))
        self.assertEqual(rows[1], ["mon", "ana; bo"])
        self.assertEqual(rows[2], ["tue", "cy"])

    def test_empty_or_missing_day_has_blank_people(self):
        rows = read_rows(rota_to_csv({"mon": []}))
        self.assertEqual(rows[1], ["mon", ""])
        self.assertEqual(rows[2], ["tue", ""])

    def test_names_with_commas_and_quotes_survive(self):
        rows = read_rows(rota_to_csv({"mon": ['Smith, Al', 'Bo "B"']}))
        self.assertEqual(rows[1], ["mon", 'Smith, Al; Bo "B"'])

    def test_write_csv_writes_to_a_file_handle(self):
        buffer = io.StringIO(newline="")
        write_csv({"mon": ["ana"]}, buffer)
        self.assertTrue(buffer.getvalue().startswith("day,people"))


if __name__ == "__main__":
    unittest.main()
