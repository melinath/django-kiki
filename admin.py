from django.contrib import admin
from django import forms
from models import MailingList, UserEmail


COLLAPSE_OPEN_CLASSES = ('collapse', 'open', 'collapse-open',)


class UserEmailInline(admin.TabularInline):
	model = UserEmail
	extra = 1
	verbose_name = 'email address'
	verbose_name_plural = 'email addresses'


class MailingListAdmin(admin.ModelAdmin):
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
    filter_horizontal = (
        'subscribed_users',
        'subscribed_groups',
        'subscribed_officer_positions',
        'subscribed_emails',
        'moderator_users',
        'moderator_groups',
        'moderator_officer_positions',
        'moderator_emails',
    )
    fieldsets = (
        (None, {
            'fields' : (
                'name',
                ('address',
                'site',)
            )
        }),
        ('Options', {
            'fields' : (
                'who_can_post',
                'self_subscribe_enabled',
                'help_text'
            )
        }),
        ('Subscribers', {
            'fields' : (
                'subscribed_users',
                'subscribed_groups',
                'subscribed_officer_positions',
                'subscribed_emails',
            ),
            'classes': COLLAPSE_OPEN_CLASSES
        }),
        ('Moderators', {
            'fields' : (
                'moderator_users',
                'moderator_groups',
                'moderator_officer_positions',
                'moderator_emails',
            ),
            'classes': COLLAPSE_OPEN_CLASSES
        })
    )
    radio_fields = {'who_can_post':admin.VERTICAL}
    prepopulated_fields = {'address': ('name',)}


class UserEmailAdmin(admin.ModelAdmin):
	search_fields = ['email']


"""
class MailingListInline(admin.TabularInline):
    model = MailingList
    filter_horizontal = ['mailing_lists']

USER_INLINES = [MailingListInline,]
GROUP_INLINES = [MailingListInline,]
"""
admin.site.register(MailingList, MailingListAdmin)
admin.site.register(UserEmail, UserEmailAdmin)