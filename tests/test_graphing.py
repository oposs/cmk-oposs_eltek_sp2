"""Metric names: prefixed, declared, and translated from the legacy names."""

import importlib.util
import pathlib
import sys

import pytest
from cmk.agent_based.v2 import CheckPlugin, Metric
from cmk.graphing.v1 import graphs, metrics, perfometers, translations
from test_check import RECTIFIER_1, SINGLE_SERVICES, _section

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "local/lib/python3/cmk_addons/plugins/oposs_eltek_sp2"

# What the legacy eltek_sp2_* checks called their metrics, per check.
LEGACY = {
    "oposs_eltek_sp2_mains_voltage": {"voltage": "oposs_eltek_voltage"},
    "oposs_eltek_sp2_rectifier_current": {"current": "oposs_eltek_current"},
    "oposs_eltek_sp2_rectifier_capacity": {"percentage": "oposs_eltek_capacity_pct"},
    "oposs_eltek_sp2_rectifier_errors": {"errors": "oposs_eltek_errors"},
    "oposs_eltek_sp2_rectifier_temperature": {"temperature": "oposs_eltek_temperature"},
    "oposs_eltek_sp2_load_current": {"current": "oposs_eltek_current"},
}


def _load(path):
    name = "test_graphing_" + path.stem + "_" + path.parent.name
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def check():
    return _load(PLUGIN / "agent_based/oposs_eltek_sp2.py")


@pytest.fixture(scope="module")
def graphing_objects():
    objects = []
    for path in sorted((PLUGIN / "graphing").glob("*.py")):
        objects.extend(vars(_load(path)).values())
    return objects


@pytest.fixture(scope="module")
def declared(graphing_objects):
    return {o.name for o in graphing_objects if isinstance(o, metrics.Metric)}


@pytest.fixture(scope="module")
def emitted(check):
    """Metric names per check plugin, from a healthy system."""
    section = _section(check)
    out = {}
    for name in SINGLE_SERVICES:
        out[f"oposs_eltek_sp2_{name}"] = [
            m.name for m in getattr(check, f"check_oposs_eltek_sp2_{name}")(section)
            if isinstance(m, Metric)
        ]
    out["oposs_eltek_sp2_mains_voltage"] = [
        m.name for m in check.check_oposs_eltek_sp2_mains_voltage("Mains Voltage 1", section)
        if isinstance(m, Metric)
    ]
    out["oposs_eltek_sp2_rectifier_status"] = [
        m.name for m in check.check_oposs_eltek_sp2_rectifier_status(RECTIFIER_1, section)
        if isinstance(m, Metric)
    ]
    return out


def test_metrics_per_check(emitted):
    assert emitted == {
        "oposs_eltek_sp2_power_system_status": [],
        "oposs_eltek_sp2_power_system_mode": [],
        "oposs_eltek_sp2_mains_failure": [],
        "oposs_eltek_sp2_rectifier_count": [],
        "oposs_eltek_sp2_rectifier_current": ["oposs_eltek_current"],
        "oposs_eltek_sp2_rectifier_capacity": ["oposs_eltek_capacity_pct"],
        "oposs_eltek_sp2_rectifier_errors": ["oposs_eltek_errors"],
        "oposs_eltek_sp2_rectifier_temperature": ["oposs_eltek_temperature"],
        "oposs_eltek_sp2_load_current": ["oposs_eltek_current"],
        "oposs_eltek_sp2_mains_voltage": ["oposs_eltek_voltage"],
        "oposs_eltek_sp2_rectifier_status": ["oposs_eltek_current", "oposs_eltek_voltage"],
    }


def test_every_emitted_metric_is_declared(emitted, declared):
    used = {n for names in emitted.values() for n in names}
    assert sorted(used - declared) == []
    assert sorted(declared - used) == []


def test_every_declared_name_is_prefixed(graphing_objects):
    kinds = (metrics.Metric, graphs.Graph, perfometers.Perfometer, translations.Translation)
    names = [o.name for o in graphing_objects if isinstance(o, kinds)]
    assert names
    assert [n for n in names if not n.startswith("oposs_eltek_")] == []


def test_graphs_and_perfometers_use_declared_metrics(graphing_objects, declared):
    used = set()
    for o in graphing_objects:
        if isinstance(o, graphs.Graph):
            used.update(o.simple_lines)
        elif isinstance(o, perfometers.Perfometer):
            used.update(o.segments)
    assert used
    assert sorted(used - declared) == []


def test_legacy_names_translate_on_the_live_check_commands(check, graphing_objects, declared):
    plugins = {p.name for p in vars(check).values() if isinstance(p, CheckPlugin)}
    found = {}
    for o in graphing_objects:
        if isinstance(o, translations.Translation):
            # The lookup key is the check command a live service runs today,
            # so it must name one of this package's check plugins.
            (command,) = o.check_commands
            assert isinstance(command, translations.PassiveCheck)
            assert command.name in plugins
            found[command.name] = {
                old: rule.metric_name for old, rule in o.translations.items()
                if isinstance(rule, translations.RenameTo)
            }
    assert found == LEGACY
    for renames in found.values():
        assert set(renames.values()) <= declared
