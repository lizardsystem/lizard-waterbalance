# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Concentration'
        db.create_table('lizard_waterbalance_concentration', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('substance', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('flow_name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('minimum', self.gf('django.db.models.fields.IntegerField')()),
            ('increment', self.gf('django.db.models.fields.IntegerField')()),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(related_name='concentrations', to=orm['lizard_waterbalance.WaterbalanceArea'])),
        ))
        db.send_create_signal('lizard_waterbalance', ['Concentration'])


    def backwards(self, orm):
        
        # Deleting model 'Concentration'
        db.delete_table('lizard_waterbalance_concentration')


    models = {
        'lizard_waterbalance.bucket': {
            'Meta': {'object_name': 'Bucket'},
            'computed_flow_off': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'computed_seepage': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'crop_evaporation_factor': ('django.db.models.fields.FloatField', [], {}),
            'drainage': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'drainage_fraction': ('django.db.models.fields.FloatField', [], {}),
            'equi_water_level': ('django.db.models.fields.FloatField', [], {}),
            'external_discharge': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'flow_off': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'indraft': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'indraft_fraction': ('django.db.models.fields.FloatField', [], {}),
            'infiltration': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'init_water_level': ('django.db.models.fields.FloatField', [], {}),
            'max_water_level': ('django.db.models.fields.FloatField', [], {}),
            'min_crop_evaporation_factor': ('django.db.models.fields.FloatField', [], {}),
            'min_water_level': ('django.db.models.fields.FloatField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'open_water': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'buckets'", 'null': 'True', 'to': "orm['lizard_waterbalance.OpenWater']"}),
            'porosity': ('django.db.models.fields.FloatField', [], {}),
            'seepage': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'surface': ('django.db.models.fields.IntegerField', [], {}),
            'surface_type': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'upper_crop_evaporation_factor': ('django.db.models.fields.FloatField', [], {}),
            'upper_drainage_fraction': ('django.db.models.fields.FloatField', [], {}),
            'upper_indraft_fraction': ('django.db.models.fields.FloatField', [], {}),
            'upper_min_crop_evaporation_factor': ('django.db.models.fields.FloatField', [], {}),
            'upper_porosity': ('django.db.models.fields.FloatField', [], {})
        },
        'lizard_waterbalance.concentration': {
            'Meta': {'object_name': 'Concentration'},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'concentrations'", 'to': "orm['lizard_waterbalance.WaterbalanceArea']"}),
            'flow_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'increment': ('django.db.models.fields.IntegerField', [], {}),
            'minimum': ('django.db.models.fields.IntegerField', [], {}),
            'substance': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'lizard_waterbalance.openwater': {
            'Meta': {'object_name': 'OpenWater'},
            'bottom_height': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'computed_evaporation': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'computed_infiltration': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'computed_precipitation': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'computed_seepage': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'crop_evaporation_factor': ('django.db.models.fields.FloatField', [], {}),
            'drained': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'flow_off': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'fractions_drained': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'fractions_flow_off': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'fractions_hardened': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'fractions_initial': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'fractions_precipitation': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'fractions_seepage': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'fractions_undrained': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'hardened': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'indraft': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'init_water_level': ('django.db.models.fields.FloatField', [], {}),
            'maximum_level': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'minimum_level': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'seepage': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'storage': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'surface': ('django.db.models.fields.IntegerField', [], {}),
            'target_level': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'undrained': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"})
        },
        'lizard_waterbalance.pumpingstation': {
            'Meta': {'object_name': 'PumpingStation'},
            'computed_level_control': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'fractions': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'into': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'level_control': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'open_water': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'pumping_stations'", 'null': 'True', 'to': "orm['lizard_waterbalance.OpenWater']"}),
            'percentage': ('django.db.models.fields.FloatField', [], {})
        },
        'lizard_waterbalance.pumpline': {
            'Meta': {'object_name': 'PumpLine'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pump': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pump_lines'", 'to': "orm['lizard_waterbalance.PumpingStation']"}),
            'timeserie': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"})
        },
        'lizard_waterbalance.timeseries': {
            'Meta': {'object_name': 'Timeseries'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'lizard_waterbalance.timeseriesevent': {
            'Meta': {'ordering': "['time']", 'object_name': 'TimeseriesEvent'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {}),
            'timeseries': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'timeseries_events'", 'to': "orm['lizard_waterbalance.Timeseries']"}),
            'value': ('django.db.models.fields.FloatField', [], {})
        },
        'lizard_waterbalance.waterbalancearea': {
            'Meta': {'ordering': "('name',)", 'object_name': 'WaterbalanceArea'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'evaporation': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'open_water': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_waterbalance.OpenWater']", 'null': 'True', 'blank': 'True'}),
            'precipitation': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'lizard_waterbalance.waterbalancelabel': {
            'Meta': {'ordering': "('order_index',)", 'object_name': 'WaterbalanceLabel'},
            'flow_type': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'order_index': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_waterbalance.WaterbalanceLabel']", 'null': 'True', 'blank': 'True'})
        },
        'lizard_waterbalance.waterbalancetimeserie': {
            'Meta': {'object_name': 'WaterbalanceTimeserie'},
            'chloride': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.Timeseries']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_waterbalance.WaterbalanceLabel']", 'null': 'True', 'blank': 'True'}),
            'nitrate': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.Timeseries']"}),
            'phosphate': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.Timeseries']"}),
            'sulfate': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.Timeseries']"}),
            'volume': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.Timeseries']"})
        }
    }

    complete_apps = ['lizard_waterbalance']
