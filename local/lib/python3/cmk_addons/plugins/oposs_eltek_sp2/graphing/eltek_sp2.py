#!/usr/bin/env python3

from cmk.graphing.v1 import Title
from cmk.graphing.v1.metrics import (
    Color,
    DecimalNotation,
    Metric,
    Unit,
)
from cmk.graphing.v1.graphs import Graph, MinimalRange
from cmk.graphing.v1.perfometers import Perfometer, FocusRange, Closed

# Units
unit_volts = Unit(DecimalNotation("V"))
unit_amperes = Unit(DecimalNotation("A"))
unit_celsius = Unit(DecimalNotation("\u00b0C"))
unit_percentage = Unit(DecimalNotation("%"))
unit_count = Unit(DecimalNotation(""))

# Metrics
metric_oposs_eltek_voltage = Metric(
    name="oposs_eltek_voltage",
    title=Title("Voltage"),
    unit=unit_volts,
    color=Color.BLUE,
)

metric_oposs_eltek_current = Metric(
    name="oposs_eltek_current",
    title=Title("Current"),
    unit=unit_amperes,
    color=Color.GREEN,
)

metric_oposs_eltek_temperature = Metric(
    name="oposs_eltek_temperature",
    title=Title("Temperature"),
    unit=unit_celsius,
    color=Color.ORANGE,
)

metric_oposs_eltek_capacity_pct = Metric(
    name="oposs_eltek_capacity_pct",
    title=Title("Capacity"),
    unit=unit_percentage,
    color=Color.YELLOW,
)

metric_oposs_eltek_errors = Metric(
    name="oposs_eltek_errors",
    title=Title("Errors"),
    unit=unit_count,
    color=Color.RED,
)

# Graphs
graph_oposs_eltek_voltage = Graph(
    name="oposs_eltek_voltage",
    title=Title("Eltek Voltage"),
    simple_lines=["oposs_eltek_voltage"],
)

graph_oposs_eltek_current = Graph(
    name="oposs_eltek_current",
    title=Title("Eltek Current"),
    simple_lines=["oposs_eltek_current"],
)

graph_oposs_eltek_temperature = Graph(
    name="oposs_eltek_temperature",
    title=Title("Eltek Temperature"),
    simple_lines=["oposs_eltek_temperature"],
    minimal_range=MinimalRange(lower=0, upper=50),
)

graph_oposs_eltek_capacity = Graph(
    name="oposs_eltek_capacity",
    title=Title("Eltek Rectifier Capacity"),
    simple_lines=["oposs_eltek_capacity_pct"],
    minimal_range=MinimalRange(lower=0, upper=100),
)

graph_oposs_eltek_errors = Graph(
    name="oposs_eltek_errors",
    title=Title("Eltek Rectifier Errors"),
    simple_lines=["oposs_eltek_errors"],
)

# Perfometers
perfometer_oposs_eltek_capacity_pct = Perfometer(
    name="oposs_eltek_capacity_pct",
    focus_range=FocusRange(
        lower=Closed(0),
        upper=Closed(100),
    ),
    segments=["oposs_eltek_capacity_pct"],
)
