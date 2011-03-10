from django.contrib import admin
from django import forms
from models import MailingList, EmailAddress, ListEmailMetadata


COLLAPSE_OPEN_CLASSES = ('collapse', 'open', 'collapse-open',)


class ListEmailMetadataInline(admin.TabularInline):
	model = ListEmailMetadata
	raw_id_fields = ['email']
	radio_fields = {'status': admin.VERTICAL}


class ListEmailMetadataAdmin(admin.ModelAdmin):
	raw_id_fields = ['email']
	search_fields = ['email__email']
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
			)
		}),
	)
	radio_fields = {'who_can_post': admin.VERTICAL}
	prepopulated_fields = {'local_part': ('name',)}
	inlines = [ListEmailMetadataInline]


class EmailAddressAdmin(admin.ModelAdmin):
	search_fields = ['email']
	radio_fields = {'status': admin.VERTICAL}


"""
class MailingListInline(admin.TabularInline):
	model = MailingList
	filter_horizontal = ['mailing_lists']

USER_INLINES = [MailingListInline,]
GROUP_INLINES = [MailingListInline,]
"""
admin.site.register(MailingList, MailingListAdmin)
admin.site.register(EmailAddress, EmailAddressAdmin)
admin.site.register(ListEmailMetadata, ListEmailMetadataAdmin)