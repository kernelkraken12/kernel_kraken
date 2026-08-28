"""Unit tests for protondb-cli (no network required)."""

import json

import pytest

from protondb_cli.cli import (
    BEGINNER,
    TUX,
    format_output,
    tier_of,
)

SAMPLE_GAME = {"id": 1588550, "name": "Cairn", "type": "game"}
SAMPLE_REPORT = {
    "appid": 1588550,
    "verdict": "Silver",
    "total": 412,
    "score": 0.67,
    "best": {"tier": "silver", "percent": 67},
}


def test_tier_of_normalizes():
    assert tier_of("Silver") == "silver"
    assert tier_of("Borked") == "borked"
    assert tier_of("Platinum") == "platinum"
    assert tier_of("") == "silver"


def test_output_contains_verdict():
    out = format_output(SAMPLE_GAME, SAMPLE_REPORT, show_art=False, show_beginner=False)
    assert "Cairn" in out
    assert "SILVER" in out
    assert "412 reports" in out
    assert "CONFIRMED-FIXES" in out
    assert "gamemoderun" in out


def test_output_tux_banner():
    out = format_output(SAMPLE_GAME, SAMPLE_REPORT, show_art=True, show_beginner=False)
    assert "o_o" in out  # Tux eyes present


def test_output_beginner_section():
    out = format_output(SAMPLE_GAME, SAMPLE_REPORT, show_art=False, show_beginner=True)
    assert "NEW TO LINUX GAMING" in out


def test_output_no_reports():
    out = format_output(SAMPLE_GAME, None, show_art=False, show_beginner=False)
    assert "no reports yet" in out


def test_tux_is_present():
    assert "o_o" in TUX
    assert "\\___)=(___/" in TUX


def test_beginner_has_steps():
    assert "Force the use of a specific tool" in BEGINNER
