"""English options page for personal album genre rules."""
from PyQt6.QtWidgets import (QVBoxLayout, QFormLayout, QLabel, QCheckBox,
    QComboBox, QLineEdit, QPlainTextEdit, QPushButton, QMessageBox, QGroupBox, QHBoxLayout)
from picard.plugin3.api import OptionsPage
from . import DEFAULTS, PLUGIN_INFO
from .engine import parse_rules, normalize


class GenreOptions(OptionsPage):
    NAME = 'personal_album_genres'
    TITLE = 'Advanced Genre Mapper'
    PARENT = 'plugins'

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Advanced Genre Mapper ' + PLUGIN_INFO['version'] + ' | Author: Borunzio'))
        self.automatic = QCheckBox('Automatically apply after Lookup / file matching and before saving')
        layout.addWidget(self.automatic)
        explanation = QLabel(
            'FILE GENRES: the most frequent complete genre list among matched tracks is used for the whole album. '
            'Example: 7 tracks with Electronic; IDM and 3 with Jazz give Electronic; IDM to all 10 tracks. '
            'This counts complete lists, not individual genres. Order does not affect matching; each track is counted once. '
            'Empty lists are ignored. Ties use the first tied list in album track order. If every list is empty, nothing changes. '
            'Load all tracks and discs before applying. Original file genres are captured once per loaded file.')
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        comparison_help = QLabel(
            'Right-click an album > Plugins > Compare album genres... to compare file genres with MusicBrainz '
            'release, release-group and album-artist genres. Fetching does not change tags. '
            'A result you apply there takes priority over automatic selection from existing files for this loaded album. '
            'Use Restore genres from existing files in that window to remove the override. Overrides last until the album is removed or Picard closes.')
        comparison_help.setWordWrap(True)
        layout.addWidget(comparison_help)
        form = QFormLayout()
        layout.addLayout(form)
        self.separators = QLineEdit()
        form.addRow('Input separator characters:', self.separators)
        self.unknown = QComboBox()
        self.unknown.addItem('Keep original spelling', 'keep')
        self.unknown.addItem('Discard unknown genres', 'drop')
        form.addRow('Unknown genres:', self.unknown)
        self.output = QComboBox()
        self.output.addItem('Single text value separated by semicolon and space (; )', 'text')
        self.output.addItem('Multiple tag values (display depends on the player)', 'multi')
        form.addRow('Output format:', self.output)
        self.sort_output = QCheckBox('Sort output genres alphabetically')
        form.addRow(self.sort_output)
        output_help = QLabel(
            'Single text value stores "Electronic; IDM" as one string, including the punctuation. '
            'Multiple tag values stores Electronic and IDM as separate genre entries; the file format and player '
            'determine how they are written and displayed. Select Single text value to keep literal semicolon-space formatting.')
        output_help.setWordWrap(True)
        layout.addWidget(output_help)
        rules_box = QGroupBox('Genre spelling rules')
        rules_layout = QVBoxLayout(rules_box)
        help_text = QLabel(
            'Left = spelling to recognize. Right = spelling to write. One rule per line. '
            'Example: Electronica = Electronic changes Electronica into Electronic. '
            'Trip-Hop = Trip-Hop registers the preferred spelling: trip hop, TRIP HOP and Trip-Hop all become Trip-Hop. '
            'Matching ignores case, spaces and hyphens. Add New Genre = New Genre to register a preferred name. '
            'Lines starting with # are comments. Rules apply independently; changes take effect on the next application.')
        help_text.setWordWrap(True)
        rules_layout.addWidget(help_text)
        self.rules = QPlainTextEdit()
        self.rules.setMinimumHeight(180)
        rules_layout.addWidget(self.rules)
        layout.addWidget(rules_box, 1)
        layout.addSpacing(12)
        preview_box = QGroupBox('Try the rules on an example')
        preview_layout = QVBoxLayout(preview_box)
        preview_help = QLabel('This test checks the rules and previews the example below. It does not change your music tags.')
        preview_help.setWordWrap(True)
        preview_layout.addWidget(preview_help)
        preview_row = QHBoxLayout()
        preview_row.addWidget(QLabel('Example input:'))
        self.sample = QLineEdit('Electronica | IDM, trip hop')
        preview_row.addWidget(self.sample, 1)
        button = QPushButton('Test rules')
        button.clicked.connect(self.preview)
        preview_row.addWidget(button)
        preview_layout.addLayout(preview_row)
        self.result = QLabel()
        self.result.setWordWrap(True)
        preview_layout.addWidget(self.result)
        layout.addWidget(preview_box)

    def load_values(self, values):
        for name in ('automatic', 'sort_output'):
            getattr(self, name).setChecked(values[name])
        for name in ('unknown', 'output'):
            widget = getattr(self, name)
            widget.setCurrentIndex(widget.findData(values[name]))
        self.separators.setText(values['separators'])
        self.rules.setPlainText(values['rules'])
        self.preview()

    def load(self):
        self.load_values(self.api.plugin_config)

    def restore_defaults(self):
        self.load_values(DEFAULTS)

    def preview(self):
        try:
            rules = parse_rules(self.rules.toPlainText())
            genres = normalize([self.sample.text()], rules, self.separators.text(), self.unknown.currentData())
            self.result.setText(f'{len(rules)} valid rules. Example result: ' + ('; '.join(genres) or '(empty)'))
            return True
        except ValueError as error:
            self.result.setText(str(error))
            return False

    def save(self):
        if not self.preview():
            QMessageBox.warning(self, 'Invalid genre rules', self.result.text() + '\nPrevious settings were kept.')
            return
        cfg = self.api.plugin_config
        for name in ('automatic', 'sort_output'):
            cfg[name] = getattr(self, name).isChecked()
        for name in ('unknown', 'output'):
            cfg[name] = getattr(self, name).currentData()
        cfg['separators'] = self.separators.text()
        cfg['rules'] = self.rules.toPlainText()
