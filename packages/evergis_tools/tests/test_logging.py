# -*- coding: utf-8 -*-
"""Tests for logging.py -- logging utilities."""

import logging

from evergis_tools.logging import get_logger, temporary_level


class TestGetLogger:
    """Tests for get_logger()."""

    def test_returns_logger(self):
        log = get_logger("test.module")
        assert isinstance(log, logging.Logger)

    def test_has_null_handler(self):
        log = get_logger("test.nullhandler")
        assert any(isinstance(h, logging.NullHandler) for h in log.handlers)

    def test_default_name(self):
        log = get_logger()
        assert log.name == "evergis_tools"

    def test_same_logger_on_repeated_call(self):
        log1 = get_logger("test.same")
        log2 = get_logger("test.same")
        assert log1 is log2


class TestTemporaryLevel:
    """Tests for temporary_level()."""

    def test_level_changed_inside(self):
        log = get_logger("test.temp_level")
        log.setLevel(logging.WARNING)
        with temporary_level(log, logging.DEBUG):
            assert log.level == logging.DEBUG
        assert log.level == logging.WARNING

    def test_level_restored_after(self):
        log = get_logger("test.restore")
        original = log.level
        with temporary_level(log, logging.CRITICAL):
            pass
        assert log.level == original

    def test_none_level_no_change(self):
        log = get_logger("test.none_level")
        log.setLevel(logging.INFO)
        with temporary_level(log, None):
            assert log.level == logging.INFO
        assert log.level == logging.INFO
