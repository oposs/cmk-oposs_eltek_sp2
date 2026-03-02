# Eltek Smartpack S Checkmk Plugin

Checkmk SNMP plugin for monitoring Eltek Smartpack S power supply systems.

## Features

Monitors Eltek Smartpack S devices via SNMP with 11 services:

| Service | Type | Metrics |
|---------|------|---------|
| Power System Status | Scalar | Status state |
| Power System Mode | Scalar | Operating mode (float/boost/test/...) |
| Mains Voltage | Per-phase | Voltage with SNMP-provided thresholds |
| Mains Failure | Scalar | Failed phase count |
| Number of Rectifiers | Scalar | Installed rectifier count |
| Rectifier Current | Scalar | Current with SNMP thresholds |
| Rectifier Capacity | Scalar | Capacity % with SNMP thresholds |
| Rectifier Errors | Scalar | Error count with SNMP thresholds |
| Rectifier Temperature | Scalar | Temperature with SNMP thresholds |
| Rectifier Status | Per-rectifier | Output current, input voltage, status |
| Load Current | Scalar | Current with SNMP thresholds |

## SNMP Detection

The plugin detects devices where OID `.1.3.6.1.4.1.12148.10.2.6.0` starts
with `Smartpack S`.

Enterprise OID base: `.1.3.6.1.4.1.12148.10`

## Thresholds

All warn/crit thresholds are read from the device via SNMP. No ruleset
configuration is needed.

## Installation

### MKP Package (recommended)

Download the latest `.mkp` file from the
[Releases](https://github.com/oposs/cmk-oposs_eltek_sp2/releases) page and
install it:

```bash
mkp install oposs_eltek_sp2-<version>.mkp
```

### Manual Installation

Copy the plugin files into your Checkmk site:

```
local/lib/python3/cmk_addons/plugins/oposs_eltek_sp2/
├── agent_based/
│   └── oposs_eltek_sp2.py
└── graphing/
    └── eltek_sp2.py
```

## Troubleshooting

Test SNMP connectivity:

```bash
snmpget -v2c -c <community> <host> .1.3.6.1.4.1.12148.10.2.6.0
```

Expected output contains `Smartpack S`.

## License

MIT - OETIKER+PARTNER AG
