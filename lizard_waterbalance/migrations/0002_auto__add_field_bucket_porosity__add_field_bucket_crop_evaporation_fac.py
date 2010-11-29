# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Bucket.porosity'
        db.add_column('lizard_waterbalance_bucket', 'porosity', self.gf('django.db.models.fields.FloatField')(default=1), keep_default=False)

        # Adding field 'Bucket.crop_evaporation_factor'
        db.add_column('lizard_waterbalance_bucket', 'crop_evaporation_factor', self.gf('django.db.models.fields.FloatField')(default=1), keep_default=False)

        # Adding field 'Bucket.min_crop_evaporation_factor'
        db.add_column('lizard_waterbalance_bucket', 'min_crop_evaporation_factor', self.gf('django.db.models.fields.FloatField')(default=1), keep_default=False)

        # Adding field 'Bucket.drainage_fraction'
        db.add_column('lizard_waterbalance_bucket', 'drainage_fraction', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Bucket.infiltration_fraction'
        db.add_column('lizard_waterbalance_bucket', 'infiltration_fraction', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Bucket.max_water_level'
        db.add_column('lizard_waterbalance_bucket', 'max_water_level', self.gf('django.db.models.fields.FloatField')(default=0.002), keep_default=False)

        # Adding field 'Bucket.equi_water_level'
        db.add_column('lizard_waterbalance_bucket', 'equi_water_level', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Bucket.min_water_level'
        db.add_column('lizard_waterbalance_bucket', 'min_water_level', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Bucket.init_water_level'
        db.add_column('lizard_waterbalance_bucket', 'init_water_level', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Bucket.external_discharge'
        db.add_column('lizard_waterbalance_bucket', 'external_discharge', self.gf('django.db.models.fields.IntegerField')(default=20), keep_default=False)

        # Adding field 'Bucket.computed_seepage'
        db.add_column('lizard_waterbalance_bucket', 'computed_seepage', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['lizard_waterbalance.WaterbalanceTimeserie']), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Bucket.porosity'
        db.delete_column('lizard_waterbalance_bucket', 'porosity')

        # Deleting field 'Bucket.crop_evaporation_factor'
        db.delete_column('lizard_waterbalance_bucket', 'crop_evaporation_factor')

        # Deleting field 'Bucket.min_crop_evaporation_factor'
        db.delete_column('lizard_waterbalance_bucket', 'min_crop_evaporation_factor')

        # Deleting field 'Bucket.drainage_fraction'
        db.delete_column('lizard_waterbalance_bucket', 'drainage_fraction')

        # Deleting field 'Bucket.infiltration_fraction'
        db.delete_column('lizard_waterbalance_bucket', 'infiltration_fraction')

        # Deleting field 'Bucket.max_water_level'
        db.delete_column('lizard_waterbalance_bucket', 'max_water_level')

        # Deleting field 'Bucket.equi_water_level'
        db.delete_column('lizard_waterbalance_bucket', 'equi_water_level')

        # Deleting field 'Bucket.min_water_level'
        db.delete_column('lizard_waterbalance_bucket', 'min_water_level')

        # Deleting field 'Bucket.init_water_level'
        db.delete_column('lizard_waterbalance_bucket', 'init_water_level')

        # Deleting field 'Bucket.external_discharge'
        db.delete_column('lizard_waterbalance_bucket', 'external_discharge')

        # Deleting field 'Bucket.computed_seepage'
        db.delete_column('lizard_waterbalance_bucket', 'computed_seepage_id')


    models = {
        'lizard_fewsunblobbed.filter': {
            'Meta': {'object_name': 'Filter', 'db_table': "u'filter'"},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'fews_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64', 'db_column': "'id'"}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True', 'db_column': "'fkey'"}),
            'isendnode': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'issubfilter': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_fewsunblobbed.Filter']", 'null': 'True', 'db_column': "'parentfkey'", 'blank': 'True'})
        },
        'lizard_fewsunblobbed.location': {
            'Meta': {'object_name': 'Location', 'db_table': "u'location'"},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'blank': 'True'}),
            'lkey': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'parentid': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'shortname': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'tooltiptext': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'x': ('django.db.models.fields.FloatField', [], {'blank': 'True'}),
            'y': ('django.db.models.fields.FloatField', [], {'blank': 'True'}),
            'z': ('django.db.models.fields.FloatField', [], {'blank': 'True'})
        },
        'lizard_fewsunblobbed.parameter': {
            'Meta': {'object_name': 'Parameter', 'db_table': "u'parameter'"},
            'id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'parametergroup': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'parametertype': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'pkey': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'shortname': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'})
        },
        'lizard_fewsunblobbed.timeserie': {
            'Meta': {'object_name': 'Timeserie', 'db_table': "u'timeserie'"},
            'filterkey': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_fewsunblobbed.Filter']", 'db_column': "'filterkey'"}),
            'locationkey': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_fewsunblobbed.Location']", 'db_column': "'locationkey'"}),
            'moduleinstanceid': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'parameterkey': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_fewsunblobbed.Parameter']", 'db_column': "'parameterkey'"}),
            'timestep': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'tkey': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'})
        },
        'lizard_waterbalance.bucket': {
            'Meta': {'object_name': 'Bucket'},
            'computed_flow_off': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'computed_seepage': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'crop_evaporation_factor': ('django.db.models.fields.FloatField', [], {}),
            'drainage': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'drainage_fraction': ('django.db.models.fields.FloatField', [], {}),
            'equi_water_level': ('django.db.models.fields.FloatField', [], {}),
            'external_discharge': ('django.db.models.fields.IntegerField', [], {}),
            'flow_off': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'indraft': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'infiltration': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'infiltration_fraction': ('django.db.models.fields.FloatField', [], {}),
            'init_water_level': ('django.db.models.fields.FloatField', [], {}),
            'max_water_level': ('django.db.models.fields.FloatField', [], {}),
            'min_crop_evaporation_factor': ('django.db.models.fields.FloatField', [], {}),
            'min_water_level': ('django.db.models.fields.FloatField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'open_water': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'buckets'", 'null': 'True', 'to': "orm['lizard_waterbalance.Bucket']"}),
            'porosity': ('django.db.models.fields.FloatField', [], {}),
            'seepage': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'surface': ('django.db.models.fields.IntegerField', [], {})
        },
        'lizard_waterbalance.openwater': {
            'Meta': {'object_name': 'OpenWater', '_ormbases': ['lizard_waterbalance.Bucket']},
            'bucket_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['lizard_waterbalance.Bucket']", 'unique': 'True', 'primary_key': 'True'}),
            'maximum_level': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'minimum_level': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'sluice_error': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"}),
            'target_level': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"})
        },
        'lizard_waterbalance.pumpingstation': {
            'Meta': {'object_name': 'PumpingStation'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'into': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'open_water': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pumping_stations'", 'to': "orm['lizard_waterbalance.OpenWater']"}),
            'percentage': ('django.db.models.fields.FloatField', [], {})
        },
        'lizard_waterbalance.pumpline': {
            'Meta': {'object_name': 'PumpLine'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pump': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pump_lines'", 'to': "orm['lizard_waterbalance.PumpingStation']"}),
            'timeserie': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['lizard_waterbalance.WaterbalanceTimeserie']"})
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
            'chloride': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['lizard_fewsunblobbed.Timeserie']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_waterbalance.WaterbalanceLabel']"}),
            'nitrate': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['lizard_fewsunblobbed.Timeserie']"}),
            'phosphate': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['lizard_fewsunblobbed.Timeserie']"}),
            'sulfate': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['lizard_fewsunblobbed.Timeserie']"}),
            'volume': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['lizard_fewsunblobbed.Timeserie']"})
        }
    }

    complete_apps = ['lizard_waterbalance']
