# -*- coding: utf-8 -*-
"""Smoke tests for evergis_tutorial_setup.

Covers package structure, theme discovery, public signature, external
layer registry and CLI surface. No network calls: the runner's
imperative steps (folder / layer / map creation) are exercised by the
integration pipeline, not here.
"""

import importlib
import inspect
import pkgutil
import subprocess
import sys

import pytest


# =====================================================================
# Helpers
# =====================================================================


def _iter_theme_packages():
    """Yield (name, module) for every theme subpackage."""
    import evergis_tutorial_setup.themes as themes_pkg

    for _, name, is_pkg in pkgutil.iter_modules(themes_pkg.__path__):
        if not is_pkg:
            continue
        yield name, importlib.import_module(f"{themes_pkg.__name__}.{name}")


# =====================================================================
# TestImports
# =====================================================================


class TestImports:
    """Public surface of the package."""

    def test_setup_importable(self):
        from evergis_tutorial_setup import setup
        assert setup is not None

    def test_setup_callable(self):
        from evergis_tutorial_setup import setup
        assert callable(setup)

    def test_runner_module_importable(self):
        # The runner exposes helpers that integration code reuses.
        from evergis_tutorial_setup import _runner
        assert hasattr(_runner, "setup")
        assert hasattr(_runner, "discover_themes")
        assert hasattr(_runner, "build_registry")

    def test_externals_module_importable(self):
        from evergis_tutorial_setup import _externals
        assert hasattr(_externals, "EXTERNAL_LAYERS")


# =====================================================================
# TestThemeStructure
# =====================================================================


class TestThemeStructure:
    """Filesystem-driven theme discovery."""

    EXPECTED_THEMES = {
        "account", "catalog", "eql", "features", "geo_tools",
        "layers", "shared", "tasks", "widgets",
    }

    def test_expected_themes_present(self):
        names = {name for name, _ in _iter_theme_packages()}
        # Allow new themes to be added without breaking the test, but
        # every name in EXPECTED_THEMES must still exist.
        missing = self.EXPECTED_THEMES - names
        assert not missing, f"missing themes: {sorted(missing)}"

    def test_theme_count_at_least_nine(self):
        names = [name for name, _ in _iter_theme_packages()]
        assert len(names) >= 9

    def test_every_theme_declares_theme_constant(self):
        from evergis_tutorial_setup._config import ThemeConfig

        for name, mod in _iter_theme_packages():
            theme = getattr(mod, "THEME", None)
            assert theme is not None, f"theme {name!r} has no THEME constant"
            assert isinstance(theme, ThemeConfig), (
                f"theme {name!r}: THEME must be ThemeConfig, "
                f"got {type(theme).__name__}"
            )

    def test_theme_name_matches_package_name(self):
        for name, mod in _iter_theme_packages():
            theme = getattr(mod, "THEME")
            assert theme.name == name, (
                f"package {name!r} declares THEME.name={theme.name!r}"
            )


# =====================================================================
# TestSetupSignature
# =====================================================================


class TestSetupSignature:
    """Public ``setup`` signature is stable."""

    def test_signature_parameters(self):
        from evergis_tutorial_setup import setup
        sig = inspect.signature(setup)
        assert list(sig.parameters) == ["themes", "force", "client"]

    def test_force_is_keyword_only_with_default_false(self):
        from evergis_tutorial_setup import setup
        param = inspect.signature(setup).parameters["force"]
        assert param.kind == inspect.Parameter.KEYWORD_ONLY
        assert param.default is False

    def test_client_is_keyword_only_with_default_none(self):
        from evergis_tutorial_setup import setup
        param = inspect.signature(setup).parameters["client"]
        assert param.kind == inspect.Parameter.KEYWORD_ONLY
        assert param.default is None

    def test_themes_is_positional(self):
        from evergis_tutorial_setup import setup
        param = inspect.signature(setup).parameters["themes"]
        assert param.kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.POSITIONAL_ONLY,
        )


# =====================================================================
# TestExternalLayers
# =====================================================================


class TestExternalLayers:
    """``EXTERNAL_LAYERS`` registry shape."""

    def test_is_dict(self):
        from evergis_tutorial_setup._externals import EXTERNAL_LAYERS
        assert isinstance(EXTERNAL_LAYERS, dict)

    def test_has_six_keys(self):
        from evergis_tutorial_setup._externals import EXTERNAL_LAYERS
        assert len(EXTERNAL_LAYERS) == 6

    def test_all_keys_overture_prefixed(self):
        from evergis_tutorial_setup._externals import EXTERNAL_LAYERS
        for key in EXTERNAL_LAYERS:
            assert key.startswith("overture_"), (
                f"external layer {key!r} must start with 'overture_'"
            )

    def test_values_are_strings(self):
        # Values are doc strings (origin / owner / notes); only keys
        # matter for resolution, but the shape must be stable.
        from evergis_tutorial_setup._externals import EXTERNAL_LAYERS
        for value in EXTERNAL_LAYERS.values():
            assert isinstance(value, str)


# =====================================================================
# TestShortMaxLen
# =====================================================================


class TestShortMaxLen:
    """EverGIS table-name cap (31) minus ``evg_`` prefix (4) = 27."""

    def test_short_max_len_constant(self):
        from evergis_tutorial_setup._runner import _SHORT_MAX_LEN
        assert _SHORT_MAX_LEN == 27


# =====================================================================
# TestNamingValidation
# =====================================================================


class TestNamingValidation:
    """``_validate_short`` enforces the EverGIS-friendly naming rules."""

    def test_valid_short(self):
        from evergis_tutorial_setup._runner import _validate_short
        # Should not raise.
        _validate_short("stations")
        _validate_short("features_stations")
        _validate_short("a")
        _validate_short("a" * 27)

    def test_empty_raises(self):
        from evergis_tutorial_setup._runner import _validate_short
        with pytest.raises(ValueError, match="empty"):
            _validate_short("")

    def test_too_long_raises(self):
        from evergis_tutorial_setup._runner import _validate_short
        with pytest.raises(ValueError, match="chars"):
            _validate_short("a" * 28)

    def test_too_long_28_or_more(self):
        from evergis_tutorial_setup._runner import _validate_short
        with pytest.raises(ValueError):
            _validate_short("x" * 50)

    def test_does_not_start_with_letter(self):
        from evergis_tutorial_setup._runner import _validate_short
        with pytest.raises(ValueError, match="must start with a letter"):
            _validate_short("1stations")
        with pytest.raises(ValueError, match="must start with a letter"):
            _validate_short("_stations")

    def test_uppercase_rejected(self):
        from evergis_tutorial_setup._runner import _validate_short
        with pytest.raises(ValueError, match="lowercase"):
            _validate_short("Stations")

    def test_non_alnum_rejected(self):
        from evergis_tutorial_setup._runner import _validate_short
        with pytest.raises(ValueError):
            _validate_short("sta-tions")
        with pytest.raises(ValueError):
            _validate_short("sta.tions")

    def test_underscore_allowed(self):
        from evergis_tutorial_setup._runner import _validate_short
        _validate_short("a_b_c")


# =====================================================================
# TestCli
# =====================================================================


class TestCli:
    """``python -m evergis_tutorial_setup`` is wired correctly."""

    def test_help_exit_zero(self):
        result = subprocess.run(
            [sys.executable, "-m", "evergis_tutorial_setup", "--help"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, (
            f"stdout={result.stdout!r}, stderr={result.stderr!r}"
        )
        assert "tutorial" in result.stdout.lower()

    def test_themes_subcommand_in_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "evergis_tutorial_setup", "--help"],
            capture_output=True, text=True, timeout=30,
        )
        assert "themes" in result.stdout
