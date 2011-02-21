from django.core.mail import send_mail


def subscribe(email, mailing_list):
	mailing_list.subscribe(email)
	send_mail("Subscription successful", """You've been subscribed to %s! You can
unsubscribe at any time by sending an email to %s-unsubscribe@%s""" %
(mailing_list.name, mailing_list.address, mailing_list.site.domain),
"noreply@%s" % mailing_list.site.domain, [email])


def unsubscribe(email, mailing_list):
	mailing_list.unsubscribe(email)
	send_mail("Unsubscription successful", """You've been unsubscribed from %s. You can
resubscribe at any time by sending an email to %s-subscribe@%s""" %
(mailing_list.name, mailing_list.address, mailing_list.site.domain),
"noreply@%s" % mailing_list.site.domain, [email])


def bounce(email, mailing_list):
	pass


COMMANDS = {
	'subscribe': subscribe,
	'bounce': bounce,
	'unsubscribe': unsubscribe,
}


def run_command(command, email, mailing_list):
	COMMANDS[command](email, mailing_list)