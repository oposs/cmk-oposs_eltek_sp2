#!/usr/bin/env python3

from typing import Any, Dict

from cmk.agent_based.v2 import (
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Metric,
    Result,
    Service,
    SNMPSection,
    SNMPTree,
    State,
    check_levels,
    startswith,
)

# State mapping from SNMP status values
stateMap = {
    "0": (State.CRIT, "error"),
    "1": (State.OK, "normal"),
    "2": (State.WARN, "minorAlarm"),
    "3": (State.CRIT, "majorAlarm"),
    "4": (State.OK, "disabled"),
    "5": (State.UNKNOWN, "disconnected"),
    "6": (State.UNKNOWN, "notPresent"),
    "7": (State.CRIT, "minorAndMajor"),
    "8": (State.CRIT, "majorLow"),
    "9": (State.WARN, "minorLow"),
    "10": (State.CRIT, "majorHigh"),
    "11": (State.WARN, "minorHigh"),
    "12": (State.UNKNOWN, "event"),
    "13": (State.UNKNOWN, "valueVolt"),
    "14": (State.UNKNOWN, "valueAmp"),
    "15": (State.UNKNOWN, "valueTemp"),
    "16": (State.UNKNOWN, "valueUnit"),
    "17": (State.UNKNOWN, "valuePerCent"),
    "18": (State.CRIT, "critical"),
    "19": (State.WARN, "warning"),
}


def stateValue(data: str) -> State:
    return State.UNKNOWN if data == "" else stateMap[data][0]


def stateInfo(data: str) -> str:
    return "No Data" if data == "" else stateMap[data][1]


MODE_MAP = {
    "0": "off",
    "1": "test",
    "2": "boost",
    "3": "float",
    "4": "emergency",
    "5": "startupdelay",
    "6": "equalize",
}

# SNMP base OID for Eltek Smartpack S
OB = ".1.3.6.1.4.1.12148.10."


def parse_oposs_eltek_sp2(string_table: list) -> Dict[str, Any]:
    """Parse SNMP data from all 11 trees into a structured dict."""
    section: Dict[str, Any] = {}

    # 0: Power System Status - scalar, 1 OID
    if string_table[0] and string_table[0][0]:
        section["power_system_status"] = {"state": string_table[0][0][0]}

    # 1: Power System Mode - scalar, 1 OID
    if string_table[1] and string_table[1][0]:
        section["power_system_mode"] = {"mode": string_table[1][0][0]}

    # 2: Mains Voltage - table (multiple rows)
    mains = {}
    for row in string_table[2]:
        if len(row) >= 7:
            desc = row[1].strip()
            mains[desc] = {
                "state": row[0],
                "desc": desc,
                "value": row[2],
                "warnUp": row[3],
                "critUp": row[4],
                "warnLow": row[5],
                "critLow": row[6],
            }
    if mains:
        section["mains_voltage"] = mains

    # 3: Mains Failure - scalar, 1 OID
    if string_table[3] and string_table[3][0]:
        section["mains_failure"] = {"value": string_table[3][0][0]}

    # 4: Number of Rectifiers - scalar, 1 OID
    if string_table[4] and string_table[4][0]:
        section["rectifier_count"] = {"count": string_table[4][0][0]}

    # 5: Rectifier Current - scalar, 4 OIDs
    if string_table[5] and string_table[5][0]:
        row = string_table[5][0]
        if len(row) >= 4:
            section["rectifier_current"] = {
                "state": row[0],
                "value": row[1],
                "warnUp": row[2],
                "critUp": row[3],
            }

    # 6: Rectifier Capacity - scalar, 4 OIDs
    if string_table[6] and string_table[6][0]:
        row = string_table[6][0]
        if len(row) >= 4:
            section["rectifier_capacity"] = {
                "state": row[0],
                "value": row[1],
                "critUp": row[2],
                "warnUp": row[3],
            }

    # 7: Rectifier Errors - scalar, 4 OIDs
    if string_table[7] and string_table[7][0]:
        row = string_table[7][0]
        if len(row) >= 4:
            section["rectifier_errors"] = {
                "state": row[0],
                "value": row[1],
                "critUp": row[2],
                "warnUp": row[3],
            }

    # 8: Rectifier Temperature - scalar, 6 OIDs
    if string_table[8] and string_table[8][0]:
        row = string_table[8][0]
        if len(row) >= 6:
            section["rectifier_temperature"] = {
                "state": row[0],
                "value": row[1],
                "critUp": row[2],
                "warnUp": row[3],
                "warnLow": row[4],
                "critLow": row[5],
            }

    # 9: Rectifier Status - table (multiple rows)
    rectifiers = {}
    for row in string_table[9]:
        if len(row) >= 5:
            key = "%s [%s]" % (row[3], row[4].strip())
            rectifiers[key] = {
                "state": row[0],
                "outI": row[1],
                "inU": row[2],
                "type": row[3],
                "serial": row[4],
            }
    if rectifiers:
        section["rectifier_status"] = rectifiers

    # 10: Load Current - scalar, 4 OIDs
    if string_table[10] and string_table[10][0]:
        row = string_table[10][0]
        if len(row) >= 4:
            section["load_current"] = {
                "state": row[0],
                "value": row[1],
                "critUp": row[2],
                "warnUp": row[3],
            }

    return section


snmp_section_oposs_eltek_sp2 = SNMPSection(
    name="oposs_eltek_sp2",
    detect=startswith(".1.3.6.1.4.1.12148.10.2.6.0", "Smartpack S"),
    parse_function=parse_oposs_eltek_sp2,
    fetch=[
        # 0: Power System Status
        SNMPTree(base=OB + "2", oids=["1.0"]),
        # 1: Power System Mode
        SNMPTree(base=OB + "2", oids=["3.0"]),
        # 2: Mains Voltage Table
        SNMPTree(
            base=OB + "3.4.1",
            oids=["2", "3", "6", "8", "7", "9", "10"],
        ),
        # 3: Mains Failure
        SNMPTree(base=OB + "3.2", oids=["5.0"]),
        # 4: Number of Rectifiers
        SNMPTree(base=OB + "5", oids=["5.0"]),
        # 5: Rectifier Current
        SNMPTree(base=OB + "5.2", oids=["1.0", "5.0", "7.0", "6.0"]),
        # 6: Rectifier Capacity
        SNMPTree(base=OB + "5.3", oids=["1.0", "5.0", "6.0", "7.0"]),
        # 7: Rectifier Errors
        SNMPTree(base=OB + "5.4", oids=["1.0", "5.0", "6.0", "7.0"]),
        # 8: Rectifier Temperature
        SNMPTree(
            base=OB + "5.18",
            oids=["1.0", "5.0", "6.0", "7.0", "8.0", "9.0"],
        ),
        # 9: Rectifier Status Table
        SNMPTree(base=OB + "5.6.1", oids=["2", "3", "4", "5", "10"]),
        # 10: Load Current
        SNMPTree(base=OB + "9.2", oids=["1.0", "5.0", "6.0", "7.0"]),
    ],
)


# ---------------------------------------------------------------------------
# Power System Status
# ---------------------------------------------------------------------------

def discover_oposs_eltek_sp2_power_system_status(
    section: Dict[str, Any],
) -> DiscoveryResult:
    if "power_system_status" in section:
        yield Service()


def check_oposs_eltek_sp2_power_system_status(
    section: Dict[str, Any],
) -> CheckResult:
    data = section.get("power_system_status")
    if not data:
        return
    yield Result(
        state=stateValue(data["state"]),
        summary="status %s" % stateInfo(data["state"]),
    )


check_plugin_oposs_eltek_sp2_power_system_status = CheckPlugin(
    name="oposs_eltek_sp2_power_system_status",
    sections=["oposs_eltek_sp2"],
    service_name="Power System Status",
    discovery_function=discover_oposs_eltek_sp2_power_system_status,
    check_function=check_oposs_eltek_sp2_power_system_status,
)


# ---------------------------------------------------------------------------
# Power System Mode
# ---------------------------------------------------------------------------

def discover_oposs_eltek_sp2_power_system_mode(
    section: Dict[str, Any],
) -> DiscoveryResult:
    if "power_system_mode" in section:
        yield Service()


def check_oposs_eltek_sp2_power_system_mode(
    section: Dict[str, Any],
) -> CheckResult:
    data = section.get("power_system_mode")
    if not data:
        return
    mode = data["mode"]
    if mode == "0":
        state = State.UNKNOWN
    elif mode == "4":
        state = State.CRIT
    else:
        state = State.OK
    yield Result(
        state=state,
        summary=MODE_MAP.get(mode, "unknown(%s)" % mode),
    )


check_plugin_oposs_eltek_sp2_power_system_mode = CheckPlugin(
    name="oposs_eltek_sp2_power_system_mode",
    sections=["oposs_eltek_sp2"],
    service_name="Power System Mode",
    discovery_function=discover_oposs_eltek_sp2_power_system_mode,
    check_function=check_oposs_eltek_sp2_power_system_mode,
)


# ---------------------------------------------------------------------------
# Mains Voltage (item-based)
# ---------------------------------------------------------------------------

def discover_oposs_eltek_sp2_mains_voltage(
    section: Dict[str, Any],
) -> DiscoveryResult:
    for key in section.get("mains_voltage", {}):
        yield Service(item=key)


def check_oposs_eltek_sp2_mains_voltage(
    item: str, section: Dict[str, Any],
) -> CheckResult:
    data = section.get("mains_voltage", {}).get(item)
    if not data:
        return
    result, metric = check_levels(
        value=float(data["value"]),
        levels_upper=(float(data["warnUp"]), float(data["critUp"])),
        levels_lower=(float(data["warnLow"]), float(data["critLow"])),
        boundaries=(float(data["critLow"]), float(data["critUp"])),
        metric_name="oposs_eltek_voltage",
        render_func=lambda v: "%.0f V (status %s)" % (v, stateInfo(data["state"])),
        label="Mains Voltage",
    )
    yield result
    yield metric


check_plugin_oposs_eltek_sp2_mains_voltage = CheckPlugin(
    name="oposs_eltek_sp2_mains_voltage",
    sections=["oposs_eltek_sp2"],
    service_name="Mains Voltage %s",
    discovery_function=discover_oposs_eltek_sp2_mains_voltage,
    check_function=check_oposs_eltek_sp2_mains_voltage,
)


# ---------------------------------------------------------------------------
# Mains Failure
# ---------------------------------------------------------------------------

def discover_oposs_eltek_sp2_mains_failure(
    section: Dict[str, Any],
) -> DiscoveryResult:
    if "mains_failure" in section:
        yield Service()


def check_oposs_eltek_sp2_mains_failure(
    section: Dict[str, Any],
) -> CheckResult:
    data = section.get("mains_failure")
    if not data:
        return
    value = float(data["value"])
    if value > 1:
        state = State.CRIT
    elif value > 0:
        state = State.WARN
    else:
        state = State.OK
    yield Result(
        state=state,
        summary="Number of failed phases: %s" % data["value"],
    )


check_plugin_oposs_eltek_sp2_mains_failure = CheckPlugin(
    name="oposs_eltek_sp2_mains_failure",
    sections=["oposs_eltek_sp2"],
    service_name="Mains Failure",
    discovery_function=discover_oposs_eltek_sp2_mains_failure,
    check_function=check_oposs_eltek_sp2_mains_failure,
)


# ---------------------------------------------------------------------------
# Number of Rectifiers
# ---------------------------------------------------------------------------

def discover_oposs_eltek_sp2_rectifier_count(
    section: Dict[str, Any],
) -> DiscoveryResult:
    if "rectifier_count" in section:
        yield Service()


def check_oposs_eltek_sp2_rectifier_count(
    section: Dict[str, Any],
) -> CheckResult:
    data = section.get("rectifier_count")
    if not data:
        return
    yield Result(
        state=State.OK,
        summary="%s Rectifiers Installed" % data["count"],
    )


check_plugin_oposs_eltek_sp2_rectifier_count = CheckPlugin(
    name="oposs_eltek_sp2_rectifier_count",
    sections=["oposs_eltek_sp2"],
    service_name="Number of Rectifiers",
    discovery_function=discover_oposs_eltek_sp2_rectifier_count,
    check_function=check_oposs_eltek_sp2_rectifier_count,
)


# ---------------------------------------------------------------------------
# Rectifier Current
# ---------------------------------------------------------------------------

def discover_oposs_eltek_sp2_rectifier_current(
    section: Dict[str, Any],
) -> DiscoveryResult:
    if "rectifier_current" in section:
        yield Service()


def check_oposs_eltek_sp2_rectifier_current(
    section: Dict[str, Any],
) -> CheckResult:
    data = section.get("rectifier_current")
    if not data:
        return
    result, metric = check_levels(
        value=float(data["value"]) / 10.0,
        levels_upper=(float(data["warnUp"]) / 10.0, float(data["critUp"]) / 10.0),
        boundaries=(0.0, 1.2 * float(data["critUp"]) / 10.0),
        metric_name="oposs_eltek_current",
        render_func=lambda v: "%.2f A (status %s)" % (v, stateInfo(data["state"])),
        label="Rectifier Current",
    )
    yield result
    yield metric


check_plugin_oposs_eltek_sp2_rectifier_current = CheckPlugin(
    name="oposs_eltek_sp2_rectifier_current",
    sections=["oposs_eltek_sp2"],
    service_name="Rectifier Current",
    discovery_function=discover_oposs_eltek_sp2_rectifier_current,
    check_function=check_oposs_eltek_sp2_rectifier_current,
)


# ---------------------------------------------------------------------------
# Rectifier Capacity
# ---------------------------------------------------------------------------

def discover_oposs_eltek_sp2_rectifier_capacity(
    section: Dict[str, Any],
) -> DiscoveryResult:
    if "rectifier_capacity" in section:
        yield Service()


def check_oposs_eltek_sp2_rectifier_capacity(
    section: Dict[str, Any],
) -> CheckResult:
    data = section.get("rectifier_capacity")
    if not data:
        return
    result, metric = check_levels(
        value=float(data["value"]),
        levels_upper=(float(data["warnUp"]), float(data["critUp"])),
        boundaries=(0.0, 1.2 * float(data["critUp"])),
        metric_name="oposs_eltek_capacity_pct",
        render_func=lambda v: "%.0f %% (status %s)" % (v, stateInfo(data["state"])),
        label="Rectifier Capacity",
    )
    yield result
    yield metric


check_plugin_oposs_eltek_sp2_rectifier_capacity = CheckPlugin(
    name="oposs_eltek_sp2_rectifier_capacity",
    sections=["oposs_eltek_sp2"],
    service_name="Rectifier Capacity",
    discovery_function=discover_oposs_eltek_sp2_rectifier_capacity,
    check_function=check_oposs_eltek_sp2_rectifier_capacity,
)


# ---------------------------------------------------------------------------
# Rectifier Errors
# ---------------------------------------------------------------------------

def discover_oposs_eltek_sp2_rectifier_errors(
    section: Dict[str, Any],
) -> DiscoveryResult:
    if "rectifier_errors" in section:
        yield Service()


def check_oposs_eltek_sp2_rectifier_errors(
    section: Dict[str, Any],
) -> CheckResult:
    data = section.get("rectifier_errors")
    if not data:
        return
    result, metric = check_levels(
        value=float(data["value"]),
        levels_upper=(float(data["warnUp"]), float(data["critUp"])),
        boundaries=(0.0, 1.2 * float(data["critUp"])),
        metric_name="oposs_eltek_errors",
        render_func=lambda v: "%.0f Errors (status %s)" % (v, stateInfo(data["state"])),
        label="Rectifier Errors",
    )
    yield result
    yield metric


check_plugin_oposs_eltek_sp2_rectifier_errors = CheckPlugin(
    name="oposs_eltek_sp2_rectifier_errors",
    sections=["oposs_eltek_sp2"],
    service_name="Rectifier Errors",
    discovery_function=discover_oposs_eltek_sp2_rectifier_errors,
    check_function=check_oposs_eltek_sp2_rectifier_errors,
)


# ---------------------------------------------------------------------------
# Rectifier Temperature
# ---------------------------------------------------------------------------

def discover_oposs_eltek_sp2_rectifier_temperature(
    section: Dict[str, Any],
) -> DiscoveryResult:
    if "rectifier_temperature" in section:
        yield Service()


def check_oposs_eltek_sp2_rectifier_temperature(
    section: Dict[str, Any],
) -> CheckResult:
    data = section.get("rectifier_temperature")
    if not data:
        return
    result, metric = check_levels(
        value=float(data["value"]),
        levels_upper=(float(data["warnUp"]), float(data["critUp"])),
        levels_lower=(float(data["warnLow"]), float(data["critLow"])),
        boundaries=(float(data["critLow"]), float(data["critUp"])),
        metric_name="oposs_eltek_temperature",
        render_func=lambda v: "%.0f C (status %s)" % (v, stateInfo(data["state"])),
        label="Rectifier Temperature",
    )
    yield result
    yield metric


check_plugin_oposs_eltek_sp2_rectifier_temperature = CheckPlugin(
    name="oposs_eltek_sp2_rectifier_temperature",
    sections=["oposs_eltek_sp2"],
    service_name="Rectifier Temperature",
    discovery_function=discover_oposs_eltek_sp2_rectifier_temperature,
    check_function=check_oposs_eltek_sp2_rectifier_temperature,
)


# ---------------------------------------------------------------------------
# Rectifier Status (item-based)
# ---------------------------------------------------------------------------

def discover_oposs_eltek_sp2_rectifier_status(
    section: Dict[str, Any],
) -> DiscoveryResult:
    for key in section.get("rectifier_status", {}):
        yield Service(item=key)


def check_oposs_eltek_sp2_rectifier_status(
    item: str, section: Dict[str, Any],
) -> CheckResult:
    data = section.get("rectifier_status", {}).get(item)
    if not data:
        return
    yield Result(
        state=stateValue(data["state"]),
        summary="Output Current %.2f A / Input Voltage %.0f V (status %s)"
        % (float(data["outI"]) / 10.0, float(data["inU"]), stateInfo(data["state"])),
    )
    yield Metric(
        name="oposs_eltek_current",
        value=float(data["outI"]) / 10.0,
    )
    yield Metric(
        name="oposs_eltek_voltage",
        value=float(data["inU"]),
    )


check_plugin_oposs_eltek_sp2_rectifier_status = CheckPlugin(
    name="oposs_eltek_sp2_rectifier_status",
    sections=["oposs_eltek_sp2"],
    service_name="Rectifier Status %s",
    discovery_function=discover_oposs_eltek_sp2_rectifier_status,
    check_function=check_oposs_eltek_sp2_rectifier_status,
)


# ---------------------------------------------------------------------------
# Load Current
# ---------------------------------------------------------------------------

def discover_oposs_eltek_sp2_load_current(
    section: Dict[str, Any],
) -> DiscoveryResult:
    if "load_current" in section:
        yield Service()


def check_oposs_eltek_sp2_load_current(
    section: Dict[str, Any],
) -> CheckResult:
    data = section.get("load_current")
    if not data:
        return
    result, metric = check_levels(
        value=float(data["value"]) / 10.0,
        levels_upper=(float(data["warnUp"]) / 10.0, float(data["critUp"]) / 10.0),
        boundaries=(0.0, 1.2 * float(data["critUp"]) / 10.0),
        metric_name="oposs_eltek_current",
        render_func=lambda v: "%.2f A (status %s)" % (v, stateInfo(data["state"])),
        label="Load Current",
    )
    yield result
    yield metric


check_plugin_oposs_eltek_sp2_load_current = CheckPlugin(
    name="oposs_eltek_sp2_load_current",
    sections=["oposs_eltek_sp2"],
    service_name="Load Current",
    discovery_function=discover_oposs_eltek_sp2_load_current,
    check_function=check_oposs_eltek_sp2_load_current,
)
