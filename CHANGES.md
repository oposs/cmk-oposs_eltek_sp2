# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### New
- The package carries the release version in its check plugin (`__version__`).

### Changed
- Licence is now GNU General Public License v2, matching the headers
  the source files carry. The `LICENSE` file previously held the MIT
  text, which contradicted them.

### Fixed
- Mains Voltage, Rectifier Current, Rectifier Capacity, Rectifier Errors,
  Rectifier Temperature and Load Current in WARN or CRIT showed the device
  status after each threshold, as in "warn/crit at 260 V (status
  normal)/275 V (status normal)". The thresholds now read "warn/crit at
  260 V/275 V", and the device status follows once, as "status normal".

## 0.1.1 - 2026-04-27
### Fixed
- Metric translations for legacy `eltek_sp2_*` history are now keyed on
  the new `oposs_eltek_sp2_*` check commands so they actually fire.
  Previously they were keyed on the now-uninstalled legacy commands and
  Checkmk's translation lookup (an exact match on the live service's
  current check command) silently missed them — leaving the legacy
  generic-named RRD files (`voltage.rrd`, `current.rrd`, `temperature.rrd`,
  `percentage.rrd`, `errors.rrd`) orphaned in the per-service directories.
  After upgrading and reloading (`cmk -R` / `omd restart apache`), graphs
  of the new `oposs_eltek_*` services on hosts that previously ran the
  legacy plugin will show one continuous line spanning the pre- and
  post-upgrade history.

## 0.1.0 - 2026-03-04
### New
- Initial migration from oegig-plugins to Checkmk 2.3.x v2 API
- Single SNMPSection with 11 SNMP tree fetches
- 11 check plugins: Power System Status, Power System Mode, Mains Voltage,
  Mains Failure, Number of Rectifiers, Rectifier Current, Rectifier Capacity,
  Rectifier Errors, Rectifier Temperature, Rectifier Status, Load Current
- Graphing definitions for voltage, current, temperature, capacity, and errors
- Metric names prefixed with `oposs_eltek_` for namespace isolation
- SNMP-provided thresholds preserved from device configuration


