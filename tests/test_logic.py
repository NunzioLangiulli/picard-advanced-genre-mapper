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
from mapper.comparison import ComparisonDialog,genre_names,source_changes

class Metadata(dict):
    def getall(self,key):
        value=self.get(key,[])
        return ([value] if value else []) if isinstance(value,str) else list(value)
class Item:
    def __init__(self,**kw): self.__dict__.update(kw)
    def update(self): pass

class Tests(unittest.TestCase):
    def setUp(self):
        self.cfg=dict(plugin.DEFAULTS)
        self.api=SimpleNamespace(plugin_config=self.cfg,logger=SimpleNamespace(error=lambda *a:None))
        self.c=plugin.Controller(self.api)
        plugin._controller=self.c
    def album(self,values):
        a=Item(tracks=[],metadata=Metadata(),id='11111111-1111-4111-8111-111111111111')
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
        plugin.before_save(self.api,a.tracks[0].files[0])
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
        plugin.before_save(self.api,a.tracks[0].files[0])
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
        d.request=lambda entity,identifier,row:calls.append((entity,identifier,row))
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

    def test_auto_toggle(self):
        a=self.album(['Electronica'])
        self.cfg['automatic']=False
        plugin.before_save(self.api,a.tracks[0].files[0])
        self.assertEqual(a.tracks[0].files[0].metadata['genre'],'Electronica')

if __name__=='__main__': unittest.main(verbosity=2)
