# Changelog

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
