# Changelog

## 2.0.1 - 2025-01-06
### Fixed
 * Deduplicate database entries by critique URL.

## 2.0.0 - 2024-09-28
### Added
 * Support "Tiptap" comments.
 * Introduce a comment cache to reduce the amount of requests.
 * Support the new deviation URL scheme.

### Changed
 * The CSV report's `block_url` column is now `batch_url`.
 * Stop post-processing timestamps.
 * Bump minimum Python version to 3.11.
 * Bump all dependencies to latest.
 * Stop guaranteeing a specific critique ordering in the CSV.
 * Hide progress bars after downloading.

### Removed
 * Stop fetching deviation artists.
 * Support for legacy "Writer" comments, irrelevant since at least 2020.
 * "Edited" timestamp for critiques and all timestamps for blocks, unused since their introduction.

## 1.0.2 - 2022-12-21
### Added
 * Support for Python 3.11.

### Changed
 * Bump all dependencies to latest.

### Fixed
 * Fix failed artist and comment fetching.

## 1.0.1 - 2022-01-15
### Fixed
 * Exclude comments to the critique journal from the database.

## 1.0.0 - 2021-10-14
### Added
 * Deviation artists to database.
 * Basic stats on fetched critiques.
 * Dependency on tqdm.
 * Dependency on aiohttp.

### Changed
 * Fetch URLs asynchronously.
 * Timestamp is now in the YYYY/MM/DD HH:MM format.
 * Bump all dependencies to latest.

### Removed
 * Database loading and updating.
 * Dependency on requests.

## 0.1.1 - 2021-01-24
### Changed
 * Update dependencies.

## 0.1.0 - 2021-01-24
### Added
 * Initial release.
