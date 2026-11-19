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
        self.current_sources = WeakKeyDictionary()
        self.written_genres = WeakKeyDictionary()
        self.display_timer = None
        self.current_snapshots = WeakKeyDictionary()

    def start_display_sync(self):
        # Poll on the GUI thread: manual edits have no public metadata-change hook.
        self.display_timer = QTimer()
        self.display_timer.setInterval(1000)
        self.display_timer.timeout.connect(self.sync_displays)
        self.display_timer.start()

    def sync_displays(self):
        if not self.active:
            return
        albums = getattr(getattr(self.api, 'tagger', None), 'albums', {})
        for album in list(albums.values()):
            self.sync_album_display(album)

    def sync_album_display(self, album):
        """Keep current genres uniform, without restoring original-file inputs."""
        if not self.active or not getattr(album, 'loaded', False) or not album.tracks:
            return
        # Standalone recordings are not an album and may have unrelated metadata.
        if not getattr(album, 'id', None):
            return
        values = [tuple(file.metadata.getall('genre'))
                  for track in album.tracks for file in track.files]
        if not values:
            return
        complete = all(track.files for track in album.tracks) and not album.get_num_unmatched_files()
        unanimous = all(value == values[0] for value in values)
        snapshot = tuple(tuple((id(file), tuple(file.metadata.getall('genre')))
                               for file in track.files) for track in album.tracks)
        stable = self.current_snapshots.get(album) == snapshot
        self.current_snapshots[album] = snapshot
        initial_finished = getattr(album, '_advanced_genre_mapper_applied', False) or album not in self.pending
        if complete and not unanimous and self.api.plugin_config['automatic'] and initial_finished:
            # Wait for two identical polls so a batch edit can finish first.
            if stable:
                try:
                    lists = []
                    for track in album.tracks:
                        candidates = [self.normalized(file.metadata.getall('genre')) for file in track.files]
                        lists.append(next((value for value in candidates if value), []))
                    result = choose(lists, tie='first', ignore_empty=True)
                    if result is not None:
                        self.write_result(album, result)
                        return
                except ValueError as error:
                    self.api.logger.error('Invalid genre rules: %s', error)
        # A unanimous manual choice is preserved exactly, including clearing all genres.
        common = values[0] if complete and unanimous else ()
        if tuple(album.metadata.getall('genre')) == common:
            return
        if common:
            album.metadata['genre'] = list(common)
        elif 'genre' in album.metadata:
            del album.metadata['genre']
        # Do not refresh track metadata, apply rules, update originals or save files.
        album.update(update_tracks=False, update_selection=False)

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

    def current_lists(self, album):
        """Read current file genres without counting our own output as new input."""
        lists = []
        for track in album.tracks:
            candidates = []
            for file in track.files:
                current = list(file.metadata.getall('genre'))
                if file not in self.current_sources or current != self.written_genres.get(file):
                    self.current_sources[file] = current
                candidates.append(self.normalized(self.current_sources[file]))
            if candidates:
                lists.append(next((value for value in candidates if value), []))
        return lists

    def automatic_choice(self, album):
        # Keep original-file and current-value counts separate; never mix sources.
        current_lists = self.current_lists(album)
        original = self.file_choice(album)
        return original if original is not None else choose(current_lists, tie='first', ignore_empty=True)

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
                      else self.automatic_choice(album))
        except ValueError as error:
            self.api.logger.error('Invalid genre rules: %s', error)
            return
        self.write_result(album, result)
        # An explicit application also consumes the initial automatic run.
        # Keep this on the album so disabling/re-enabling cannot reset it.
        album._advanced_genre_mapper_applied = True

    def write_result(self, album, result):
        cfg = self.api.plugin_config
        if result is None:
            return
        if cfg['sort_output']:
            result = sorted(result, key=str.casefold)
        value = result if cfg['output'] == 'multi' else '; '.join(result)
        album.metadata['genre'] = value
        for track in album.tracks:
            # Leave unmatched track templates intact for files that arrive later.
            if not track.files:
                continue
            track.metadata['genre'] = value
            for file in track.files:
                expected = result if cfg['output'] == 'multi' else ([value] if value else [])
                if file.metadata.getall('genre') != expected:
                    file.metadata['genre'] = value
                    file.update()
                self.written_genres[file] = list(file.metadata.getall('genre'))
            track.update()
        album.update()

    def schedule(self, album):
        if (not self.active or album is None or not self.api.plugin_config['automatic']
                or getattr(album, '_advanced_genre_mapper_applied', False)):
            return
        token = self.pending.get(album, 0) + 1
        self.pending[album] = token
        album_ref = ref(album)
        def run():
            current = album_ref()
            if (self.active and current is not None and self.pending.get(current) == token
                    and self.api.plugin_config['automatic']
                    and not getattr(current, '_advanced_genre_mapper_applied', False)
                    and getattr(current, 'loaded', False)
                    and current.tracks
                    and all(track.files for track in current.tracks)
                    and not current.get_num_unmatched_files()):
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
    _controller.start_display_sync()


def disable(api):
    if _controller is not None:
        _controller.active = False
        if _controller.display_timer is not None:
            _controller.display_timer.stop()
