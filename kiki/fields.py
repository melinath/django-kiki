from django.forms.fields import ChoiceField
from django.forms.models import ModelMultipleChoiceField, ModelChoiceIterator
from django.forms.widgets import CheckboxSelectMultiple, CheckboxInput
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from itertools import chain


# is this the way to do it? Or should I make the thing iterable?
class HelpTextCheckboxSelectMultiple(CheckboxSelectMultiple):
	def render(self, name, value, attrs=None, choices=()):
		if value is None: value = []
		has_id = attrs and 'id' in attrs
		final_attrs = self.build_attrs(attrs, name=name)
		output = [u'<ul>']
		# Normalize to strings
		str_values = set([force_unicode(v) for v in value])
		
		for i, (option_value, option_label, option_help_text) in enumerate(chain(self.choices, choices)):
			# If an ID attribute was given, add a numeric index as a suffix,
			# so that the checkboxes don't all have the same ID attribute.
			if has_id:
				final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
				label_for = u' for="%s"' % final_attrs['id']
			else:
				label_for = ''

			cb = CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
			option_value = force_unicode(option_value)
			rendered_cb = cb.render(name, option_value)
			option_label = conditional_escape(force_unicode(option_label))
			output.append(u"<li><label%s>%s %s</label><p class='help'>%s</p></li>" % (label_for, rendered_cb, option_label, option_help_text))
		output.append(u'</ul>')
		return mark_safe(u'\n'.join(output))


class HelpTextModelChoiceIterator(ModelChoiceIterator):
	def choice(self, obj):
		choice = super(HelpTextModelChoiceIterator, self).choice(obj)
		choice += (obj.help_text or '',)
		return choice


class MailingListMultipleChoiceField(ModelMultipleChoiceField):
	def label_from_instance(self, obj):
		return mark_safe('%s &#8212; %s@%s' % (obj.name, obj.address, obj.site))
	
	def _get_choices(self):
		if hasattr(self, '_choices'):
			return self._choices
		
		return HelpTextModelChoiceIterator(self)
	choices = property(_get_choices, ChoiceField._set_choices)
	widget = HelpTextCheckboxSelectMultiple