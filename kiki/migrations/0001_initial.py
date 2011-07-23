# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'MailingList'
        db.create_table('kiki_mailinglist', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('subject_prefix', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('local_part', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('domain', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sites.Site'])),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('who_can_post', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('self_subscribe_enabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('kiki', ['MailingList'])

        # Adding M2M table for field subscribed_users on 'MailingList'
        db.create_table('kiki_mailinglist_subscribed_users', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('mailinglist', models.ForeignKey(orm['kiki.mailinglist'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('kiki_mailinglist_subscribed_users', ['mailinglist_id', 'user_id'])

        # Adding M2M table for field subscribed_groups on 'MailingList'
        db.create_table('kiki_mailinglist_subscribed_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('mailinglist', models.ForeignKey(orm['kiki.mailinglist'], null=False)),
            ('group', models.ForeignKey(orm['auth.group'], null=False))
        ))
        db.create_unique('kiki_mailinglist_subscribed_groups', ['mailinglist_id', 'group_id'])

        # Adding M2M table for field subscribed_emails on 'MailingList'
        db.create_table('kiki_mailinglist_subscribed_emails', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('mailinglist', models.ForeignKey(orm['kiki.mailinglist'], null=False)),
            ('emailaddress', models.ForeignKey(orm['mail.emailaddress'], null=False))
        ))
        db.create_unique('kiki_mailinglist_subscribed_emails', ['mailinglist_id', 'emailaddress_id'])

        # Adding M2M table for field moderator_users on 'MailingList'
        db.create_table('kiki_mailinglist_moderator_users', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('mailinglist', models.ForeignKey(orm['kiki.mailinglist'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('kiki_mailinglist_moderator_users', ['mailinglist_id', 'user_id'])

        # Adding M2M table for field moderator_groups on 'MailingList'
        db.create_table('kiki_mailinglist_moderator_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('mailinglist', models.ForeignKey(orm['kiki.mailinglist'], null=False)),
            ('group', models.ForeignKey(orm['auth.group'], null=False))
        ))
        db.create_unique('kiki_mailinglist_moderator_groups', ['mailinglist_id', 'group_id'])

        # Adding M2M table for field moderator_emails on 'MailingList'
        db.create_table('kiki_mailinglist_moderator_emails', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('mailinglist', models.ForeignKey(orm['kiki.mailinglist'], null=False)),
            ('emailaddress', models.ForeignKey(orm['mail.emailaddress'], null=False))
        ))
        db.create_unique('kiki_mailinglist_moderator_emails', ['mailinglist_id', 'emailaddress_id'])

        # Adding model 'MessageManager'
        db.create_table('kiki_messagemanager', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('kiki', ['MessageManager'])

        # Adding model 'Message'
        db.create_table('kiki_message', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('message_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('received', self.gf('django.db.models.fields.DateTimeField')()),
            ('message', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('kiki', ['Message'])

        # Adding model 'ProcessingAttempt'
        db.create_table('kiki_processingattempt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='u', max_length=1, db_index=True)),
            ('error', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('mailing_list', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['kiki.MailingList'])),
            ('message', self.gf('django.db.models.fields.related.ForeignKey')(related_name='processing_attempts', to=orm['kiki.Message'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('kiki', ['ProcessingAttempt'])


    def backwards(self, orm):
        
        # Deleting model 'MailingList'
        db.delete_table('kiki_mailinglist')

        # Removing M2M table for field subscribed_users on 'MailingList'
        db.delete_table('kiki_mailinglist_subscribed_users')

        # Removing M2M table for field subscribed_groups on 'MailingList'
        db.delete_table('kiki_mailinglist_subscribed_groups')

        # Removing M2M table for field subscribed_emails on 'MailingList'
        db.delete_table('kiki_mailinglist_subscribed_emails')

        # Removing M2M table for field moderator_users on 'MailingList'
        db.delete_table('kiki_mailinglist_moderator_users')

        # Removing M2M table for field moderator_groups on 'MailingList'
        db.delete_table('kiki_mailinglist_moderator_groups')

        # Removing M2M table for field moderator_emails on 'MailingList'
        db.delete_table('kiki_mailinglist_moderator_emails')

        # Deleting model 'MessageManager'
        db.delete_table('kiki_messagemanager')

        # Deleting model 'Message'
        db.delete_table('kiki_message')

        # Deleting model 'ProcessingAttempt'
        db.delete_table('kiki_processingattempt')


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
        'kiki.mailinglist': {
            'Meta': {'object_name': 'MailingList'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'domain': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'local_part': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'moderator_emails': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'moderated_mailinglist_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['mail.EmailAddress']"}),
            'moderator_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'moderated_mailinglist_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
            'moderator_users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'moderated_mailinglist_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'self_subscribe_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'subject_prefix': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'subscribed_emails': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'subscribed_mailinglist_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['mail.EmailAddress']"}),
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
        'mail.emailaddress': {
            'Meta': {'object_name': 'EmailAddress'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "u'u'", 'max_length': '1'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'emails'", 'null': 'True', 'to': "orm['auth.User']"})
        },
        'sites.site': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['kiki']
