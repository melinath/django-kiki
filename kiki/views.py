from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import loader, RequestContext
from kiki.forms import SubscriptionForm


def subscription_view(request, template="kiki/subscription.html", form_class=SubscriptionForm):
	if request.method == 'POST':
		form = form_class(request.POST)
		if form.is_valid():
			form.save()
			return HttpResponseRedirect('')
	elif request.GET:
		form = form_class(request.GET)
	else:
		form = form_class()
	
	context = {
		'form': form,
	}
	return render_to_response(template, context, context_instance=RequestContext(request))


def subscription_confirmation_view(request):
	# what arguments are needed?
	pass