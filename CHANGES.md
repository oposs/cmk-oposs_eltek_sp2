# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### New

- Initial migration from oegig-plugins to Checkmk 2.3.x v2 API
- Single SNMPSection with 11 SNMP tree fetches
- 11 check plugins: Power System Status, Power System Mode, Mains Voltage,
  Mains Failure, Number of Rectifiers, Rectifier Current, Rectifier Capacity,
  Rectifier Errors, Rectifier Temperature, Rectifier Status, Load Current
- Graphing definitions for voltage, current, temperature, capacity, and errors
- Metric names prefixed with `oposs_eltek_` for namespace isolation
- SNMP-provided thresholds preserved from device configuration

### Changed

### Fixed
