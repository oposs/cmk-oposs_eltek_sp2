#!/usr/bin/env python3
# Copyright (C) 2025 OETIKER+PARTNER AG - License: GNU General Public License v2

"""Metric translations for the Eltek Smartpack S v2 plugin rename.

The legacy plugin used check commands ``eltek_sp2_*`` with generic metric
names (``voltage``, ``current``, ``percentage``, ``errors``,
``temperature``).  This plugin uses ``oposs_eltek_sp2_*`` check commands
and prefixed ``oposs_eltek_*`` metrics.

IMPORTANT: ``check_commands`` MUST reference the *new* check command (the
one the live service has today). Checkmk's translation lookup
(``cmk/gui/graphing/_translated_metrics.py``,
``lookup_metric_translations_for_check_command``) is an exact dict-key
match against that command — entries keyed on the legacy ``eltek_sp2_*``
commands would never fire after the legacy plugin is uninstalled, leaving
the legacy generic-named RRD files orphaned in the per-service directories.
Service names are unchanged across both plugins, so the legacy
``voltage.rrd`` etc. coexist with the new ``oposs_eltek_voltage.rrd`` in
the same directory and the rename below stitches them into one continuous
graph.
"""

from cmk.graphing.v1 import translations

translation_oposs_eltek_sp2_mains_voltage = translations.Translation(
    name="oposs_eltek_sp2_mains_voltage",
    check_commands=[translations.PassiveCheck("oposs_eltek_sp2_mains_voltage")],
    translations={
        "voltage": translations.RenameTo("oposs_eltek_voltage"),
    },
)

translation_oposs_eltek_sp2_rectifier_current = translations.Translation(
    name="oposs_eltek_sp2_rectifier_current",
    check_commands=[translations.PassiveCheck("oposs_eltek_sp2_rectifier_current")],
    translations={
        "current": translations.RenameTo("oposs_eltek_current"),
    },
)

translation_oposs_eltek_sp2_rectifier_capacity = translations.Translation(
    name="oposs_eltek_sp2_rectifier_capacity",
    check_commands=[translations.PassiveCheck("oposs_eltek_sp2_rectifier_capacity")],
    translations={
        "percentage": translations.RenameTo("oposs_eltek_capacity_pct"),
    },
)

translation_oposs_eltek_sp2_rectifier_errors = translations.Translation(
    name="oposs_eltek_sp2_rectifier_errors",
    check_commands=[translations.PassiveCheck("oposs_eltek_sp2_rectifier_errors")],
    translations={
        "errors": translations.RenameTo("oposs_eltek_errors"),
    },
)

translation_oposs_eltek_sp2_rectifier_temperature = translations.Translation(
    name="oposs_eltek_sp2_rectifier_temperature",
    check_commands=[translations.PassiveCheck("oposs_eltek_sp2_rectifier_temperature")],
    translations={
        "temperature": translations.RenameTo("oposs_eltek_temperature"),
    },
)

translation_oposs_eltek_sp2_load_current = translations.Translation(
    name="oposs_eltek_sp2_load_current",
    check_commands=[translations.PassiveCheck("oposs_eltek_sp2_load_current")],
    translations={
        "current": translations.RenameTo("oposs_eltek_current"),
    },
)
