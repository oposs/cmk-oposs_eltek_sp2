# cmk-oposs_eltek_sp2

Checkmk SNMP plugin for Eltek Smartpack S power supply systems.
Migrated from oegig-plugins to Checkmk 2.3.x v2 API.

## Components

- `local/lib/python3/cmk_addons/plugins/oposs_eltek_sp2/agent_based/oposs_eltek_sp2.py` — SNMP section + 11 check plugins
- `local/lib/python3/cmk_addons/plugins/oposs_eltek_sp2/graphing/eltek_sp2.py` — metric, graph, perfometer definitions
- `.mkp-builder.ini` — MKP packaging config
- `.github/workflows/release.yml` — automated release workflow

## Architecture

- One `SNMPSection` with 11 `SNMPTree` fetches (scalar + table OIDs)
- Parse function builds a dict keyed by check type
- 11 `CheckPlugin` module-level variables, 2 item-based (mains_voltage, rectifier_status)
- Thresholds from SNMP device config, no rulesets needed
- Metric prefix: `oposs_eltek_`
