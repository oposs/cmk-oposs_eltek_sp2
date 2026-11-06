"""Tests for the eleven Eltek Smartpack S check plugins.

The string table mirrors what Checkmk's SNMP fetch delivers for the eleven
SNMPTree entries of the section, in fetch order: one list of rows per tree,
one row per table entry (a scalar tree gives a single row), and every value a
string. A missing OID shows up as an empty string, a missing tree as [].

The values follow the Eltek SP2 MIB: status columns use the ErrorStatus enum
(1 = normal), currents come in tenths of an ampere, voltages in volts,
temperatures in degrees Celsius. Thresholds are the alarm levels the device
itself is configured with.
"""

import importlib.util
import json
import pathlib
import re
import sys

import pytest
from cmk.agent_based.v2 import Metric, Result, Service, State

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECK = ROOT / "local/lib/python3/cmk_addons/plugins/oposs_eltek_sp2/agent_based/oposs_eltek_sp2.py"

RECTIFIER_1 = "Flatpack2 48/2000 HE [113871234567]"
RECTIFIER_2 = "Flatpack2 48/2000 HE [113871234568]"


@pytest.fixture(scope="module")
def check():
    name = "test_oposs_eltek_sp2_check"
    spec = importlib.util.spec_from_file_location(name, CHECK)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    yield module
    sys.modules.pop(name, None)


def _tables(**override):
    """The SNMP string table of a healthy three-phase system with two rectifiers."""
    tables = {
        # 2.1.0 powerSystemStatus
        "status": [["1"]],
        # 2.3.0 powerSystemMode: float
        "mode": [["3"]],
        # 3.4.1 mains voltage table: status, description, value,
        # minor high (warn), major high (crit), minor low (warn), major low (crit)
        "mains": [
            ["1", "Mains Voltage 1", "231", "260", "275", "200", "185"],
            ["1", "Mains Voltage 2", "229", "260", "275", "200", "185"],
            ["1", "Mains Voltage 3", "233", "260", "275", "200", "185"],
        ],
        # 3.2.5.0 number of failed mains phases
        "failure": [["0"]],
        # 5.5.0 number of installed rectifiers
        "count": [["2"]],
        # 5.2: status, value (0.1 A), minor (warn), major (crit)
        "current": [["1", "276", "1000", "1200"]],
        # 5.3: status, value (%), major (crit), minor (warn)
        "capacity": [["1", "35", "90", "80"]],
        # 5.4: status, value, major (crit), minor (warn)
        "errors": [["1", "0", "2", "1"]],
        # 5.18: status, value (C), major high, minor high, minor low, major low
        "temperature": [["1", "28", "60", "50", "5", "0"]],
        # 5.6.1 rectifier table: status, output current (0.1 A), input
        # voltage, type, serial (the device pads it with blanks)
        "rectifiers": [
            ["1", "138", "232", "Flatpack2 48/2000 HE", "113871234567 "],
            ["1", "138", "231", "Flatpack2 48/2000 HE", "113871234568 "],
        ],
        # 9.2: status, value (0.1 A), major (crit), minor (warn)
        "load": [["1", "270", "1500", "1300"]],
    }
    tables.update(override)
    return [tables[k] for k in (
        "status", "mode", "mains", "failure", "count", "current", "capacity",
        "errors", "temperature", "rectifiers", "load",
    )]


def _section(check, **override):
    return check.parse_oposs_eltek_sp2(_tables(**override))


def _results(output):
    return [r for r in output if isinstance(r, Result)]


def _metrics(output):
    return [m for m in output if isinstance(m, Metric)]


def _state(output):
    return State.worst(*(r.state for r in _results(output)))


# ---------------------------------------------------------------------------
# Section: SNMP fetch, detection, parsing
# ---------------------------------------------------------------------------

def test_section_fetches_eleven_trees(check):
    section = check.snmp_section_oposs_eltek_sp2
    assert section.name == "oposs_eltek_sp2"
    assert len(section.fetch) == 11


@pytest.mark.parametrize("system_type, matches", [
    ("Smartpack S", True),
    ("Smartpack S 48V", True),
    ("Smartpack2 Master", False),
    ("", False),
])
def test_detection_looks_for_smartpack_s(check, system_type, matches):
    # The detect spec is a list of (OID, regex, must-match) conditions that
    # Checkmk matches from the start of the value.
    ((oid, pattern, flag),) = check.snmp_section_oposs_eltek_sp2.detect[0]
    assert oid == ".1.3.6.1.4.1.12148.10.2.6.0"
    assert flag is True
    assert bool(re.match(pattern, system_type)) is matches


def test_parse_healthy_system(check):
    section = _section(check)
    assert sorted(section) == [
        "load_current", "mains_failure", "mains_voltage", "power_system_mode",
        "power_system_status", "rectifier_capacity", "rectifier_count",
        "rectifier_current", "rectifier_errors", "rectifier_status",
        "rectifier_temperature",
    ]
    assert section["mains_voltage"]["Mains Voltage 2"] == {
        "state": "1", "desc": "Mains Voltage 2", "value": "229",
        "warnUp": "260", "critUp": "275", "warnLow": "200", "critLow": "185",
    }
    assert section["rectifier_status"][RECTIFIER_1]["serial"] == "113871234567 "


def test_parse_device_without_data_is_empty(check):
    assert check.parse_oposs_eltek_sp2([[] for _ in range(11)]) == {}


def test_parse_drops_short_rows(check):
    section = _section(
        check,
        mains=[["1", "Mains Voltage 1", "231"]],
        current=[["1", "276"]],
        capacity=[["1"]],
        errors=[["1", "0", "2"]],
        temperature=[["1", "28", "60", "50", "5"]],
        rectifiers=[["1", "138", "232", "Flatpack2 48/2000 HE"]],
        load=[["1", "270", "1500"]],
    )
    assert sorted(section) == [
        "mains_failure", "power_system_mode", "power_system_status", "rectifier_count",
    ]


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

SINGLE_SERVICES = [
    "power_system_status", "power_system_mode", "mains_failure", "rectifier_count",
    "rectifier_current", "rectifier_capacity", "rectifier_errors",
    "rectifier_temperature", "load_current",
]


@pytest.mark.parametrize("name", SINGLE_SERVICES)
def test_single_services_are_discovered(check, name):
    discover = getattr(check, f"discover_oposs_eltek_sp2_{name}")
    assert list(discover(_section(check))) == [Service()]
    assert list(discover({})) == []


def test_one_mains_voltage_service_per_phase(check):
    found = list(check.discover_oposs_eltek_sp2_mains_voltage(_section(check)))
    assert found == [Service(item=f"Mains Voltage {n}") for n in (1, 2, 3)]
    assert list(check.discover_oposs_eltek_sp2_mains_voltage({})) == []


def test_one_rectifier_status_service_per_rectifier(check):
    found = list(check.discover_oposs_eltek_sp2_rectifier_status(_section(check)))
    assert found == [Service(item=RECTIFIER_1), Service(item=RECTIFIER_2)]
    assert list(check.discover_oposs_eltek_sp2_rectifier_status({})) == []


def test_service_names(check):
    names = {
        p.name: p.service_name
        for p in vars(check).values()
        if type(p).__name__ == "CheckPlugin"
    }
    assert names == {
        "oposs_eltek_sp2_power_system_status": "Power System Status",
        "oposs_eltek_sp2_power_system_mode": "Power System Mode",
        "oposs_eltek_sp2_mains_voltage": "Mains Voltage %s",
        "oposs_eltek_sp2_mains_failure": "Mains Failure",
        "oposs_eltek_sp2_rectifier_count": "Number of Rectifiers",
        "oposs_eltek_sp2_rectifier_current": "Rectifier Current",
        "oposs_eltek_sp2_rectifier_capacity": "Rectifier Capacity",
        "oposs_eltek_sp2_rectifier_errors": "Rectifier Errors",
        "oposs_eltek_sp2_rectifier_temperature": "Rectifier Temperature",
        "oposs_eltek_sp2_rectifier_status": "Rectifier Status %s",
        "oposs_eltek_sp2_load_current": "Load Current",
    }


# ---------------------------------------------------------------------------
# A healthy system is OK everywhere
# ---------------------------------------------------------------------------

def test_power_system_status_normal(check):
    out = list(check.check_oposs_eltek_sp2_power_system_status(_section(check)))
    assert out == [Result(state=State.OK, summary="status normal")]


@pytest.mark.parametrize("value, state, text", [
    ("0", State.CRIT, "error"),
    ("2", State.WARN, "minorAlarm"),
    ("3", State.CRIT, "majorAlarm"),
    ("4", State.OK, "disabled"),
    ("5", State.UNKNOWN, "disconnected"),
    ("7", State.CRIT, "minorAndMajor"),
    ("18", State.CRIT, "critical"),
    ("19", State.WARN, "warning"),
    ("", State.UNKNOWN, "No Data"),
])
def test_power_system_status_states(check, value, state, text):
    section = _section(check, status=[[value]])
    out = list(check.check_oposs_eltek_sp2_power_system_status(section))
    assert out == [Result(state=state, summary=f"status {text}")]


@pytest.mark.parametrize("mode, state, text", [
    ("3", State.OK, "float"),
    ("2", State.OK, "boost"),
    ("1", State.OK, "test"),
    ("6", State.OK, "equalize"),
    ("5", State.OK, "startupdelay"),
    ("4", State.CRIT, "emergency"),
    ("0", State.UNKNOWN, "off"),
    ("9", State.OK, "unknown(9)"),
])
def test_power_system_mode(check, mode, state, text):
    out = list(check.check_oposs_eltek_sp2_power_system_mode(_section(check, mode=[[mode]])))
    assert out == [Result(state=state, summary=text)]


@pytest.mark.parametrize("value, state", [("0", State.OK), ("1", State.WARN), ("2", State.CRIT), ("3", State.CRIT)])
def test_mains_failure(check, value, state):
    out = list(check.check_oposs_eltek_sp2_mains_failure(_section(check, failure=[[value]])))
    assert out == [Result(state=state, summary=f"Number of failed phases: {value}")]


def test_rectifier_count(check):
    out = list(check.check_oposs_eltek_sp2_rectifier_count(_section(check)))
    assert out == [Result(state=State.OK, summary="2 Rectifiers Installed")]


def test_mains_voltage_ok(check):
    out = list(check.check_oposs_eltek_sp2_mains_voltage("Mains Voltage 2", _section(check)))
    assert _results(out) == [
        Result(state=State.OK, summary="Mains Voltage: 229 V"),
        Result(state=State.OK, summary="status normal"),
    ]
    assert _metrics(out) == [
        Metric("oposs_eltek_voltage", 229.0, levels=(260.0, 275.0), boundaries=(185.0, 275.0)),
    ]


def test_rectifier_current_ok(check):
    out = list(check.check_oposs_eltek_sp2_rectifier_current(_section(check)))
    assert _results(out) == [
        Result(state=State.OK, summary="Rectifier Current: 27.60 A"),
        Result(state=State.OK, summary="status normal"),
    ]
    assert _metrics(out) == [
        Metric("oposs_eltek_current", 27.6, levels=(100.0, 120.0), boundaries=(0.0, 144.0)),
    ]


def test_rectifier_capacity_ok(check):
    out = list(check.check_oposs_eltek_sp2_rectifier_capacity(_section(check)))
    assert _results(out) == [
        Result(state=State.OK, summary="Rectifier Capacity: 35 %"),
        Result(state=State.OK, summary="status normal"),
    ]
    assert _metrics(out) == [
        Metric("oposs_eltek_capacity_pct", 35.0, levels=(80.0, 90.0), boundaries=(0.0, 108.0)),
    ]


def test_rectifier_errors_ok(check):
    out = list(check.check_oposs_eltek_sp2_rectifier_errors(_section(check)))
    assert _results(out) == [
        Result(state=State.OK, summary="Rectifier Errors: 0 Errors"),
        Result(state=State.OK, summary="status normal"),
    ]
    assert _metrics(out) == [
        Metric("oposs_eltek_errors", 0.0, levels=(1.0, 2.0), boundaries=(0.0, 2.4)),
    ]


def test_rectifier_temperature_ok(check):
    out = list(check.check_oposs_eltek_sp2_rectifier_temperature(_section(check)))
    assert _results(out) == [
        Result(state=State.OK, summary="Rectifier Temperature: 28 C"),
        Result(state=State.OK, summary="status normal"),
    ]
    assert _metrics(out) == [
        Metric("oposs_eltek_temperature", 28.0, levels=(50.0, 60.0), boundaries=(0.0, 60.0)),
    ]


def test_load_current_ok(check):
    out = list(check.check_oposs_eltek_sp2_load_current(_section(check)))
    assert _results(out) == [
        Result(state=State.OK, summary="Load Current: 27.00 A"),
        Result(state=State.OK, summary="status normal"),
    ]
    assert _metrics(out) == [
        Metric("oposs_eltek_current", 27.0, levels=(130.0, 150.0), boundaries=(0.0, 180.0)),
    ]


def test_rectifier_status_ok(check):
    out = list(check.check_oposs_eltek_sp2_rectifier_status(RECTIFIER_1, _section(check)))
    assert out == [
        Result(state=State.OK, summary="Output Current 13.80 A / Input Voltage 232 V (status normal)"),
        Metric("oposs_eltek_current", 13.8),
        Metric("oposs_eltek_voltage", 232.0),
    ]


@pytest.mark.parametrize("value, state", [("3", State.CRIT), ("2", State.WARN), ("6", State.UNKNOWN)])
def test_rectifier_status_follows_the_device(check, value, state):
    rows = [[value, "0", "232", "Flatpack2 48/2000 HE", "113871234567 "]]
    out = list(check.check_oposs_eltek_sp2_rectifier_status(RECTIFIER_1, _section(check, rectifiers=rows)))
    assert _state(out) == state


# ---------------------------------------------------------------------------
# Thresholds from the device
# ---------------------------------------------------------------------------

def _mains(value):
    return [["1", "Mains Voltage 1", value, "260", "275", "200", "185"]]


@pytest.mark.parametrize("value, state", [
    ("259", State.OK),
    ("260", State.WARN),
    ("275", State.CRIT),
    ("201", State.OK),
    ("199", State.WARN),
    ("184", State.CRIT),
    ("0", State.CRIT),
])
def test_mains_voltage_levels(check, value, state):
    out = list(check.check_oposs_eltek_sp2_mains_voltage("Mains Voltage 1", _section(check, mains=_mains(value))))
    assert _state(out) == state


@pytest.mark.parametrize("value, state", [("999", State.OK), ("1000", State.WARN), ("1200", State.CRIT)])
def test_rectifier_current_levels(check, value, state):
    section = _section(check, current=[["1", value, "1000", "1200"]])
    assert _state(list(check.check_oposs_eltek_sp2_rectifier_current(section))) == state


@pytest.mark.parametrize("value, state", [("79", State.OK), ("80", State.WARN), ("95", State.CRIT)])
def test_rectifier_capacity_levels(check, value, state):
    section = _section(check, capacity=[["1", value, "90", "80"]])
    assert _state(list(check.check_oposs_eltek_sp2_rectifier_capacity(section))) == state


@pytest.mark.parametrize("value, state", [("0", State.OK), ("1", State.WARN), ("2", State.CRIT)])
def test_rectifier_errors_levels(check, value, state):
    section = _section(check, errors=[["1", value, "2", "1"]])
    assert _state(list(check.check_oposs_eltek_sp2_rectifier_errors(section))) == state


@pytest.mark.parametrize("value, state", [
    ("49", State.OK), ("50", State.WARN), ("61", State.CRIT),
    ("6", State.OK), ("4", State.WARN), ("-1", State.CRIT),
])
def test_rectifier_temperature_levels(check, value, state):
    section = _section(check, temperature=[["1", value, "60", "50", "5", "0"]])
    assert _state(list(check.check_oposs_eltek_sp2_rectifier_temperature(section))) == state


@pytest.mark.parametrize("value, state", [("1299", State.OK), ("1300", State.WARN), ("1500", State.CRIT)])
def test_load_current_levels(check, value, state):
    section = _section(check, load=[["1", value, "1500", "1300"]])
    assert _state(list(check.check_oposs_eltek_sp2_load_current(section))) == state


def test_threshold_text_shows_plain_levels(check):
    out = list(check.check_oposs_eltek_sp2_mains_voltage("Mains Voltage 1", _section(check, mains=_mains("265"))))
    assert _results(out) == [
        Result(state=State.WARN, summary="Mains Voltage: 265 V (warn/crit at 260 V/275 V)"),
        Result(state=State.OK, summary="status normal"),
    ]


def test_device_status_does_not_change_the_state(check):
    # The level checks take their state from the thresholds alone.
    rows = [["3", "Mains Voltage 1", "231", "260", "275", "200", "185"]]
    out = list(check.check_oposs_eltek_sp2_mains_voltage("Mains Voltage 1", _section(check, mains=rows)))
    assert _results(out)[-1] == Result(state=State.OK, summary="status majorAlarm")
    assert _state(out) == State.OK


# ---------------------------------------------------------------------------
# Missing items and garbage from the device
# ---------------------------------------------------------------------------

def test_vanished_items_give_no_result(check):
    section = _section(check)
    assert list(check.check_oposs_eltek_sp2_mains_voltage("Mains Voltage 9", section)) == []
    assert list(check.check_oposs_eltek_sp2_rectifier_status("Flatpack2 [0]", section)) == []


@pytest.mark.parametrize("name", SINGLE_SERVICES)
def test_vanished_data_gives_no_result(check, name):
    assert list(getattr(check, f"check_oposs_eltek_sp2_{name}")({})) == []


def test_unknown_status_code_is_unknown(check):
    out = list(check.check_oposs_eltek_sp2_power_system_status(_section(check, status=[["20"]])))
    assert out == [Result(state=State.UNKNOWN, summary="status unknown(20)")]


def test_unknown_rectifier_status_code_is_unknown(check):
    rows = [["99", "138", "232", "Flatpack2 48/2000 HE", "113871234567 "]]
    out = list(check.check_oposs_eltek_sp2_rectifier_status(RECTIFIER_1, _section(check, rectifiers=rows)))
    assert _results(out) == [
        Result(state=State.UNKNOWN, summary="Output Current 13.80 A / Input Voltage 232 V (status unknown(99))"),
    ]


def test_unknown_status_code_in_a_level_check_is_shown(check):
    # The level checks take their state from the thresholds alone, so an
    # unknown device status is only reported, as any other device status.
    out = list(check.check_oposs_eltek_sp2_load_current(_section(check, load=[["42", "270", "1500", "1300"]])))
    assert _results(out) == [
        Result(state=State.OK, summary="Load Current: 27.00 A"),
        Result(state=State.OK, summary="status unknown(42)"),
    ]


@pytest.mark.xfail(strict=True, raises=ValueError,
                   reason="BUG: an empty value from SNMP (missing OID) crashes the check (ValueError)")
@pytest.mark.parametrize("name, override", [
    ("mains_failure", {"failure": [[""]]}),
    ("rectifier_current", {"current": [["1", "", "1000", "1200"]]}),
    ("rectifier_temperature", {"temperature": [["1", "28", "60", "50", "", ""]]}),
])
def test_empty_snmp_value_does_not_crash(check, name, override):
    out = list(getattr(check, f"check_oposs_eltek_sp2_{name}")(_section(check, **override)))
    assert _results(out)

# ---------------------------------------------------------------------------
# Release version
# ---------------------------------------------------------------------------

def test_check_carries_the_released_version():
    # The publish check fails on main when a version file disagrees with
    # the newest released CHANGES.md heading.
    released = re.search(r"^## (\d+\.\d+\.\d+)", (ROOT / "CHANGES.md").read_text(),
                         flags=re.MULTILINE).group(1)
    assert re.search(rf'^__version__ = "{re.escape(released)}"$', CHECK.read_text(), flags=re.MULTILINE)


def test_release_writes_version_into_check(tmp_path):
    """Apply the version_files entry of .github/repo-infra.json to the check
    module, as Create release PR does (a multiline regex, first match)"""
    config = json.loads((ROOT / ".github/repo-infra.json").read_text())
    (spec,) = [f for f in config["version_files"] if (ROOT / f["path"]) == CHECK]
    stamped = re.sub(spec["pattern"], spec["replacement"].replace("$VERSION", "9.8.7"),
                     CHECK.read_text(), count=1, flags=re.MULTILINE)
    assert re.search(spec["verify"].replace("$VERSION", re.escape("9.8.7")), stamped, flags=re.MULTILINE)
    copy = tmp_path / "stamped_check.py"
    copy.write_text(stamped)
    module_spec = importlib.util.spec_from_file_location("stamped_check", copy)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    assert module.__version__ == "9.8.7"
