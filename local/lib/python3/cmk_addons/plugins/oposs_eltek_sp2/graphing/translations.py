#!/usr/bin/env python3
# Copyright (C) 2025 OETIKER+PARTNER AG - License: GNU General Public License v2

"""Metric translations for the Eltek Smartpack S v2 plugin rename."""

from cmk.graphing.v1 import translations

translation_eltek_sp2_mains_voltage = translations.Translation(
    name="eltek_sp2_mains_voltage",
    check_commands=[translations.PassiveCheck("eltek_sp2_mains_voltage")],
    translations={
        "voltage": translations.RenameTo("oposs_eltek_voltage"),
    },
)

translation_eltek_sp2_rectifier_current = translations.Translation(
    name="eltek_sp2_rectifier_current",
    check_commands=[translations.PassiveCheck("eltek_sp2_rectifier_current")],
    translations={
        "current": translations.RenameTo("oposs_eltek_current"),
    },
)

translation_eltek_sp2_rectifier_capacity = translations.Translation(
    name="eltek_sp2_rectifier_capacity",
    check_commands=[translations.PassiveCheck("eltek_sp2_rectifier_capacity")],
    translations={
        "percentage": translations.RenameTo("oposs_eltek_capacity_pct"),
    },
)

translation_eltek_sp2_rectifier_errors = translations.Translation(
    name="eltek_sp2_rectifier_errors",
    check_commands=[translations.PassiveCheck("eltek_sp2_rectifier_errors")],
    translations={
        "errors": translations.RenameTo("oposs_eltek_errors"),
    },
)

translation_eltek_sp2_rectifier_temperature = translations.Translation(
    name="eltek_sp2_rectifier_temperature",
    check_commands=[translations.PassiveCheck("eltek_sp2_rectifier_temperature")],
    translations={
        "temperature": translations.RenameTo("oposs_eltek_temperature"),
    },
)

translation_eltek_sp2_load_current = translations.Translation(
    name="eltek_sp2_load_current",
    check_commands=[translations.PassiveCheck("eltek_sp2_load_current")],
    translations={
        "current": translations.RenameTo("oposs_eltek_current"),
    },
)
