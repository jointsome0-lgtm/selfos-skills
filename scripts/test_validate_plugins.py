#!/usr/bin/env python3
"""Regression tests for legacy package validation shared with main."""

from __future__ import annotations

import unittest

from validate_plugins import required_text


class RequiredTextTest(unittest.TestCase):
    def test_plain_non_empty_text_passes(self) -> None:
        errors: list[str] = []

        value = required_text(
            {"description": "Invented compatibility package."},
            "description",
            "invented.json",
            errors,
        )

        self.assertEqual(value, "Invented compatibility package.")
        self.assertEqual(errors, [])

    def test_control_character_is_rejected(self) -> None:
        errors: list[str] = []

        value = required_text(
            {"description": "Invented\ncompatibility package."},
            "description",
            "invented.json",
            errors,
        )

        self.assertIsNone(value)
        self.assertEqual(
            errors,
            ["invented.json: 'description' must not contain control characters"],
        )


if __name__ == "__main__":
    unittest.main()
