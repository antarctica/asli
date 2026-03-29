# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Breaking changes
+ Command line interface has changed from `asli_calc` type separated program structure to one main program with subcommands, e.g. `asli calc`
  + `asli_calc` is now `asli calc`
  + `asli_data_lsm` is now `asli download --lsm`
  + `asli_data_era5` is now `asli download`
  + `asli_plot` is now `asli plot`
+ `--datadir` option for `asli calc` and `asli plot` has been removed; with the corresponding arguments in the python interface to `ASLICalculator` being removed. Data paths are now specified as full paths in order to improve user experience in the command line interface via utilising normal tab completion.
+ `filename` argument is changed to `filepath` throughout, reflecting change from specifying files relative to `data_dir`.

## 0.1.0 - 2026-03-20
