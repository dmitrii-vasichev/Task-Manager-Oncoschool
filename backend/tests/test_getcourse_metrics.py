"""Regression tests for GetCourse metric calculation — issue #163.

Root cause: service assumed dict-based items (row.get("email"), row.get("status"))
but GetCourse export API returns array-based items (row[index]).

These tests verify metric calculation matches the working n8n flow exactly:
- users_count = len(items)
- payments_count = len(items)  (pre-filtered by status=accepted in request)
- payments_sum = sum(row[7])
- orders_count = count where row[10] > 0
- orders_sum = sum(row[10]) where > 0
"""

import unittest
from datetime import date
from decimal import Decimal

from app.services.getcourse_service import (
    GetCourseService,
    PAYMENT_PRICE_INDEX,
    ORDER_SUM_INDEX,
)


class TestCountUsers(unittest.TestCase):
    """users_count = number of rows returned."""

    def test_counts_all_rows(self):
        rows = [["user1@mail.ru", "Иванов"], ["user2@mail.ru", "Петров"]]
        self.assertEqual(GetCourseService._count_users(rows), 2)

    def test_empty_list(self):
        self.assertEqual(GetCourseService._count_users([]), 0)

    def test_single_user(self):
        self.assertEqual(GetCourseService._count_users([["a@b.c"]]), 1)


class TestSumPayments(unittest.TestCase):
    """payments_count = len(rows), payments_sum = sum of column[7]."""

    def _make_row(self, price_str: str) -> list:
        """Build a payment row with price at index 7."""
        row = [""] * (PAYMENT_PRICE_INDEX + 1)
        row[PAYMENT_PRICE_INDEX] = price_str
        return row

    def test_basic_sum(self):
        rows = [self._make_row("1000"), self._make_row("2500.50")]
        count, total = GetCourseService._sum_payments(rows)
        self.assertEqual(count, 2)
        self.assertEqual(total, Decimal("3500.50"))

    def test_russian_locale_formatting(self):
        """Handles '1 000,50' (space separator, comma decimal)."""
        rows = [self._make_row("1 000,50"), self._make_row("2\xa0500")]
        count, total = GetCourseService._sum_payments(rows)
        self.assertEqual(count, 2)
        self.assertEqual(total, Decimal("3500.50"))

    def test_empty_price(self):
        """Empty/None price treated as 0."""
        rows = [self._make_row(""), self._make_row("100")]
        count, total = GetCourseService._sum_payments(rows)
        self.assertEqual(count, 2)
        self.assertEqual(total, Decimal("100"))

    def test_empty_rows(self):
        count, total = GetCourseService._sum_payments([])
        self.assertEqual(count, 0)
        self.assertEqual(total, Decimal("0"))

    def test_row_too_short(self):
        """Row shorter than PAYMENT_PRICE_INDEX — skip but still count."""
        rows = [["a", "b"]]
        count, total = GetCourseService._sum_payments(rows)
        self.assertEqual(count, 1)
        self.assertEqual(total, Decimal("0"))


class TestSumOrders(unittest.TestCase):
    """orders_count = count where row[10] > 0, orders_sum = sum of those."""

    def _make_row(self, cost_str: str) -> list:
        """Build a deals row with cost at index 10."""
        row = [""] * (ORDER_SUM_INDEX + 1)
        row[ORDER_SUM_INDEX] = cost_str
        return row

    def test_only_positive_counted(self):
        """n8n logic: only orders with cost > 0 are counted."""
        rows = [
            self._make_row("5000"),
            self._make_row("0"),
            self._make_row(""),
            self._make_row("3000"),
        ]
        count, total = GetCourseService._sum_orders(rows)
        self.assertEqual(count, 2)
        self.assertEqual(total, Decimal("8000"))

    def test_russian_locale(self):
        rows = [self._make_row("15 000,99")]
        count, total = GetCourseService._sum_orders(rows)
        self.assertEqual(count, 1)
        self.assertEqual(total, Decimal("15000.99"))

    def test_empty_rows(self):
        count, total = GetCourseService._sum_orders([])
        self.assertEqual(count, 0)
        self.assertEqual(total, Decimal("0"))

    def test_all_zero_cost(self):
        rows = [self._make_row("0"), self._make_row("0")]
        count, total = GetCourseService._sum_orders(rows)
        self.assertEqual(count, 0)
        self.assertEqual(total, Decimal("0"))


class TestParseDecimal(unittest.TestCase):
    """_parse_decimal handles Russian-locale number formatting."""

    def test_integer(self):
        self.assertEqual(GetCourseService._parse_decimal("1000"), Decimal("1000"))

    def test_comma_decimal(self):
        self.assertEqual(GetCourseService._parse_decimal("1000,50"), Decimal("1000.50"))

    def test_nbsp_separator(self):
        self.assertEqual(GetCourseService._parse_decimal("1\xa0000"), Decimal("1000"))

    def test_space_separator(self):
        self.assertEqual(GetCourseService._parse_decimal("10 000"), Decimal("10000"))

    def test_none(self):
        self.assertEqual(GetCourseService._parse_decimal(None), Decimal("0"))

    def test_empty_string(self):
        self.assertEqual(GetCourseService._parse_decimal(""), Decimal("0"))

    def test_non_numeric(self):
        self.assertEqual(GetCourseService._parse_decimal("abc"), Decimal("0"))

    def test_currency_suffix_rub(self):
        """Handles '5000 ₽' or '5000₽'."""
        self.assertEqual(GetCourseService._parse_decimal("5000₽"), Decimal("5000"))

    def test_currency_suffix_rub_with_space(self):
        self.assertEqual(GetCourseService._parse_decimal("5 000 ₽"), Decimal("5000"))

    def test_currency_prefix(self):
        self.assertEqual(GetCourseService._parse_decimal("₽5000"), Decimal("5000"))

    def test_currency_with_comma(self):
        self.assertEqual(GetCourseService._parse_decimal("1 500,50 RUB"), Decimal("1500.50"))

    def test_trailing_text(self):
        self.assertEqual(GetCourseService._parse_decimal("2500.00 руб."), Decimal("2500.00"))

    def test_thin_space_separator(self):
        """Thin space U+2009 — used by some GetCourse locales."""
        self.assertEqual(GetCourseService._parse_decimal("5\u2009000"), Decimal("5000"))

    def test_narrow_nbsp_separator(self):
        """Narrow no-break space U+202F."""
        self.assertEqual(GetCourseService._parse_decimal("12\u202f500,50"), Decimal("12500.50"))


class TestExtractDateFromRow(unittest.TestCase):
    """Date extraction from array rows for range backfill grouping."""

    def test_iso_datetime(self):
        row = ["user@mail.ru", "Иванов", "2026-03-15 10:30:00", "phone"]
        d = GetCourseService._extract_date_from_row(row)
        self.assertEqual(d, date(2026, 3, 15))

    def test_iso_date_only(self):
        row = ["a", "b", "2026-03-15", "c"]
        d = GetCourseService._extract_date_from_row(row)
        self.assertEqual(d, date(2026, 3, 15))

    def test_respects_date_range(self):
        """Dates outside the range are ignored."""
        row = ["2020-01-01", "data", "2026-03-15"]
        d = GetCourseService._extract_date_from_row(
            row, date_range=(date(2026, 3, 1), date(2026, 3, 31))
        )
        self.assertEqual(d, date(2026, 3, 15))

    def test_no_date_found(self):
        row = ["abc", "123", "not-a-date"]
        d = GetCourseService._extract_date_from_row(row)
        self.assertIsNone(d)

    def test_empty_row(self):
        d = GetCourseService._extract_date_from_row([])
        self.assertIsNone(d)


class TestGroupRowsByDate(unittest.TestCase):
    """Group array rows by extracted date."""

    def test_basic_grouping(self):
        rows = [
            ["a", "2026-03-15", "data1"],
            ["b", "2026-03-15", "data2"],
            ["c", "2026-03-16", "data3"],
        ]
        grouped = GetCourseService._group_rows_by_date(
            rows, date_range=(date(2026, 3, 15), date(2026, 3, 16))
        )
        self.assertEqual(len(grouped[date(2026, 3, 15)]), 2)
        self.assertEqual(len(grouped[date(2026, 3, 16)]), 1)

    def test_empty_rows(self):
        grouped = GetCourseService._group_rows_by_date([])
        self.assertEqual(len(grouped), 0)

    def test_non_list_rows_skipped(self):
        """Dict-like rows (shouldn't happen) are gracefully skipped."""
        rows = [{"key": "val"}, ["a", "2026-03-15"]]
        grouped = GetCourseService._group_rows_by_date(rows)
        self.assertEqual(len(grouped), 1)


class TestN8nScenario(unittest.TestCase):
    """End-to-end scenario matching n8n Code node logic.

    Reproduces the exact calculation from the n8n flow:
    - users_count = rows_users.length
    - payments_count = rows_payments.length
    - payments_sum = sum of row[7] for all payments
    - orders_count = count where row[10] > 0
    - orders_sum = sum of row[10] where > 0
    """

    def test_full_metric_calculation(self):
        # 3 users
        user_rows = [
            ["1", "user1@mail.ru", "Иванов", "2026-03-15"],
            ["2", "user2@mail.ru", "Петров", "2026-03-15"],
            ["3", "user3@mail.ru", "Сидоров", "2026-03-15"],
        ]

        # 2 payments (already filtered by status=accepted in request)
        payment_rows = [
            ["1", "user1", "prod1", "offer1", "pay1", "2026-03-15", "acc1", "5 000,00", "extra"],
            ["2", "user2", "prod2", "offer2", "pay2", "2026-03-15", "acc2", "12\xa0500,50", "extra"],
        ]

        # 3 deals: 2 with positive cost, 1 with zero
        deal_rows = [
            ["1", "user1", "deal1", "offer1", "2026-03-15", "info1", "info2", "info3", "info4", "info5", "10 000"],
            ["2", "user2", "deal2", "offer2", "2026-03-15", "info1", "info2", "info3", "info4", "info5", "0"],
            ["3", "user3", "deal3", "offer3", "2026-03-15", "info1", "info2", "info3", "info4", "info5", "7 500,50"],
        ]

        users_count = GetCourseService._count_users(user_rows)
        payments_count, payments_sum = GetCourseService._sum_payments(payment_rows)
        orders_count, orders_sum = GetCourseService._sum_orders(deal_rows)

        self.assertEqual(users_count, 3)
        self.assertEqual(payments_count, 2)
        self.assertEqual(payments_sum, Decimal("17500.50"))
        self.assertEqual(orders_count, 2)  # only rows where cost > 0
        self.assertEqual(orders_sum, Decimal("17500.50"))


if __name__ == "__main__":
    unittest.main()
