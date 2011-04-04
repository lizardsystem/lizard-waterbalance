# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Label.color'
        db.add_column('lizard_waterbalance_label', 'color', self.gf('lizard_map.models.ColorField')(default='000000', max_length=8), keep_default=False)

        # Adding field 'Label.color_increment'
        db.add_column('lizard_waterbalance_label', 'color_increment', self.gf('lizard_map.models.ColorField')(default='000000', max_length=8), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Label.color'
        db.delete_column('lizard_waterbalance_label', 'color')

        # Deleting field 'Label.color_increment'
        db.delete_column('lizard_waterbalance_label', 'color_increment')


    models = {
        'lizard_waterbalance.bucket': {
            'Meta': {'object_name': 'Bucket'},
            'crop_evaporation_factor': ('django.db.models.fields.FloatField', [], {}),
            'drainage_fraction': ('django.db.models.fields.FloatField', [], {}),
            'equi_water_level': ('django.db.models.fields.FloatField', [], {}),
            'external_discharge': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'indraft_fraction': ('django.db.models.fields.FloatField', [], {}),
            'init_water_level': ('django.db.models.fields.FloatField', [], {}),
            'max_water_level': ('django.db.models.fields.FloatField', [], {}),
            'min_crop_evaporation_factor': ('django.db.models.fields.FloatField', [], {}),
            'min_water_level': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'open_water': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'buckets'", 'to': "orm['lizard_waterbalance.OpenWater']"}),
            'porosity': ('django.db.models.fields.FloatField', [], {}),
            'results': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'bucket_results'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'seepage': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'bucket_seepage'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'surface': ('django.db.models.fields.IntegerField', [], {}),
            'surface_type': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'upper_drainage_fraction': ('django.db.models.fields.FloatField', [], {}),
            'upper_equi_water_level': ('django.db.models.fields.FloatField', [], {}),
            'upper_indraft_fraction': ('django.db.models.fields.FloatField', [], {}),
            'upper_init_water_level': ('django.db.models.fields.FloatField', [], {}),
            'upper_max_water_level': ('django.db.models.fields.FloatField', [], {}),
            'upper_min_water_level': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'upper_porosity': ('django.db.models.fields.FloatField', [], {})
        },
        'lizard_waterbalance.concentration': {
            'Meta': {'unique_together': "(('configuration', 'label'),)", 'object_name': 'Concentration'},
            'cl_concentration': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'configuration': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'config_concentrations'", 'to': "orm['lizard_waterbalance.WaterbalanceConf']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'label_concentrations'", 'to': "orm['lizard_waterbalance.Label']"}),
            'n_incremental': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'n_lower_concentration': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'p_incremental': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'p_lower_concentration': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'so4_incremental': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'so4_lower_concentration': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'stof_increment': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'stof_lower_concentration': ('django.db.models.fields.FloatField', [], {'default': '0.0'})
        },
        'lizard_waterbalance.label': {
            'Meta': {'ordering': "('order', 'name')", 'object_name': 'Label'},
            'color': ('lizard_map.models.ColorField', [], {'max_length': '8'}),
            'color_increment': ('lizard_map.models.ColorField', [], {'max_length': '8'}),
            'flow_type': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_waterbalance.Label']", 'null': 'True', 'blank': 'True'}),
            'program_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'})
        },
        'lizard_waterbalance.openwater': {
            'Meta': {'object_name': 'OpenWater'},
            'bottom_height': ('django.db.models.fields.FloatField', [], {}),
            'evaporation': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'configuration_evaporation'", 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'infiltration': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'open_water_infiltration'", 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'init_water_level': ('django.db.models.fields.FloatField', [], {}),
            'maximum_level': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'open_water_max_level'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'minimum_level': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'open_water_min_level'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'precipitation': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'configuration_precipitation'", 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'seepage': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'open_water_seepage'", 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'surface': ('django.db.models.fields.IntegerField', [], {}),
            'target_level': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'open_water_targetlevel'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"})
        },
        'lizard_waterbalance.parameter': {
            'Meta': {'object_name': 'Parameter'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'parameter': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'sourcetype': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'})
        },
        'lizard_waterbalance.pumpingstation': {
            'Meta': {'unique_together': "(('open_water', 'label'),)", 'object_name': 'PumpingStation'},
            'computed_level_control': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'into': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'label': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pumping_stations'", 'to': "orm['lizard_waterbalance.Label']"}),
            'max_discharge': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'open_water': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pumping_stations'", 'to': "orm['lizard_waterbalance.OpenWater']"}),
            'percentage': ('django.db.models.fields.FloatField', [], {}),
            'results': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'pumping_station_result'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"})
        },
        'lizard_waterbalance.pumpline': {
            'Meta': {'object_name': 'PumpLine'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'pumping_station': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pump_lines'", 'to': "orm['lizard_waterbalance.PumpingStation']"}),
            'timeserie': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pump_line_timeserie'", 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"})
        },
        'lizard_waterbalance.sobekbucket': {
            'Meta': {'object_name': 'SobekBucket'},
            'drainage_indraft': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'sobekbucket_drainage_indraft'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'flow_off': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'sobekbucket_flow_off'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'open_water': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sobekbuckets'", 'to': "orm['lizard_waterbalance.OpenWater']"}),
            'surface_type': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'lizard_waterbalance.timeseries': {
            'Meta': {'object_name': 'Timeseries'},
            'default_value': ('django.db.models.fields.FloatField', [], {'default': '0.0', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'stick_to_last_value': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'})
        },
        'lizard_waterbalance.timeseriesevent': {
            'Meta': {'ordering': "['time']", 'object_name': 'TimeseriesEvent'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {}),
            'timeseries': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'timeseries_events'", 'to': "orm['lizard_waterbalance.Timeseries']"}),
            'value': ('django.db.models.fields.FloatField', [], {})
        },
        'lizard_waterbalance.timeseriesfews': {
            'Meta': {'object_name': 'TimeseriesFews'},
            'default_value': ('django.db.models.fields.FloatField', [], {'default': '0.0', 'null': 'True', 'blank': 'True'}),
            'fkey': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lkey': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'pkey': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'stick_to_last_value': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'})
        },
        'lizard_waterbalance.waterbalancearea': {
            'Meta': {'ordering': "('name',)", 'object_name': 'WaterbalanceArea'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'geom': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'lizard_waterbalance.waterbalanceconf': {
            'Meta': {'ordering': "('waterbalance_area__name', 'waterbalance_scenario__order')", 'unique_together': "(('waterbalance_area', 'waterbalance_scenario'),)", 'object_name': 'WaterbalanceConf'},
            'calculation_end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'calculation_start_date': ('django.db.models.fields.DateTimeField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'labels': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'configuration_results'", 'to': "orm['lizard_waterbalance.Label']", 'through': "orm['lizard_waterbalance.Concentration']", 'blank': 'True', 'symmetrical': 'False', 'null': 'True'}),
            'open_water': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['lizard_waterbalance.OpenWater']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'references': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'configuration_references'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'results': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'configuration_results'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'waterbalance_area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_waterbalance.WaterbalanceArea']"}),
            'waterbalance_scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_waterbalance.WaterbalanceScenario']"})
        },
        'lizard_waterbalance.waterbalancescenario': {
            'Meta': {'ordering': "('order',)", 'object_name': 'WaterbalanceScenario'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'lizard_waterbalance.waterbalancetimeserie': {
            'Meta': {'unique_together': "(('name', 'parameter', 'configuration', 'timestep'),)", 'object_name': 'WaterbalanceTimeserie'},
            'configuration': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_waterbalance.WaterbalanceConf']", 'null': 'True', 'blank': 'True'}),
            'fews_timeseries': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.TimeseriesFews']"}),
            'hint_datetime_end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'hint_datetime_start': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'local_timeseries': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.Timeseries']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'parameter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_waterbalance.Parameter']"}),
            'timestep': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'use_fews': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['lizard_waterbalance']
