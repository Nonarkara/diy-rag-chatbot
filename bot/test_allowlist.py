"""Offline tests of the actual parser without importing Telegram or starting a bot.

Run: python -m unittest bot.test_allowlist -v
"""
import ast
import os
from pathlib import Path
import unittest
from unittest import mock


def load_parser():
    source = ast.parse(Path(__file__).with_name('telegram.py').read_text())
    node = next(item for item in source.body
                if isinstance(item, ast.FunctionDef) and item.name == '_parse_allowed_users')
    module = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module)
    scope = {'os': os}
    exec(compile(module, 'telegram.py:_parse_allowed_users', 'exec'), scope)
    return scope['_parse_allowed_users']


class AllowlistTests(unittest.TestCase):
    def parse(self, value=None):
        env = {} if value is None else {'TELEGRAM_ALLOWED_USERS': value}
        with mock.patch.dict(os.environ, env, clear=True):
            return load_parser()()

    def test_unset_empty_and_whitespace_keep_existing_default(self):
        for value in (None, '', ' ', '\t\n'):
            with self.subTest(value=value):
                self.assertEqual(self.parse(value), set())

    def test_valid_numeric_ids_keep_existing_behavior(self):
        for value, expected in [
            ('123', {123}), ('123,456', {123, 456}),
            (' 123 , 456 \n', {123, 456}), ('00123,123', {123}),
            ('0,9', {0, 9}),
        ]:
            with self.subTest(value=value):
                self.assertEqual(self.parse(value), expected)

    def test_invalid_nonempty_values_are_rejected(self):
        for value in ('alice', 'invalid-id', '-123', '+123', '1.5', '1e3', '123abc'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.parse(value)

    def test_mixed_lists_cannot_silently_drop_invalid_entries(self):
        for value in ('123,alice', 'alice,123', '123,-456', '123,4.5'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.parse(value)

    def test_empty_entries_in_nonempty_list_are_rejected(self):
        for value in (',', ',,', '123,', ',123', '123,,456', '123, ,456'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.parse(value)

    def test_digit_like_but_non_integer_text_is_rejected(self):
        with self.assertRaises(ValueError):
            self.parse('²')


if __name__ == '__main__':
    unittest.main()
