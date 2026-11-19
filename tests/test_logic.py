"""Headless behavior tests; no Qt binaries or application access required."""
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest

root=Path(__file__).resolve().parent.parent
core=ModuleType('PyQt6.QtCore')
core.QTimer=SimpleNamespace(singleShot=lambda *args:None)
widgets=ModuleType('PyQt6.QtWidgets')
for name in ('QDialog','QVBoxLayout','QHBoxLayout','QLabel','QTableWidget','QTableWidgetItem','QAbstractItemView','QHeaderView','QLineEdit','QPushButton','QMessageBox'):
    setattr(widgets,name,type(name,(),{}))
sys.modules['PyQt6']=ModuleType('PyQt6')
sys.modules['PyQt6.QtCore']=core
sys.modules['PyQt6.QtWidgets']=widgets
api=ModuleType('picard.plugin3.api')
api.BaseAction=object
sys.modules['picard.plugin3.api']=api
path=root/'__init__.py'
spec=importlib.util.spec_from_file_location('mapper',path,submodule_search_locations=[str(path.parent)])
plugin=importlib.util.module_from_spec(spec)
sys.modules['mapper']=plugin
spec.loader.exec_module(plugin)
from mapper.comparison import ComparisonDialog,genre_names,source_changes,rym_search,rym_relation

class Metadata(dict):
    def getall(self,key):
        value=self.get(key,[])
        return ([value] if value else []) if isinstance(value,str) else list(value)
class Item:
    def __init__(self,**kw): self.__dict__.update(kw)
    def update(self, **kwargs): pass

class Tests(unittest.TestCase):
    def setUp(self):
        self.cfg=dict(plugin.DEFAULTS)
        self.api=SimpleNamespace(plugin_config=self.cfg,logger=SimpleNamespace(error=lambda *a:None))
        self.c=plugin.Controller(self.api)
        plugin._controller=self.c
    def album(self,values):
        a=Item(tracks=[],metadata=Metadata(),loaded=True,get_num_unmatched_files=lambda:0,id='11111111-1111-4111-8111-111111111111')
        for value in values:
            t=Item(files=[],metadata=Metadata(),album=a)
            f=Item(orig_metadata=Metadata(genre=value),metadata=Metadata(genre=value,cover='unchanged'),parent_item=t)
            t.files.append(f)
            a.tracks.append(t)
        return a
    def test_fixed_majority(self):
        a=self.album(['Electronica;IDM','IDM|Electronic','Jazz',''])
        self.cfg.update(tie='skip',ignore_empty=False)
        self.c.apply(a)
        self.assertTrue(all(t.metadata['genre']=='Electronic; IDM' for t in a.tracks))
        self.assertEqual(a.tracks[0].files[0].metadata['cover'],'unchanged')
        tie=self.album(['Jazz','Rap'])
        self.assertEqual(self.c.file_choice(tie),['Jazz'])
    def test_original_sources_and_empty(self):
        a=self.album([''])
        a.tracks[0].files[0].metadata['genre']='MusicBrainz suggestion'
        self.assertIsNone(self.c.file_choice(a))
        self.c.apply(a)
        self.assertEqual(a.metadata['genre'],'MusicBrainz suggestion')
    def test_lookup_genres_uniform_across_twelve_tracks(self):
        a=self.album(['']*12)
        for index,track in enumerate(a.tracks):
            track.files[0].metadata['genre']='Electronica|IDM' if index<8 else 'Jazz'
        plugin.ApplyAlbumGenres().callback([a])
        self.assertTrue(all(t.files[0].metadata['genre']=='Electronic; IDM' for t in a.tracks))
        self.assertIsNone(self.c.file_choice(a))
        self.c.apply(a)
        self.assertEqual(self.c.current_lists(a).count(['Jazz']),4)

    def test_incremental_lookup_counts_ignore_own_output(self):
        a=self.album(['',''])
        for track,value in zip(a.tracks,['Jazz','Rap']):
            track.files[0].metadata['genre']=value
        self.c.apply(a)
        incoming=self.album(['']).tracks[0]
        incoming.album=a
        incoming.files[0].metadata['genre']='Rap'
        a.tracks.append(incoming)
        self.c.apply(a)
        self.assertEqual(a.metadata['genre'],'Rap')
        self.assertTrue(all(t.files[0].metadata['genre']=='Rap' for t in a.tracks))

    def test_late_lookup_and_empty_sources(self):
        a=self.album(['',''])
        self.c.apply(a)
        self.assertNotIn('genre',a.metadata)
        a.tracks[0].files[0].metadata['genre']='Electronica'
        self.c.apply(a)
        self.assertTrue(all(t.files[0].metadata['genre']=='Electronic' for t in a.tracks))

    def test_original_priority_and_unmatched_template(self):
        a=self.album(['Jazz','',''])
        for track in a.tracks: track.files[0].metadata['genre']='Rap'
        unmatched=Item(files=[],metadata=Metadata(genre='Ambient'),album=a)
        a.tracks.append(unmatched)
        self.c.apply(a)
        self.assertEqual(a.metadata['genre'],'Jazz')
        self.assertEqual(unmatched.metadata['genre'],'Ambient')

    def test_incremental_and_override(self):
        a=self.album(['Jazz','Rap'])
        self.c.apply(a)
        a.tracks.extend(self.album(['Rap']).tracks)
        self.c.apply(a)
        self.assertEqual(a.metadata['genre'],'Rap')
        self.c.overrides[a]=['Electronica','IDM']
        self.c.apply(a)
        self.assertEqual(a.metadata['genre'],'Electronic; IDM')
        self.c.overrides.pop(a)
        self.c.apply(a)
        self.assertEqual(a.metadata['genre'],'Rap')
    def test_dictionary(self):
        names=set(plugin.parse_rules(plugin.DEFAULTS['rules']).values())
        for name in names: self.assertEqual(self.c.normalized([name]),[name])
        self.assertEqual(self.c.normalized(['Electronica|Elettrinica; Electronic']),['Electronic'])
    def test_vote_filter(self):
        names,reported=genre_names({'genres':[{'name':'Jazz','count':0},{'name':'IDM','count':5},{'name':'ambient','count':2}]})
        self.assertEqual(names,['IDM','ambient'])
        self.assertIn('IDM (5)',reported)
    def dialog(self):
        d=ComparisonDialog.__new__(ComparisonDialog)
        d.controller=self.c
        d.alive=True
        d.states={}
        d.values={}
        d.status=lambda row,text:d.states.__setitem__(row,text)
        d.set_row=lambda row,names,reported,state:d.values.__setitem__(row,names)
        return d
    def test_request_cache_and_source_separation(self):
        d=self.dialog()
        requests=[]
        def get(path,cb,**kw):
            requests.append((path,kw))
            cb({'genres':[{'name':'electronica','count':4}]},None,None)
        self.api.mb_api=SimpleNamespace(get=get)
        identifier='11111111-1111-4111-8111-111111111111'
        d.request('release',identifier,0)
        d.request('release',identifier,1)
        self.assertEqual(len(requests),1)
        self.assertEqual(d.values[0],['electronica'])
        self.assertEqual(requests[0][1]['parse_response_type'],'json')
        d.request('artist',identifier,2)
        self.assertEqual(len(requests),2)
    def test_request_failure_missing_and_closed(self):
        d=self.dialog()
        callbacks=[]
        self.api.mb_api=SimpleNamespace(get=lambda path,cb,**kw:callbacks.append(cb))
        d.request('release',None,0)
        self.assertIn('Missing',d.states[0])
        self.assertEqual(callbacks,[])
        d.request('release','11111111-1111-4111-8111-111111111111',1)
        callbacks[0](None,None,403)
        self.assertIn('failed',d.states[1])
        self.assertEqual(self.c.mb_cache,{})
        d.alive=False
        callbacks[0]({'genres':[]},None,None)
        self.assertEqual(d.values,{})
    def test_related_sources_and_dedup(self):
        d=self.dialog()
        rows=[]
        calls=[]
        d.add_row=lambda text:rows.append(text) or len(rows)-1
        d.request=lambda entity,identifier,row,on_success=None:calls.append((entity,identifier,row))
        d.set_rym_link=lambda *args:None
        release={'release-group':{'id':'group'},'artist-credit':[{'artist':{'id':'a','name':'A'}},{'artist':{'id':'a','name':'A'}},{'artist':{'id':'b','name':'B'}}]}
        d.fetch_related(release)
        self.assertEqual([c[0] for c in calls],['release-group','artist','artist'])
    def test_changes_stay_within_the_source(self):
        self.assertEqual(source_changes(['Jazz'],self.c),'No changes')
        self.assertIn('electronica -> Electronic',source_changes(['electronica'],self.c))
        self.assertNotIn('Jazz',source_changes(['electronica'],self.c))
        self.assertIn('Duplicate removed',source_changes(['Electronica; Electronic'],self.c))
        self.cfg['unknown']='drop'
        self.assertIn('removed (unknown genre)',source_changes(['Unlisted Genre'],self.c))

    def test_original_selected_list(self):
        a=self.album(['Jazz','electronica | IDM','IDM; Electronic'])
        self.assertEqual(self.c.original_selected_list(a),['electronica | IDM'])

    def test_multiple_tag_values(self):
        a=self.album(['Electronic; IDM'])
        self.cfg['output']='multi'
        self.c.apply(a)
        self.assertEqual(a.tracks[0].files[0].metadata.getall('genre'),['Electronic','IDM'])
        self.cfg['output']='text'
        self.c.apply(a)
        self.assertEqual(a.tracks[0].files[0].metadata.getall('genre'),['Electronic; IDM'])

    def test_connector_variants_preserve_chosen_spelling(self):
        rules=plugin.parse_rules("Drum n Bass = Drum 'n' Bass")
        for name in ["Drum 'n' bass", "Drum ‘n’ Bass", "Drum ’n’ Bass", "Drum ʼnʼ Bass",
                     "Drum and Bass", "Drum & Bass", "Drum&Bass", "Drum n Bass",
                     "Drum'n'Bass", "DRUM-N-BASS"]:
            self.assertEqual(plugin.normalize([name],rules),["Drum 'n' Bass"])
        rules=plugin.parse_rules('Drum & Bass = Drum and Bass')
        self.assertEqual(plugin.normalize(["Drum 'n' Bass"],rules),['Drum and Bass'])

    def test_connector_boundaries_and_conflicts(self):
        from mapper.engine import key
        self.assertNotEqual(key('Scandinavian'),key('Sc&inavian'))
        self.assertNotEqual(key('Dance'),key('Da&ce'))
        rules=plugin.parse_rules("Rock&Roll = Rock&Roll")
        self.assertEqual(plugin.normalize(["Rock 'n' Roll"],rules),['Rock&Roll'])
        self.assertEqual(plugin.normalize(['Unlisted and Style'],rules),['Unlisted and Style'])
        with self.assertRaisesRegex(ValueError,'different output spellings'):
            plugin.parse_rules("Drum n Bass = Drum n Bass\nDrum & Bass = Drum and Bass")
        plugin.parse_rules("Drum n Bass = Drum and Bass\nDrum & Bass = Drum and Bass")

    def test_three_genres_need_only_one_rule_each(self):
        rules=plugin.parse_rules("Rock&Roll = Rock&Roll\nRhythm&Blues = R&B\nDrum&Bass = Drum 'n' Bass")
        for left,right,target in [('rock','roll','Rock&Roll'),('Rhythm','Blues','R&B'),('drum','bass',"Drum 'n' Bass")]:
            for connector in [' and ', ' n ', " 'n' ", '&', " 'n'", ' ‘n’ ']:
                self.assertEqual(plugin.normalize([left+connector+right],rules),[target])
                self.assertEqual(self.c.normalized([left+connector+right]),[target])

    def test_default_full_name_and_abbreviations_merge(self):
        for value in ['RnB','rnb','RNB','r&b','R & B','R n B','R and B']:
            self.assertEqual(self.c.normalized([value]),['R&B'])
        self.assertEqual(self.c.normalized(['Rhythm and Blues; RnB; r&b']),['R&B'])
        self.assertEqual(self.c.normalized(["drum 'n'bass"]),["Drum 'n' Bass"])
        self.assertEqual(self.c.normalized(['rock n roll']),['Rock&Roll'])

    def run_scheduled(self, album):
        callbacks = []
        original = plugin.QTimer.singleShot
        plugin.QTimer.singleShot = lambda delay, callback: callbacks.append(callback)
        try:
            self.c.schedule(album)
            for callback in callbacks:
                callback()
        finally:
            plugin.QTimer.singleShot = original

    def test_initial_application_then_manual_edits_survive_events(self):
        albums = [self.album(['Electronica', 'Jazz']), self.album(['Rap', 'Rap'])]
        for album in albums:
            self.run_scheduled(album)
            self.assertTrue(album._advanced_genre_mapper_applied)
            for track in album.tracks:
                track.files[0].metadata['genre'] = 'My Manual Genre'
            self.run_scheduled(album)
            self.c = plugin.Controller(self.api)
            self.run_scheduled(album)
            self.assertTrue(all(t.files[0].metadata['genre'] == 'My Manual Genre' for t in album.tracks))

    def test_partial_album_waits_for_last_track(self):
        album = self.album(['Jazz', 'Rap', 'Rap'])
        last = album.tracks[-1]
        file = last.files.pop()
        self.run_scheduled(album)
        self.assertFalse(getattr(album, '_advanced_genre_mapper_applied', False))
        self.assertEqual(album.tracks[0].files[0].metadata['genre'], 'Jazz')
        last.files.append(file)
        self.run_scheduled(album)
        self.assertEqual(album.metadata['genre'], 'Rap')

    def test_loading_and_unmatched_files_defer_application(self):
        album = self.album(['Electronica'])
        album.loaded = False
        self.run_scheduled(album)
        self.assertNotIn('genre', album.metadata)
        album.loaded = True
        album.get_num_unmatched_files = lambda: 1
        self.run_scheduled(album)
        self.assertNotIn('genre', album.metadata)
        album.get_num_unmatched_files = lambda: 0
        self.run_scheduled(album)
        self.assertEqual(album.metadata['genre'], 'Electronic')

    def test_manual_action_cancels_queued_auto_but_remains_repeatable(self):
        album = self.album(['Electronica'])
        callbacks = []
        original = plugin.QTimer.singleShot
        plugin.QTimer.singleShot = lambda delay, callback: callbacks.append(callback)
        try:
            self.c.schedule(album)
            plugin.ApplyAlbumGenres().callback([album])
            album.tracks[0].files[0].metadata['genre'] = 'Manual'
            for callback in callbacks:
                callback()
            self.assertEqual(album.tracks[0].files[0].metadata['genre'], 'Manual')
            plugin.ApplyAlbumGenres().callback([album])
            self.assertEqual(album.tracks[0].files[0].metadata['genre'], 'Electronic')
        finally:
            plugin.QTimer.singleShot = original

    def test_no_pre_save_hook_registered(self):
        options = ModuleType('mapper.options')
        options.GenreOptions = object
        previous = sys.modules.get('mapper.options')
        sys.modules['mapper.options'] = options
        registrations = []
        class Config(dict):
            def register_option(self, name, value):
                self.setdefault(name, value)
        class Api:
            plugin_config = Config()
            def __getattr__(self, name):
                if name.startswith('register_'):
                    return lambda *args, **kwargs: registrations.append(name)
                raise AttributeError(name)
        try:
            original_start = plugin.Controller.start_display_sync
            plugin.Controller.start_display_sync = lambda self: None
            self.addCleanup(setattr, plugin.Controller, "start_display_sync", original_start)
            plugin.enable(Api())
            self.assertNotIn('register_file_pre_save_processor', registrations)
            self.assertIn('register_file_post_addition_to_track_processor', registrations)
            plugin.disable(None)
        finally:
            if previous is None:
                sys.modules.pop('mapper.options', None)
            else:
                sys.modules['mapper.options'] = previous

    def test_rym_search_and_verified_links(self):
        from urllib.parse import parse_qs, urlsplit
        url = rym_search('album', 'A & B', '中文 + Album')
        self.assertEqual(parse_qs(urlsplit(url).query),
                         {'searchtype': ['l'], 'searchterm': ['A & B 中文 + Album']})
        self.assertEqual(parse_qs(urlsplit(rym_search('artist', 'A')).query)['searchtype'], ['a'])
        for kind, path in [('artist', 'artist/name'), ('album', 'release/album/name/title')]:
            expected = 'https://rateyourmusic.com/' + path
            document = {'relations': [{'url': {'resource': expected}}]}
            self.assertEqual(rym_relation(document, kind), expected)
            document['relations'][0]['url']['resource'] = expected.replace('rateyourmusic.com', 'rateyourmusic.com.evil.test')
            self.assertIsNone(rym_relation(document, kind))
        self.assertIsNone(rym_relation({}, 'album'))

    def test_display_sync_preserves_manual_spelling_and_files(self):
        album = self.album(['Custom Jazz; RnB'] * 2)
        before = [(dict(t.metadata), dict(t.files[0].metadata), dict(t.files[0].orig_metadata)) for t in album.tracks]
        self.cfg['automatic'] = True
        self.c.normalized = lambda values: self.fail('Display sync must not normalize')
        self.c.apply = lambda album: self.fail('Display sync must not apply rules')
        self.c.sync_album_display(album)
        self.assertEqual(album.metadata.getall('genre'), ['Custom Jazz; RnB'])
        self.assertFalse(getattr(album, '_advanced_genre_mapper_applied', False))
        for t, old in zip(album.tracks, before):
            self.assertEqual((dict(t.metadata), dict(t.files[0].metadata), dict(t.files[0].orig_metadata)), old)
        for t in album.tracks:
            t.files[0].metadata['genre'] = ['Manual', 'SECOND']
        self.c.sync_album_display(album)
        self.assertEqual(album.metadata.getall('genre'), ['Manual', 'SECOND'])

    def test_display_sync_clears_mixed_empty_and_partial_summary(self):
        album = self.album(['Jazz', 'Jazz'])
        self.c.sync_album_display(album)
        album.tracks[1].files[0].metadata['genre'] = 'Rap'
        self.c.sync_album_display(album)
        self.assertNotIn('genre', album.metadata)
        self.assertEqual(album.tracks[0].files[0].metadata['genre'], 'Jazz')
        for track in album.tracks:
            track.files[0].metadata['genre'] = ''
        album.metadata['genre'] = 'Stale'
        self.c.sync_album_display(album)
        self.assertNotIn('genre', album.metadata)
        album.tracks[0].files[0].metadata['genre'] = 'Jazz'
        album.tracks[1].files.clear()
        album.metadata['genre'] = 'Stale'
        self.c.sync_album_display(album)
        self.assertNotIn('genre', album.metadata)

    def test_display_sync_already_loaded_and_disabled_automatic(self):
        album = self.album(['Jazz', 'Jazz'])
        self.api.tagger = SimpleNamespace(albums={album.id: album})
        self.cfg['automatic'] = False
        calls = []
        album.update = lambda **kw: calls.append(kw)
        self.c.sync_displays()
        self.c.sync_displays()
        self.assertEqual(calls, [{'update_tracks': False, 'update_selection': False}])
        self.c.active = False
        album.tracks[0].files[0].metadata['genre'] = 'Rap'
        self.c.sync_displays()
        self.assertEqual(album.metadata.getall('genre'), ['Jazz'])

    def test_current_majority_nine_against_one(self):
        album = self.album(['Old Genre'] * 10)
        for index, track in enumerate(album.tracks):
            track.files[0].metadata['genre'] = 'Jazz' if index < 9 else 'Rock'
        album._advanced_genre_mapper_applied = True
        self.c.overrides[album] = ['Old Override']
        self.c.sync_album_display(album)
        self.assertEqual(album.tracks[-1].files[0].metadata['genre'], 'Rock')
        self.c.sync_album_display(album)
        self.assertEqual(album.metadata.getall('genre'), ['Jazz'])
        self.assertTrue(all(t.files[0].metadata.getall('genre') == ['Jazz'] for t in album.tracks))
        self.assertTrue(all(t.files[0].orig_metadata.getall('genre') == ['Old Genre'] for t in album.tracks))
        for track in album.tracks:
            track.files[0].metadata['genre'] = 'My Manual Rock'
        self.c.sync_album_display(album)
        self.c.sync_album_display(album)
        self.assertEqual(album.metadata.getall('genre'), ['My Manual Rock'])
        self.assertTrue(all(t.files[0].metadata.getall('genre') == ['My Manual Rock'] for t in album.tracks))

    def test_current_majority_complete_lists_aliases_and_ties(self):
        album = self.album(['Electronica|IDM', 'IDM; Electronic', 'Jazz', ''])
        self.c.sync_album_display(album)
        self.c.sync_album_display(album)
        self.assertEqual(album.metadata.getall('genre'), ['Electronic; IDM'])
        tie = self.album(['Jazz', 'Rap'])
        self.c.sync_album_display(tie)
        self.c.sync_album_display(tie)
        self.assertEqual(tie.metadata.getall('genre'), ['Jazz'])

    def test_current_majority_disabled_or_incomplete_does_not_write(self):
        album = self.album(['Jazz', 'Jazz', 'Rock'])
        self.cfg['automatic'] = False
        self.c.sync_album_display(album)
        self.c.sync_album_display(album)
        self.assertEqual(album.tracks[-1].files[0].metadata['genre'], 'Rock')
        self.cfg['automatic'] = True
        album.get_num_unmatched_files = lambda: 1
        self.c.sync_album_display(album)
        self.c.sync_album_display(album)
        self.assertEqual(album.tracks[-1].files[0].metadata['genre'], 'Rock')

    def test_current_majority_waits_for_stable_batch_and_initial_run(self):
        album = self.album(['Jazz', 'Jazz', 'Rock'])
        self.c.pending[album] = 1
        self.c.sync_album_display(album)
        self.c.sync_album_display(album)
        self.assertEqual(album.tracks[-1].files[0].metadata['genre'], 'Rock')
        album._advanced_genre_mapper_applied = True
        album.tracks[0].files[0].metadata['genre'] = 'Rock'
        self.c.sync_album_display(album)
        self.assertEqual(album.tracks[1].files[0].metadata['genre'], 'Jazz')
        album.tracks[1].files[0].metadata['genre'] = 'Manual'
        self.c.sync_album_display(album)
        self.assertEqual(album.tracks[1].files[0].metadata['genre'], 'Manual')
        self.c.sync_album_display(album)
        self.assertEqual(album.tracks[1].files[0].metadata['genre'], 'Rock')

    def test_auto_toggle(self):
        a=self.album(['Electronica'])
        self.cfg['automatic']=False
        self.run_scheduled(a)
        self.assertEqual(a.tracks[0].files[0].metadata['genre'],'Electronica')

if __name__=='__main__': unittest.main(verbosity=2)
