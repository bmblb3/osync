# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2025-08-29

### Changed

- Modify flake.nix according to [these instructions](https://pyproject-nix.github.io/uv2nix/patterns/applications.html)
so that it could be possible to include it in a system flake

## [0.2.0] - 2025-08-29

### Added

- Use an Enum ("kind") for include / exclude patterns

### Fixed

- Simplify a lot of the code, merge tests
- Use an Enum ("direction") for push / pull

## [0.1.0] - 2025-08-28

### Added

- Working app
