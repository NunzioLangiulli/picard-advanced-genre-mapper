"""Compare original file genres with independent MusicBrainz sources."""
from collections import Counter
import re
from uuid import UUID
from weakref import ref

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QLineEdit, QPushButton, QMessageBox)


def valid_id(value):
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        return None


def genre_names(node):
    """Return positively voted official genres, ordered by vote count."""
    entries = [g for g in node.get('genres', []) if int(g.get('count', 0)) > 0 and g.get('name')]
    entries.sort(key=lambda g: (-int(g['count']), g['name'].casefold()))
    return [g['name'] for g in entries], '; '.join(f"{g['name']} ({g['count']})" for g in entries)


def source_changes(names, controller):
    """Describe only transformations within this source, never cross-source differences."""
    separators = controller.api.plugin_config['separators']
    parts = [part.strip() for name in names for part in
             (re.split('[' + re.escape(separators) + ']', name) if separators else [name]) if part.strip()]
    changes, seen = [], set()
    for original in parts:
        values = controller.normalized([original])
        if not values:
            changes.append(original + ' -> removed (unknown genre)')
            continue
        target = values[0]
        if original != target:
            changes.append(original + ' -> ' + target)
        if target.casefold() in seen:
            changes.append('Duplicate removed: ' + target)
        seen.add(target.casefold())
    if separators and any(len(re.split('[' + re.escape(separators) + ']', name)) > 1 for name in names):
        changes.append('Input separators normalized')
    return '\n'.join(dict.fromkeys(changes)) or 'No changes'


class ComparisonDialog(QDialog):
    def __init__(self, controller, album):
        super().__init__()
        self.controller = controller
        self.album = album
        self.alive = True
        self.rows = []
        self.setWindowTitle('Advanced Genre Mapper - Compare album genres')
        self.resize(1100, 650)
        layout = QVBoxLayout(self)
        heading = QLabel(str(album.metadata.get('album', 'Album')))
        layout.addWidget(heading)
        help_text = QLabel('Each row compares the original genres with the result of your rules for that same source. MusicBrainz rows show all official genres with positive votes '
            '(vote counts in parentheses); Picard genre filters are not applied here. Artist genres describe the artist, '
            'not necessarily this album. Select one or more rows to use or merge them. Retrieval status reports loading, success, missing genres or errors; it does not rate genre accuracy. Fetching never changes tags.')
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(['Source', 'Original genres', 'After your rules', 'Changes within this source', 'Retrieval status'])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        layout.addWidget(QLabel('Final album genres (editable; separate genres with semicolon and space):'))
        self.final = QLineEdit()
        layout.addWidget(self.final)
        buttons = QHBoxLayout()
        layout.addLayout(buttons)
        for label, callback in [('Use selected sources', self.use_selected),
                                ('Merge selected with final', self.merge_selected),
                                ('Restore genres from existing files', self.reset_majority),
                                ('Apply to entire album', self.apply_final),
                                ('Close', self.reject)]:
            button = QPushButton(label)
            button.clicked.connect(callback)
            buttons.addWidget(button)
        self.notice = QLabel('Applying changes Picard metadata only. Save files in Picard when ready.')
        self.notice.setWordWrap(True)
        layout.addWidget(self.notice)
        self.finished.connect(self.closed)
        try:
            self.majority = controller.file_choice(album) or []
            lists = controller.file_lists(album)
            votes = Counter(tuple(sorted(g.casefold() for g in values)) for values in lists if values)
            counts = sorted(votes.values(), reverse=True)
            self.summary.setText('Existing files: ' + str(len(lists)) + ' matched tracks; '
                + str(sum(votes.values())) + ' tracks with genres. The most frequent complete list appears on '
                + str(counts[0] if counts else 0) + ' tracks. Complete lists are counted, not individual genres. '
                'Empty lists are ignored; ties use the first tied list in album track order.')
            row = self.add_row('Existing files - most frequent list')
            original = controller.original_selected_list(album)
            self.set_row(row, original, '; '.join(original), 'Available' if self.majority else 'No file genres')
            initial = controller.overrides.get(album, self.majority)
            self.final.setText('; '.join(controller.normalized(initial)))
        except ValueError as error:
            self.majority = []
            self.notice.setText('Invalid spelling rules: ' + str(error))
        self.fetch_release()

    def closed(self, result):
        self.alive = False

    def add_row(self, name):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.rows.append(None)
        for col, text in enumerate([name, '', '', '', 'Loading...']):
            self.table.setItem(row, col, QTableWidgetItem(text))
        return row

    def status(self, row, text):
        self.table.item(row, 4).setText(text)

    def set_row(self, row, names, reported, state='Ready'):
        try:
            values = self.controller.normalized(names)
        except ValueError as error:
            self.status(row, 'Invalid spelling rules: ' + str(error))
            return
        self.rows[row] = values
        self.table.item(row, 1).setText(reported or '(none)')
        self.table.item(row, 2).setText('; '.join(values) or '(none)')
        changes = source_changes(names, self.controller)
        self.table.item(row, 3).setText(changes)
        self.status(row, state)
        for col in range(5):
            self.table.item(row, col).setToolTip(self.table.item(row, col).text())
        self.table.resizeRowsToContents()

    def request(self, entity, mbid, row, on_success=None):
        identifier = valid_id(mbid)
        if not identifier:
            self.status(row, 'Missing MusicBrainz ID; reload the matched album')
            return
        cache_key = (entity, identifier)
        dialog_ref = ref(self)
        def received(document, reply, error):
            dialog = dialog_ref()
            if dialog is None or not dialog.alive or not dialog.controller.active:
                return
            if error or not isinstance(document, dict) or document.get('error'):
                dialog.status(row, 'Request failed; close and reopen to retry')
                return
            dialog.controller.mb_cache[cache_key] = document
            names, reported = genre_names(document)
            dialog.set_row(row, names, reported, 'Ready' if names else 'No positive genre votes')
            if on_success:
                on_success(document)
        if cache_key in self.controller.mb_cache:
            received(self.controller.mb_cache[cache_key], None, None)
            return
        includes = 'genres+artists+release-groups' if entity == 'release' else 'genres'
        try:
            self.controller.api.mb_api.get('/' + entity + '/' + identifier, received,
                unencoded_queryargs={'inc': includes, 'fmt': 'json'},
                parse_response_type='json', priority=False, important=False, mblogin=False)
        except Exception as error:
            self.controller.api.logger.error('Genre comparison request failed: %s', error)
            self.status(row, 'Could not start request; close and reopen to retry')

    def fetch_release(self):
        row = self.add_row('MusicBrainz release')
        # Album identity is independent of writable tags removed by other plugins.
        identifier = getattr(self.album, 'id', None) or self.album.metadata.get('musicbrainz_albumid')
        self.request('release', identifier, row, self.fetch_related)

    def fetch_related(self, release):
        row = self.add_row('MusicBrainz release group')
        self.request('release-group', release.get('release-group', {}).get('id'), row)
        seen = set()
        for credit in release.get('artist-credit', []):
            if not isinstance(credit, dict):
                continue
            artist = credit.get('artist', {})
            identifier = artist.get('id')
            if identifier in seen:
                continue
            seen.add(identifier)
            row = self.add_row('MusicBrainz artist: ' + artist.get('name', 'Unknown artist'))
            self.request('artist', identifier, row)
        if not seen:
            row = self.add_row('MusicBrainz album artists')
            self.status(row, 'No artist credits returned')

    def selected_values(self):
        selected = sorted({index.row() for index in self.table.selectionModel().selectedRows()})
        if not selected or any(self.rows[row] is None for row in selected):
            self.notice.setText('Select one or more successfully loaded source rows first.')
            return None
        return [genre for row in selected for genre in self.rows[row]]

    def final_values(self, values):
        # Final editor always accepts the advertised semicolon separator.
        return self.controller.normalized([part.strip() for value in values for part in value.split(';')])

    def use_selected(self):
        self.combine(False)

    def merge_selected(self):
        self.combine(True)

    def combine(self, merge):
        values = self.selected_values()
        if values is None:
            return
        try:
            self.final.setText('; '.join(self.final_values(([self.final.text()] if merge else []) + values)))
        except ValueError as error:
            self.notice.setText(str(error))

    def apply_final(self):
        if not self.controller.active:
            self.notice.setText('The plugin is disabled. Re-enable it before applying changes.')
            return
        try:
            values = self.final_values([self.final.text()])
        except ValueError as error:
            self.notice.setText(str(error))
            return
        if not values and QMessageBox.question(self, 'Clear album genres?',
                'The final list is empty. Clear the genre tag on every track in this album?') != QMessageBox.StandardButton.Yes:
            return
        self.controller.overrides[self.album] = values
        self.controller.apply(self.album)
        self.notice.setText('Applied to every track. This choice overrides automatic selection from existing files for this loaded album. Save files in Picard when ready.')

    def reset_majority(self):
        if not self.controller.active:
            return
        self.controller.overrides.pop(self.album, None)
        self.controller.apply(self.album)
        self.final.setText('; '.join(self.controller.file_choice(self.album) or []))
        self.notice.setText('Selection from existing files restored. If all original lists are empty, existing tags are left unchanged.')
