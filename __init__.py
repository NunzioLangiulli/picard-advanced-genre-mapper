"""Apply configurable personal genre rules after files are matched to an album."""
from pathlib import Path
import tomllib
from weakref import WeakKeyDictionary, ref
from PyQt6.QtCore import QTimer
from picard.plugin3.api import BaseAction
from .engine import parse_rules, normalize, choose

PLUGIN_INFO = tomllib.loads(Path(__file__).with_name('MANIFEST.toml').read_text(encoding='utf-8'))

DEFAULTS = dict(automatic=True,
    rules=Path(__file__).with_name('spellings.txt').read_text(encoding='utf-8-sig'),
    separators=';,|', unknown='keep',
    output='text', sort_output=False)
_controller = None


class Controller:
    def __init__(self, api):
        self.api = api
        self.active = True
        self.sources = WeakKeyDictionary()
        self.pending = WeakKeyDictionary()
        self.overrides = WeakKeyDictionary()
        self.mb_cache = {}

    def source(self, file):
        # Freeze inputs so a partial-album result cannot skew later votes.
        if file not in self.sources:
            original = file.orig_metadata.getall('genre')
            self.sources[file] = list(original)
        return self.sources[file]

    def normalized(self, values):
        cfg = self.api.plugin_config
        return normalize(values, parse_rules(cfg['rules']), cfg['separators'], cfg['unknown'])

    def file_lists(self, album):
        lists = []
        for track in album.tracks:
            candidates = [self.normalized(self.source(file)) for file in track.files]
            if candidates:
                lists.append(next((value for value in candidates if value), []))
        return lists

    def file_choice(self, album):
        # The complete most frequent list is the fixed file-source policy.
        return choose(self.file_lists(album), tie='first', ignore_empty=True)

    def original_selected_list(self, album):
        """Return the first original file list represented by the selected normalized list."""
        selected = self.file_choice(album)
        if not selected:
            return []
        identity = {genre.casefold() for genre in selected}
        for track in album.tracks:
            for file in track.files:
                original = self.source(file)
                normalized = self.normalized(original)
                if normalized:
                    if {genre.casefold() for genre in normalized} == identity:
                        return original
                    break
        return []

    def apply(self, album):
        try:
            result = (self.normalized(self.overrides[album]) if album in self.overrides
                      else self.file_choice(album))
        except ValueError as error:
            self.api.logger.error('Invalid genre rules: %s', error)
            return
        self.write_result(album, result)

    def write_result(self, album, result):
        cfg = self.api.plugin_config
        if result is None:
            return
        if cfg['sort_output']:
            result = sorted(result, key=str.casefold)
        value = result if cfg['output'] == 'multi' else '; '.join(result)
        album.metadata['genre'] = value
        for track in album.tracks:
            track.metadata['genre'] = value
            for file in track.files:
                expected = result if cfg['output'] == 'multi' else ([value] if value else [])
                if file.metadata.getall('genre') != expected:
                    file.metadata['genre'] = value
                    file.update()
            track.update()
        album.update()

    def schedule(self, album):
        if not self.active or album is None or not self.api.plugin_config['automatic']:
            return
        token = self.pending.get(album, 0) + 1
        self.pending[album] = token
        album_ref = ref(album)
        def run():
            current = album_ref()
            if (self.active and current is not None and self.pending.get(current) == token
                    and self.api.plugin_config['automatic']):
                self.apply(current)
        QTimer.singleShot(750, run)


class ApplyAlbumGenres(BaseAction):
    NAME = 'Apply album genre rules now'
    TITLE = NAME

    def callback(self, albums):
        for album in albums:
            _controller.apply(album)


class CompareAlbumGenres(BaseAction):
    NAME = 'Compare album genres...'
    TITLE = NAME

    def callback(self, albums):
        from .comparison import ComparisonDialog
        for album in albums:
            dialog = ComparisonDialog(_controller, album)
            dialog.exec()


def added(api, track, file):
    _controller.source(file)
    _controller.schedule(track.album)


def removed(api, track, file):
    _controller.schedule(track.album)


def before_save(api, file):
    album = getattr(getattr(file, 'parent_item', None), 'album', None)
    if _controller.active and api.plugin_config['automatic'] and album is not None:
        _controller.apply(album)


def enable(api):
    global _controller
    from .options import GenreOptions
    for name, value in DEFAULTS.items():
        api.plugin_config.register_option(name, value)
    _controller = Controller(api)
    api.register_options_page(GenreOptions)
    api.register_album_action(ApplyAlbumGenres)
    api.register_album_action(CompareAlbumGenres)
    api.register_file_post_addition_to_track_processor(added, priority=-1000)
    api.register_file_post_removal_from_track_processor(removed, priority=-1000)
    api.register_file_pre_save_processor(before_save, priority=-1000)


def disable(api):
    if _controller is not None:
        _controller.active = False
