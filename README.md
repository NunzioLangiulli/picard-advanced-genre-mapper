# Advanced Genre Mapper

**Version:** 1.2.12 · **Author:** Borunzio · **Target:** Picard 3.0.2

Normalize genre spelling and review album-level genres without mixing the original data sources.

> Development status: logic tests pass; the latest Qt layouts and full Lookup/save workflow still need live validation.



## Install / Update

This folder is a local Git repository. Use Picard's Local repository plugin
installer to update/reinstall from this folder, select **v1.2.12**, then restart Picard. The automatic checkbox can remain enabled. Existing saved spelling rules are preserved.
The plugin UUID is unchanged, so this replaces Album Genres - Personal Format
and retains its saved spelling rules. Keep the .git folder for installation.


## Options

Options > Plugins > Advanced Genre Mapper
All interface text, comments and documentation are in English.
With the automatic checkbox enabled, selection from original-file genres runs **once after the first complete Lookup / file matching** for each loaded album. Ongoing uniformity then uses current file genres only. Neither stage is triggered by Save. After that first application, original-file genres are never restored automatically. If current file genres differ, the most frequent complete normalized list is applied across the album after two stable checks. A manual edit applied uniformly to every track is preserved exactly, including spelling and clearing the genre.

Automatic processing waits for a loaded album with files matched to every track and no unmatched files remaining. Partial albums are not automatically processed; use Apply album genre rules now if you intentionally have only part of an album. Refreshing, rematching, adding/removing files or toggling the plugin does not repeat completed original-source selection on the same album object. These events can still change current file genres, which remain subject to ongoing majority uniformity. Picard itself or other plugins may also replace metadata on refresh. Remove the album and load it again to start a new cycle. An explicit manual application also consumes the pending first automatic run, but the manual action remains repeatable.
The plugin does not save audio files automatically.
Already-loaded complete albums are also checked by ongoing uniformity. Use Apply album genre rules now only when you explicitly want original-source/comparison selection again; it can replace current manual edits and works even when automatic processing is disabled or the album is partial.


## How File Genres Are Chosen (Fixed Rule)

The most frequent COMPLETE normalized genre list among matched tracks wins.
For example, if 7 tracks contain Electronic; IDM and 3 contain Jazz, every
track receives Electronic; IDM. Genres are not counted individually and
unrelated lists are not combined automatically.
Lists with identical genres in different orders count as the same list.
Each matched track casts one vote. For multiple files linked to the same
track, the first non-empty normalized file list is used.
Empty lists are ignored. A tie is resolved using the first tied list in
album track order. If all original-file lists are empty, the plugin uses the most frequent complete list among current track genres (the New value column). If both sources have no nonempty normalized list, no genre result is applied. Ongoing summary refresh can still clear an empty or mixed album summary.
Load all tracks and all discs for automatic application. Saving never triggers genre processing.
This policy is fixed, not an optional selection strategy.

During initial Lookup selection, original file genres take priority. Explicit manual rule application first uses any remembered comparison choice, otherwise this same original-source policy. If none remain after normalization, current track genres are counted separately as a fallback. Original and current sources are never mixed in one count. The plugin remembers its own output so applying repeatedly does not distort the counts. Inputs are captured once per loaded file, preventing an early
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
- Current track genres: a fallback row only when original-file selection has no usable list. This follows the manual-selection fallback cache, not the timer's direct current-value count.

MusicBrainz requests start when the comparison window opens. They use
Picard's MusicBrainz connection and request queue. Rate Your Music buttons open pages in your browser; no RYM genres are downloaded or imported.
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
the genre on every matched track and linked file (unmatched track templates are left alone). An empty result requires confirmation before clearing.
Save the files normally in Picard to write the changes to disk.

An applied comparison choice takes priority when you explicitly apply the rules again for that loaded album. It also consumes any pending initial automatic application. Save never reapplies the comparison choice. Later current genre differences follow the majority policy below; unanimous manual edits are preserved.
It is kept in memory only, until the album is removed or Picard closes.
Restore genres from existing files removes this override and immediately applies the
most frequent complete original-file genre list rule. If every original list is empty, current track genres provide the fallback.
Closing the comparison without applying discards its draft. The initial Final album genres editor is populated from the remembered choice or original-source selection/fallback; it is not a live mirror of later manual file edits. Merely opening or closing this dialog never applies that draft. The independent uniformity timer continues while the dialog is open.


## Rate Your Music shortcuts

The comparison dialog includes **Search RYM artist** and **Search RYM album**.
They open artist or release search results in your default browser using the album artist and album title. If MusicBrainz provides a matching Rate Your Music URL relationship, the relevant button becomes **Open RYM artist** or **Open RYM album** and opens that exact linked page. The album button prefers a release-group link when available. For multiple credited artists, the artist button keeps a combined search rather than choosing one artist silently.

Search is a fallback, not a guaranteed exact match. Names are URL-encoded, never converted into guessed page slugs. Missing names disable the corresponding search until an exact link is found. RYM may require login or browser verification. No RYM API, scraping or genre import is used; these buttons do not modify tags. Review the page and enter any desired genres in the final editor yourself.

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
Use Test rules before saving options. The example checks spelling, separators and unknown-genre handling only; it does not simulate list selection, output sorting or tag storage.
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
alphabetized or retain the winning/chosen list's order. These settings are used when rules are applied; changing them does not automatically rewrite an already unanimous current album.


## Other Settings

Keep genre in the Keep Only Tags allowlist. Disable older genre scripts or
plugins that overwrite the final result. Genre comparison does not require
Use genres from MusicBrainz to be enabled. No cover art or other tags are edited.


## Validation

Automated tests cover normalization, majority voting, automatic events,
comparison requests, source separation, errors and selection overrides.
Headless regressions cover current-value majorities, whole-album manual changes, ties, partial albums, source selection and the absence of a pre-save rule hook. Separate real Qt/Picard checks exercised the comparison window construction and timer behavior. These checks do not establish installed-application visual or end-to-end validation.
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

Version display: install the v1.2.12 Git tag to show that version reference
in Picard. Installing main can show the branch instead. The options page
also displays the manifest version and author.

## Empty original genre tags

Initial Lookup selection uses original file lists first; if none survive normalization, it uses current New value fallback lists. Explicit Apply album genre rules now uses a remembered comparison choice first, then this same policy. This fallback caches pre-application current inputs so repeated manual applications do not count the plugin's own output as new input. In contrast, ongoing uniformity reads the actual current file values directly on every check. Tracks without linked files are not written; automatic processing waits for a complete match.

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

### Migrating older R&B mappings

Your saved dictionary is not overwritten. Replace any previous
`Rhythm&Blues = Rhythm&Blues` rule with `Rhythm&Blues = R&B`, keep
`R&B = R&B`, and add `RnB = R&B` if missing. Keep any equivalent full-name
aliases consistent with the R&B output spelling. The default Drum&Bass and
Rock&Roll rules remain included. Use Test rules before applying. Restore
Defaults also loads the new dictionary, but resets all customized options
and rules on this page.

## Ongoing uniformity and album summary

With automatic processing enabled, a complete album is checked about once per second. If its current file genres differ, two consecutive unchanged snapshots are required before applying the most frequent complete normalized genre list to every matched track and file. Each track counts once, even with multiple linked files; its first nonempty normalized file list is used. Empty lists are ignored and ties use the first tied list in album track order. Lists with the same normalized genres in different orders are counted together. This is not a union of genres or a count of individual genres. If normalization leaves no nonempty list (for example, all values are discarded as unknown), no winning result is applied; the mixed summary stays empty.

Examples: nine tracks with Jazz and one with Rock become ten Jazz tracks. Changing all ten tracks manually to Rock keeps Rock. If every file already has exactly the same values, they are preserved exactly as tag values, without reapplying spelling rules; clearing all genres is also preserved. Editing tracks one at a time with pauses may therefore cause a minority edit to be replaced: select the whole album to change its genre together.

Ongoing uniformity reads current file metadata only. It does not restore original-file genres, cached source lists or an earlier comparison choice. The initial Lookup still uses the original-source selection policy described above. No pre-save processor is registered: saving does not trigger rules or save other files. Automatic changes are in-memory edits and require Picard's normal Save action; wait for the display to settle before saving.

The album row mirrors the resulting common genre list. With automatic processing disabled, only this summary is synchronized and track/file tags remain untouched. Mixed, empty or partial albums have no common genre summary; unloaded albums and albums without matched files are left alone. Partial albums are never automatically unified. Disabling the plugin stops the timer.
