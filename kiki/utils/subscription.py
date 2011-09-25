from hashlib import sha1

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import int_to_base36, base36_to_int


class SubscriptionTokenGenerator(PasswordResetTokenGenerator):
	"""
	Strategy object used to generate and check tokens for the subscription
	mechanism.
	
	"""
	def check_token(self, metadata, token, timeout_days=1):
		"""
		Check that a registration token is correct for a given :class:`ListUserMetadata`.
		
		"""
		# If the email is already subscribed, the hash isn't be valid.
		if metadata.status == metadata.SUBSCRIBED:
			return False
		
		# Parse the token
		try:
			ts_b36, hash = token.split('-')
		except ValueError:
			return False
		
		try:
			ts = base36_to_int(ts_b36)
		except ValueError:
			return False
		
		# Check that the timestamp and uid have not been tampered with.
		if self._make_token_with_timestamp(metadata, ts) != token:
			return False
		
		# Check that the timestamp is within limit
		if (self._num_days(self._today()) - ts) > timeout_days > 0:
			return False
		
		return True
	
	def _make_token_with_timestamp(self, metadata, timestamp):
		ts_b36 = int_to_base36(timestamp)
		
		# By hashing on the subscribed state of the email and using state that
		# is sure to change, we produce a hash that will be invalid as soon as
		# it is used.
		hash = sha1(settings.SECRET_KEY + unicode(metadata.user_id) + unicode(metadata.status) + unicode(metadata.mailing_list_id) + unicode(timestamp)).hexdigest()[::2]
		return '%s-%s' % (ts_b36, hash)


token_generator = SubscriptionTokenGenerator()
