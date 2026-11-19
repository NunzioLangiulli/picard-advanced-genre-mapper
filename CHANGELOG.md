# Changelog

## 1.2.12

- Align README, plugin description, options help and comparison messages with initial Lookup selection, ongoing current-value uniformity and explicit manual actions.
- Clarify cached manual fallback versus live current-value counting, comparison draft initialization, partial albums, unknown-only results and unanimous manual edits.
- Explain that output-setting changes do not automatically rewrite unanimous albums and that the example tester does not simulate selection or storage.
- Documentation and interface wording only; genre-processing behavior is unchanged from 1.2.11.

## 1.2.11

- Keep complete albums uniform using the most frequent normalized complete list from current file genres after two stable checks.
- Preserve unanimous manual changes exactly and never restore original genres or saved comparison choices during ongoing synchronization.
- Keep summary-only behavior when automatic processing is disabled; saving still triggers no rules.
- Add regression coverage for 9-to-1 majorities, whole-album edits, aliases, ties, partial albums and batch stability.

## 1.2.10

- Synchronize the album row with unanimous current file genres without applying rules or modifying tracks/files.
- Preserve exact manual spelling, order and multiple values; clear mixed or partial summaries.
- Refresh already-loaded albums independently of automatic normalization and stop on disable.
- Add regression tests for manual edits, mixed/empty values, partial albums and refresh scope.

## 1.2.9

- Apply automatically only once after the first complete album match.
- Remove the pre-save processor so manual genre edits survive saving with automatic processing enabled.
- Wait for all tracks to be matched; refreshes and later matching events do not repeat completed processing.
- Keep explicit manual actions available and cancel pending automatic application after a manual application.
- Add Rate Your Music artist and album links with search fallback in the comparison dialog.
- Update options, documentation and regression tests.

## 1.2.8

- Normalize Rhythm&Blues, R&B and RnB to the single canonical spelling R&B.
- Deduplicate these aliases when they occur together in a genre list.
- Clarify canonical rules versus aliases and update migration guidance and tests.

## 1.2.7

- Preserve the full-name Rhythm&Blues spelling separately from R&B in the defaults.
- Add RnB -> R&B while retaining the R&B, Drum&Bass and Rock&Roll rules.
- Update examples, saved-dictionary migration instructions and regression tests.

## 1.2.6

- Add default Rhythm&Blues -> R&B and Drum&Bass -> Drum 'n' Bass mappings.
- Document one rule per genre for every connector variant, including existing saved dictionaries.
- Matching behavior is unchanged from 1.2.5.

## 1.2.5

- Match and, &, n and quoted n as equivalent genre connectors, including curly apostrophes.
- Preserve the exact output spelling on the right of each rule.
- Explain conflicts between equivalent aliases with different output spellings.

## 1.2.4

- Fix automatic and manual normalization when original file genres are empty but Lookup supplies current track genres.
- Keep source counts separate and prevent generated output from distorting repeated or incremental processing.
- Leave unmatched track templates intact until their files arrive.

## 1.2.3

- Remove duplicate documentation and Python caches; consolidate contributor and release instructions.

## 1.2.2

- Rename to Advanced Genre Mapper and credit Borunzio.
- Display manifest version and author in the options page.
- Add public-facing README, contribution and release guides.

## 1.2.1

- Compare transformations within each source, not across sources.
- Clarify existing-file selection, source retrieval and multi-value output.
- Separate spelling rules from the example tester; use the native Restore Defaults action.

## 1.2.0

- Add MusicBrainz release, release-group and artist source review.
- Preserve an applied selection through automatic updates during the loaded album session.

## 1.1.0

- Add automatic normalization and editable English options.

## 1.0.0

- Initial manual album genre normalization.
