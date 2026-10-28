# Contributing

Use English for code comments, interface text, documentation and reports.

## Bug reports

Once hosted, open an issue in this repository. Include Picard and plugin versions, operating system, relevant settings, enabled interacting plugins, expected behavior, actual behavior, and minimal reproduction steps. Include only the relevant log excerpt; remove private file paths or personal information. Do not upload audio files.

## Changes

Keep changes focused. Preserve the plugin UUID. Document user-visible behavior and update the changelog. Add regression coverage for behavior changes. State whether validation used mocks, live Picard, real network responses or actual file saves; never describe mock tests as end-to-end validation.

Test compatibility with the stated Picard version. Do not add network requests or automatic file writes without documenting the behavior. Source contributions should identify their provenance, including generated code, and receive human review before release.

## Release and publication guide

## Before first public release

1. Use a separate public repository for this plugin. Keep its display name and existing UUID.
2. Preserve the MIT license and copyright notice in LICENSE and the matching manifest license field.
3. Review all source, including generated contributions, and complete the live checks documented in the README.
4. Create the GitHub repository. Add its real URL to `homepage` and its Issues URL to `report_bugs_to` in MANIFEST.toml. No placeholder URL should be committed there.
5. Review README, changelog and compatibility claims. Do not publish private test data, local paths, credentials or audio files.

## Versioning

Set the manifest version, update documentation and changelog, commit the release, and create a matching Git tag such as `v1.0.1`. Do not move an already-published version tag. Push both the default branch and release tag when publishing. Create a GitHub release with change notes and known limitations.

Picard 3's Version field reflects the installed Git reference. Installing from `main` can show a branch rather than the manifest version. Install a release tag to display that version reference. Author information comes from the manifest.

## Picard registry

Follow the official [submission guide](https://github.com/metabrainz/picard-plugins-registry/blob/main/PLUGIN_SUBMISSION.md). The registry requires a publicly hosted Git repository and valid root MANIFEST.toml. Use the registry tooling to submit a community plugin; do not manually edit plugins.toml. A semantic version tag enables version discovery. Inclusion requires the maintainers' review and is not automatic.

Discuss the plugin and collect feedback in the [MetaBrainz Picard community](https://community.metabrainz.org/c/picard/13).

## Status

These files prepare a local project for publication. They do not create a GitHub repository, publish a release or submit a registry entry.
