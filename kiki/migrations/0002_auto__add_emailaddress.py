# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'EmailAddress'
        db.create_table('kiki_emailaddress', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=75)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='emails', null=True, to=orm['auth.User'])),
            ('status', self.gf('django.db.models.fields.CharField')(default=u'u', max_length=1)),
        ))
        db.send_create_signal('kiki', ['EmailAddress'])


    def backwards(self, orm):
        
        # Deleting model 'EmailAddress'
        db.delete_table('kiki_emailaddress')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'kiki.emailaddress': {
            'Meta': {'object_name': 'EmailAddress'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "u'u'", 'max_length': '1'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'emails'", 'null': 'True', 'to': "orm['auth.User']"})
        },
        'kiki.mailinglist': {
            'Meta': {'object_name': 'MailingList'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'domain': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'local_part': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'moderator_emails': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'moderated_mailinglist_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['kiki.EmailAddress']"}),
            'moderator_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'moderated_mailinglist_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
            'moderator_users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'moderated_mailinglist_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'self_subscribe_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'subject_prefix': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'subscribed_emails': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'subscribed_mailinglist_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['kiki.EmailAddress']"}),
            'subscribed_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'subscribed_mailinglist_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
            'subscribed_users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'subscribed_mailinglist_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'who_can_post': ('django.db.models.fields.CharField', [], {'max_length': '3'})
        },
        'kiki.message': {
            'Meta': {'object_name': 'Message'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'message_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'received': ('django.db.models.fields.DateTimeField', [], {})
        },
        'kiki.messagemanager': {
            'Meta': {'object_name': 'MessageManager'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'kiki.processingattempt': {
            'Meta': {'object_name': 'ProcessingAttempt'},
            'error': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mailing_list': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['kiki.MailingList']"}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'processing_attempts'", 'to': "orm['kiki.Message']"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'u'", 'max_length': '1', 'db_index': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'sites.site': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['kiki']
