# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Timeseries'
        db.create_table('lizard_waterbalance_timeseries', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('default_value', self.gf('django.db.models.fields.FloatField')(default=0.0, null=True, blank=True)),
            ('stick_to_last_value', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
        ))
        db.send_create_signal('lizard_waterbalance', ['Timeseries'])

        # Adding model 'TimeseriesEvent'
        db.create_table('lizard_waterbalance_timeseriesevent', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')()),
            ('value', self.gf('django.db.models.fields.FloatField')()),
            ('timeseries', self.gf('django.db.models.fields.related.ForeignKey')(related_name='timeseries_events', to=orm['lizard_waterbalance.Timeseries'])),
        ))
        db.send_create_signal('lizard_waterbalance', ['TimeseriesEvent'])

        # Adding model 'TimeseriesFews'
        db.create_table('lizard_waterbalance_timeseriesfews', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('pkey', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('fkey', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('lkey', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('lizard_waterbalance', ['TimeseriesFews'])

        # Adding model 'Parameter'
        db.create_table('lizard_waterbalance_parameter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('unit', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('sourcetype', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('parameter', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('lizard_waterbalance', ['Parameter'])

        # Adding model 'WaterbalanceTimeserie'
        db.create_table('lizard_waterbalance_waterbalancetimeserie', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('parameter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_waterbalance.Parameter'])),
            ('use_fews', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('fews_timeseries', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['lizard_waterbalance.TimeseriesFews'])),
            ('local_timeseries', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['lizard_waterbalance.Timeseries'])),
            ('configuration', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_waterbalance.WaterbalanceConf'], null=True, blank=True)),
            ('timestep', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('hint_datetime_start', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('hint_datetime_end', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('lizard_waterbalance', ['WaterbalanceTimeserie'])

        # Adding unique constraint on 'WaterbalanceTimeserie', fields ['name', 'parameter', 'configuration', 'timestep']
        db.create_unique('lizard_waterbalance_waterbalancetimeserie', ['name', 'parameter_id', 'configuration_id', 'timestep'])

        # Adding model 'OpenWater'
        db.create_table('lizard_waterbalance_openwater', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('surface', self.gf('django.db.models.fields.IntegerField')()),
            ('bottom_height', self.gf('django.db.models.fields.FloatField')()),
            ('minimum_level', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='open_water_min_level', null=True, to=orm['lizard_waterbalance.WaterbalanceTimeserie'])),
            ('maximum_level', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='open_water_max_level', null=True, to=orm['lizard_waterbalance.WaterbalanceTimeserie'])),
            ('target_level', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='open_water_targetlevel', null=True, to=orm['lizard_waterbalance.WaterbalanceTimeserie'])),
            ('init_water_level', self.gf('django.db.models.fields.FloatField')()),
            ('precipitation', self.gf('django.db.models.fields.related.ForeignKey')(related_name='configuration_precipitation', to=orm['lizard_waterbalance.WaterbalanceTimeserie'])),
            ('evaporation', self.gf('django.db.models.fields.related.ForeignKey')(related_name='configuration_evaporation', to=orm['lizard_waterbalance.WaterbalanceTimeserie'])),
            ('seepage', self.gf('django.db.models.fields.related.ForeignKey')(related_name='open_water_seepage', to=orm['lizard_waterbalance.WaterbalanceTimeserie'])),
            ('infiltration', self.gf('django.db.models.fields.related.ForeignKey')(related_name='open_water_infiltration', to=orm['lizard_waterbalance.WaterbalanceTimeserie'])),
        ))
        db.send_create_signal('lizard_waterbalance', ['OpenWater'])

        # Adding model 'Bucket'
        db.create_table('lizard_waterbalance_bucket', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('open_water', self.gf('django.db.models.fields.related.ForeignKey')(related_name='buckets', to=orm['lizard_waterbalance.OpenWater'])),
            ('surface_type', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('surface', self.gf('django.db.models.fields.IntegerField')()),
            ('seepage', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='bucket_seepage', null=True, to=orm['lizard_waterbalance.WaterbalanceTimeserie'])),
            ('porosity', self.gf('django.db.models.fields.FloatField')()),
            ('crop_evaporation_factor', self.gf('django.db.models.fields.FloatField')()),
            ('min_crop_evaporation_factor', self.gf('django.db.models.fields.FloatField')()),
            ('drainage_fraction', self.gf('django.db.models.fields.FloatField')()),
            ('indraft_fraction', self.gf('django.db.models.fields.FloatField')()),
            ('max_water_level', self.gf('django.db.models.fields.FloatField')()),
            ('equi_water_level', self.gf('django.db.models.fields.FloatField')()),
            ('min_water_level', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('init_water_level', self.gf('django.db.models.fields.FloatField')()),
            ('external_discharge', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('upper_porosity', self.gf('django.db.models.fields.FloatField')()),
            ('upper_drainage_fraction', self.gf('django.db.models.fields.FloatField')()),
            ('upper_indraft_fraction', self.gf('django.db.models.fields.FloatField')()),
            ('upper_max_water_level', self.gf('django.db.models.fields.FloatField')()),
            ('upper_equi_water_level', self.gf('django.db.models.fields.FloatField')()),
            ('upper_min_water_level', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('upper_init_water_level', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('lizard_waterbalance', ['Bucket'])

        # Adding M2M table for field results on 'Bucket'
        db.create_table('lizard_waterbalance_bucket_results', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bucket', models.ForeignKey(orm['lizard_waterbalance.bucket'], null=False)),
            ('waterbalancetimeserie', models.ForeignKey(orm['lizard_waterbalance.waterbalancetimeserie'], null=False))
        ))
        db.create_unique('lizard_waterbalance_bucket_results', ['bucket_id', 'waterbalancetimeserie_id'])

        # Adding model 'SobekBucket'
        db.create_table('lizard_waterbalance_sobekbucket', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('open_water', self.gf('django.db.models.fields.related.ForeignKey')(related_name='sobekbuckets', to=orm['lizard_waterbalance.OpenWater'])),
            ('surface_type', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('flow_off', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='sobekbucket_flow_off', null=True, to=orm['lizard_waterbalance.WaterbalanceTimeserie'])),
            ('drainage_indraft', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='sobekbucket_drainage_indraft', null=True, to=orm['lizard_waterbalance.WaterbalanceTimeserie'])),
        ))
        db.send_create_signal('lizard_waterbalance', ['SobekBucket'])

        # Adding model 'PumpingStation'
        db.create_table('lizard_waterbalance_pumpingstation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('open_water', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pumping_stations', to=orm['lizard_waterbalance.OpenWater'])),
            ('label', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pumping_stations', to=orm['lizard_waterbalance.Label'])),
            ('into', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('percentage', self.gf('django.db.models.fields.FloatField')()),
            ('max_discharge', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('computed_level_control', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('lizard_waterbalance', ['PumpingStation'])

        # Adding unique constraint on 'PumpingStation', fields ['open_water', 'label']
        db.create_unique('lizard_waterbalance_pumpingstation', ['open_water_id', 'label_id'])

        # Adding M2M table for field results on 'PumpingStation'
        db.create_table('lizard_waterbalance_pumpingstation_results', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('pumpingstation', models.ForeignKey(orm['lizard_waterbalance.pumpingstation'], null=False)),
            ('waterbalancetimeserie', models.ForeignKey(orm['lizard_waterbalance.waterbalancetimeserie'], null=False))
        ))
        db.create_unique('lizard_waterbalance_pumpingstation_results', ['pumpingstation_id', 'waterbalancetimeserie_id'])

        # Adding model 'PumpLine'
        db.create_table('lizard_waterbalance_pumpline', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('pumping_station', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pump_lines', to=orm['lizard_waterbalance.PumpingStation'])),
            ('timeserie', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pump_line_timeserie', to=orm['lizard_waterbalance.WaterbalanceTimeserie'])),
        ))
        db.send_create_signal('lizard_waterbalance', ['PumpLine'])

        # Adding model 'WaterbalanceScenario'
        db.create_table('lizard_waterbalance_waterbalancescenario', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('lizard_waterbalance', ['WaterbalanceScenario'])

        # Adding model 'WaterbalanceArea'
        db.create_table('lizard_waterbalance_waterbalancearea', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('geom', self.gf('django.contrib.gis.db.models.fields.MultiPolygonField')(null=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('lizard_waterbalance', ['WaterbalanceArea'])

        # Adding model 'WaterbalanceConf'
        db.create_table('lizard_waterbalance_waterbalanceconf', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('waterbalance_area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_waterbalance.WaterbalanceArea'])),
            ('waterbalance_scenario', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_waterbalance.WaterbalanceScenario'])),
            ('open_water', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['lizard_waterbalance.OpenWater'], unique=True, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('calculation_start_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('calculation_end_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('lizard_waterbalance', ['WaterbalanceConf'])

        # Adding unique constraint on 'WaterbalanceConf', fields ['waterbalance_area', 'waterbalance_scenario']
        db.create_unique('lizard_waterbalance_waterbalanceconf', ['waterbalance_area_id', 'waterbalance_scenario_id'])

        # Adding M2M table for field results on 'WaterbalanceConf'
        db.create_table('lizard_waterbalance_waterbalanceconf_results', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('waterbalanceconf', models.ForeignKey(orm['lizard_waterbalance.waterbalanceconf'], null=False)),
            ('waterbalancetimeserie', models.ForeignKey(orm['lizard_waterbalance.waterbalancetimeserie'], null=False))
        ))
        db.create_unique('lizard_waterbalance_waterbalanceconf_results', ['waterbalanceconf_id', 'waterbalancetimeserie_id'])

        # Adding M2M table for field references on 'WaterbalanceConf'
        db.create_table('lizard_waterbalance_waterbalanceconf_references', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('waterbalanceconf', models.ForeignKey(orm['lizard_waterbalance.waterbalanceconf'], null=False)),
            ('waterbalancetimeserie', models.ForeignKey(orm['lizard_waterbalance.waterbalancetimeserie'], null=False))
        ))
        db.create_unique('lizard_waterbalance_waterbalanceconf_references', ['waterbalanceconf_id', 'waterbalancetimeserie_id'])

        # Adding model 'Label'
        db.create_table('lizard_waterbalance_label', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('program_name', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_waterbalance.Label'], null=True, blank=True)),
            ('flow_type', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('lizard_waterbalance', ['Label'])

        # Adding model 'Concentration'
        db.create_table('lizard_waterbalance_concentration', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('label', self.gf('django.db.models.fields.related.ForeignKey')(related_name='label_concentrations', to=orm['lizard_waterbalance.Label'])),
            ('configuration', self.gf('django.db.models.fields.related.ForeignKey')(related_name='config_concentrations', to=orm['lizard_waterbalance.WaterbalanceConf'])),
            ('stof_lower_concentration', self.gf('django.db.models.fields.FloatField')(default=0.0)),
            ('stof_increment', self.gf('django.db.models.fields.FloatField')(default=0.0)),
            ('cl_concentration', self.gf('django.db.models.fields.FloatField')(default=0.0)),
            ('p_lower_concentration', self.gf('django.db.models.fields.FloatField')(default=0.0)),
            ('p_incremental', self.gf('django.db.models.fields.FloatField')(default=0.0)),
            ('n_lower_concentration', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('n_incremental', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('so4_lower_concentration', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('so4_incremental', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
        ))
        db.send_create_signal('lizard_waterbalance', ['Concentration'])

        # Adding unique constraint on 'Concentration', fields ['configuration', 'label']
        db.create_unique('lizard_waterbalance_concentration', ['configuration_id', 'label_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'Concentration', fields ['configuration', 'label']
        db.delete_unique('lizard_waterbalance_concentration', ['configuration_id', 'label_id'])

        # Removing unique constraint on 'WaterbalanceConf', fields ['waterbalance_area', 'waterbalance_scenario']
        db.delete_unique('lizard_waterbalance_waterbalanceconf', ['waterbalance_area_id', 'waterbalance_scenario_id'])

        # Removing unique constraint on 'PumpingStation', fields ['open_water', 'label']
        db.delete_unique('lizard_waterbalance_pumpingstation', ['open_water_id', 'label_id'])

        # Removing unique constraint on 'WaterbalanceTimeserie', fields ['name', 'parameter', 'configuration', 'timestep']
        db.delete_unique('lizard_waterbalance_waterbalancetimeserie', ['name', 'parameter_id', 'configuration_id', 'timestep'])

        # Deleting model 'Timeseries'
        db.delete_table('lizard_waterbalance_timeseries')

        # Deleting model 'TimeseriesEvent'
        db.delete_table('lizard_waterbalance_timeseriesevent')

        # Deleting model 'TimeseriesFews'
        db.delete_table('lizard_waterbalance_timeseriesfews')

        # Deleting model 'Parameter'
        db.delete_table('lizard_waterbalance_parameter')

        # Deleting model 'WaterbalanceTimeserie'
        db.delete_table('lizard_waterbalance_waterbalancetimeserie')

        # Deleting model 'OpenWater'
        db.delete_table('lizard_waterbalance_openwater')

        # Deleting model 'Bucket'
        db.delete_table('lizard_waterbalance_bucket')

        # Removing M2M table for field results on 'Bucket'
        db.delete_table('lizard_waterbalance_bucket_results')

        # Deleting model 'SobekBucket'
        db.delete_table('lizard_waterbalance_sobekbucket')

        # Deleting model 'PumpingStation'
        db.delete_table('lizard_waterbalance_pumpingstation')

        # Removing M2M table for field results on 'PumpingStation'
        db.delete_table('lizard_waterbalance_pumpingstation_results')

        # Deleting model 'PumpLine'
        db.delete_table('lizard_waterbalance_pumpline')

        # Deleting model 'WaterbalanceScenario'
        db.delete_table('lizard_waterbalance_waterbalancescenario')

        # Deleting model 'WaterbalanceArea'
        db.delete_table('lizard_waterbalance_waterbalancearea')

        # Deleting model 'WaterbalanceConf'
        db.delete_table('lizard_waterbalance_waterbalanceconf')

        # Removing M2M table for field results on 'WaterbalanceConf'
        db.delete_table('lizard_waterbalance_waterbalanceconf_results')

        # Removing M2M table for field references on 'WaterbalanceConf'
        db.delete_table('lizard_waterbalance_waterbalanceconf_references')

        # Deleting model 'Label'
        db.delete_table('lizard_waterbalance_label')

        # Deleting model 'Concentration'
        db.delete_table('lizard_waterbalance_concentration')


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
            'fkey': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lkey': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'pkey': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
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
