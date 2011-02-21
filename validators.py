from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, email_re
from django.utils.translation import ugettext_lazy as _
import re


pattern = email_re.pattern.split('@')


class EmailNameValidator(RegexValidator):
	regex = re.compile(pattern[0] + '$', re.IGNORECASE)


class EmailDomainValidator(RegexValidator):
	regex = re.compile('^' + pattern[1], re.IGNORECASE)