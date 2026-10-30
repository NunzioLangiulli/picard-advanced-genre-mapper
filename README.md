# Advanced Genre Mapper

**Version:** 1.2.8 · **Author:** Borunzio · **Target:** Picard 3.0.2

Normalize genre spelling and review album-level genres without mixing the original data sources.

> Development status: logic tests pass; the latest Qt layouts and full Lookup/save workflow still need live validation.



## Install / Update

This folder is a local Git repository. Use Picard's Local repository plugin
installer to update/reinstall from this folder, then restart Picard.
The plugin UUID is unchanged, so this replaces Album Genres - Personal Format
and retains its saved spelling rules. Keep the .git folder for installation.


## Options

Options > Plugins > Advanced Genre Mapper
All interface text, comments and documentation are in English.
The automatic checkbox controls application after matching and before saving.
The plugin does not save audio files automatically.
For already loaded albums, use the album context action Apply album genre rules now.


## How File Genres Are Chosen (Fixed Rule)

The most frequent COMPLETE normalized genre list among matched tracks wins.
For example, if 7 tracks contain Electronic; IDM and 3 contain Jazz, every
track receives Electronic; IDM. Genres are not counted individually and
unrelated lists are not combined automatically.
Lists with identical genres in different orders count as the same list.
Each matched track casts one vote. For multiple files linked to the same
track, the first non-empty normalized file list is used.
Empty lists are ignored. A tie is resolved using the first tied list in
album track order. If all original-file lists are empty, the plugin uses the most frequent complete list among current track genres (the New value column). If both sources are empty, nothing changes.
Load all tracks and all discs before applying or saving.
This policy is fixed, not an optional selection strategy.

Original file genres take priority. If none remain after normalization, current track genres are counted separately as a fallback. Original and current sources are never mixed in one count. The plugin remembers its own output so applying repeatedly does not distort the counts. Inputs are captured once per loaded file, preventing an early
partial-album result from distorting later votes. Remove and reload files
after changing source tags on disk. Saved results become the original genres
when files are loaded again.


## Compare Sources

Right-click a matched album > Plugins > Compare album genres...
The window shows:
- Existing files: the most frequent complete genre list.
- MusicBrainz release: the matched edition.
- MusicBrainz release group: the album across editions.
- MusicBrainz album artists: one independent row for each credited artist.

MusicBrainz requests start when the comparison window opens. They use
Picard's MusicBrainz connection and request queue. No RYM integration exists.
All official MusicBrainz genres with positive vote counts are shown; counts
appear in parentheses. Picard's genre threshold, maximum count, personal
genre and folksonomy settings are not applied to these comparison requests.
This is deliberate: the window presents independent sources for review.
Successful responses are cached for the plugin session. Failed requests can
be retried by closing and reopening the window. Restart Picard to refresh
successful cached responses after editing genres on MusicBrainz.

Each row compares its own original genres with the result of your spelling
rules. Changes within this source lists spelling changes, removed unknown
genres, removed duplicates and normalized separators. It never compares
genres from different sources. Retrieval status describes whether the data
is loading, available, empty or could not be fetched; it is not a quality score.
The existing-files row uses the first original list that corresponds to the
most frequent normalized list.
Artist genres are descriptive suggestions, not automatic album classifications.
Retrieving data never changes tags. An unavailable source is labelled as an
error or missing ID, separately from a successful response with no genres.
The matched album's internal ID is used even if writable MusicBrainz ID tags
are removed by another plugin. Unmatched files must first be matched to an album.

Select one or more rows, then choose Use selected sources or Merge selected
with final. Edit Final album genres if needed. Apply to entire album changes
the genre on every track. An empty result requires confirmation before clearing.
Save the files normally in Picard to write the changes to disk.

An applied comparison choice takes priority over automatic file voting for
that loaded album, including when more files arrive and before saving.
It is kept in memory only, until the album is removed or Picard closes.
Restore genres from existing files removes this override and immediately applies the
original-file voting rule. If every original list is empty, current track genres provide the fallback.
Closing the comparison without applying discards its draft.


## Spelling And Output Options

One rule per line: alias = preferred spelling
Example:
Electronic = Electronic
Electronica = Electronic
Elettronica = Electronic

The left side is the spelling to recognize; the right side is the spelling
to write. Trip-Hop = Trip-Hop registers the preferred spelling: trip hop,
TRIP HOP and Trip-Hop all become Trip-Hop. Equal sides are therefore useful
for spelling normalization and for recognizing known genres.
Matching ignores case, whitespace and hyphens. Add New Genre = New Genre
to introduce a canonical spelling. Update every relevant alias when renaming
a target: mappings are direct, not recursive. Blank lines and # comments are
ignored. Conflicting normalized aliases are rejected. Canonical spellings
cannot contain commas, semicolons or vertical bars.
Use Test rules before saving options.
Use Picard's Restore Defaults button on this page to restore the plugin's
initial settings and dictionary. Accept the options dialog to save them.
Saved mappings live in Picard's plugin settings. spellings.txt supplies defaults.

Input separators default to comma, semicolon and vertical bar. Unknown genres
are retained by default, with an option to discard them. Output defaults to
one text value separated by literal semicolon-space (; ): Electronic; IDM
is stored as one string. Multiple tag values instead passes two independent
values, Electronic and IDM, to Picard. Storage depends on the file format,
and each player chooses the display separator. Literal semicolon-space
display is therefore not guaranteed with multiple values. Output can be
alphabetized or retain the winning/chosen list's order.


## Other Settings

Keep genre in the Keep Only Tags allowlist. Disable older genre scripts or
plugins that overwrite the final result. Genre comparison does not require
Use genres from MusicBrainz to be enabled. No cover art or other tags are edited.


## Validation

Automated tests cover normalization, majority voting, automatic events,
comparison requests, source separation, errors and selection overrides.
The new comparison window has not yet been visually validated in Qt.
Actual Lookup and saving with your complete installed plugin configuration
require a live check.

The Genre spelling rules and Try the rules on an example sections are
separate. Test rules checks the dictionary and previews only the example;
it does not edit music tags.

## Repository contents

- `MANIFEST.toml`: plugin identity, author and version.
- `engine.py`: normalization and list selection.
- `comparison.py`: source retrieval and review window.
- `options.py`: settings and rule preview.
- `spellings.txt`: initial editable dictionary; these are personal conventions, not a universal genre taxonomy.
- `tests/test_logic.py`: headless regression tests.

## Development

Run `python tests/test_logic.py` with Python 3.12 or newer. Tests use simulated Picard/Qt objects and do not access music files or the network.

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CHANGELOG.md](CHANGELOG.md).

## License

MIT License. Copyright (c) 2026 Borunzio. See [LICENSE](LICENSE).

Version display: install the v1.2.8 Git tag to show that version reference
in Picard. Installing main can show the branch instead. The options page
also displays the manifest version and author.

## Empty original genre tags

Automatic processing and Apply album genre rules now use the same selection: original file lists first; if all are empty after normalization, current New value lists instead. The most frequent complete list is applied to every matched file. Repeated processing excludes the plugin's own output from the input counts. Tracks without linked files are left untouched until their files arrive.

## Equivalent connectors: one rule per genre

The matching engine treats `and`, `n`, `'n'` and `&` as equivalent connectors.
You do not need one alias rule for each connector spelling. This behavior
has been available since 1.2.5; version 1.2.6 adds the missing default genre
mappings and examples, without changing the matching engine.

The current defaults include these rules:

```text
Rock&Roll = Rock&Roll
Rhythm&Blues = R&B
R&B = R&B
RnB = R&B
Drum&Bass = Drum 'n' Bass
```

| Input examples | Output |
| --- | --- |
| rock and roll; rock n roll; rock 'n' roll; Rock&Roll | Rock&Roll |
| Rhythm and Blues; Rhythm n Blues; Rhythm 'n' Blues; Rhythm&Blues | R&B |
| r&b; R & B; R n B; R and B; RnB; rnb | R&B |
| drum and bass; drum n bass; drum 'n'bass; Drum&Bass | Drum 'n' Bass |

The left side identifies the genre; the right side sets its exact output
spelling. Rhythm&Blues, R&B and RnB all produce R&B. If several of these
forms appear in an input list, the output contains R&B only once.
R&B = R&B declares the canonical spelling; the other rules are input aliases.
RnB needs its own alias because its n is inside a word; connector matching
does not replace arbitrary letters inside words. Matching is case-insensitive,
so additional aliases for rnb, RNB or r&b are unnecessary.

Curly apostrophes and compact quoted connectors such as `Drum'n'Bass` are
accepted. Bare n and and must be separate words, optionally separated by
hyphens; letters inside words such as Dance or Scandinavian are not replaced.

### Updating an existing installation

Saved rules are preserved when updating the plugin. Add the missing rules
above to your saved dictionary; do not reset your customized rules. Rock&Roll
is already in the default dictionary. If you already have
`Drum n Bass = Drum 'n' Bass`, it works exactly like the Drum&Bass rule and
can be kept instead: there is no need to add a second equivalent alias.
Equivalent aliases must have the same output spelling. If two rules disagree,
Test rules reports the conflict. Edit their right-hand sides to agree or keep
only one equivalent rule. Test rules previews changes without editing music tags.

### Updating to 1.2.8

Your saved dictionary is not overwritten. Replace any previous
`Rhythm&Blues = Rhythm&Blues` rule with `Rhythm&Blues = R&B`, keep
`R&B = R&B`, and add `RnB = R&B` if missing. Keep any equivalent full-name
aliases consistent with the R&B output spelling. The default Drum&Bass and
Rock&Roll rules remain included. Use Test rules before applying. Restore
Defaults also loads the new dictionary, but resets all customized options
and rules on this page.
