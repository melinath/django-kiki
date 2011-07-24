from django.contrib import admin
from django import forms
from models import MailingList, ListUserMetadata, Message, ListMessage


COLLAPSE_OPEN_CLASSES = ('collapse', 'open', 'collapse-open',)


class ListUserMetadataInline(admin.TabularInline):
	model = ListUserMetadata
	raw_id_fields = ['user']
	radio_fields = {'status': admin.VERTICAL}
	extra=0


class ListUserMetadataAdmin(admin.ModelAdmin):
	raw_id_fields = ['user']
	search_fields = ['user__email']
	list_filter = ['status', 'mailing_list']
	radio_fields = {'status': admin.VERTICAL}


class MailingListForm(forms.ModelForm):
	domain = MailingList._meta.get_field('domain').formfield(label="@")
	
	class Meta:
		model = MailingList


class MailingListAdmin(admin.ModelAdmin):
	form = MailingListForm
	list_display = (
		'name',
		'address',
		'who_can_post',
		'self_subscribe_enabled'
	)
	list_filter = list_editable = (
		'who_can_post',
		'self_subscribe_enabled'
	)
	fieldsets = (
		(None, {
			'fields' : (
				'name',
				('local_part',
				'domain',),
				'description',
			)
		}),
		('Options', {
			'fields' : (
				'who_can_post',
				'self_subscribe_enabled',
				'subject_prefix',
				'moderation_enabled',
			)
		}),
	)
	radio_fields = {'who_can_post': admin.VERTICAL}
	prepopulated_fields = {'local_part': ('name',)}
	inlines = [ListUserMetadataInline]


class ListMessageInline(admin.StackedInline):
	model = ListMessage
	extra = 0
	radio_fields = {'status': admin.VERTICAL}
	fields = ('message', 'mailing_list', 'status',)
	raw_id_fields = ('message', 'mailing_list')


class MessageAdmin(admin.ModelAdmin):
	search_fields = ('from_email',)
	inlines = [ListMessageInline]
	fields = ('message_id', 'from_email', 'received', 'status', 'original_message')
	radio_fields = {'status': admin.VERTICAL}


admin.site.register(MailingList, MailingListAdmin)
admin.site.register(ListUserMetadata, ListUserMetadataAdmin)
admin.site.register(Message, MessageAdmin)