from django.conf.urls.defaults import url, patterns

from kiki.views import SubscriptionView, SubscriptionConfirmationView


urlpatterns = patterns('',
	url(r'^$', SubscriptionView.as_view(), name='kiki_subscription'),
	url(r'^confirm/(?P<midb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})$', SubscriptionConfirmationView.as_view(), name='kiki_subscription_confirm')
)
