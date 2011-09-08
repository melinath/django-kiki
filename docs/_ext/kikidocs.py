from celery.app.task import BaseTask
from sphinx.ext import autodoc


class TaskDocumenter(autodoc.DataDocumenter):
	@classmethod
	def can_document_member(cls, member, membername, isattr, parent):
		if isinstance(member, BaseTask):
			return True


def setup(app):
	app.add_autodocumenter(TaskDocumenter)
