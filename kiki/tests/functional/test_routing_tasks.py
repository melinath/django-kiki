from kiki.tasks import receive_email_task, create_message_commands_task, list_post_task, send_list_message_task
from kiki.utils.test import create_test_email


class RoutingTestCase(TestCase):
	fixtures = ['test_data.json']
	
	def test_receive_email_task(self):
		mail.outbox = []
		result = receive_email_task.delay(create_test_email("unused@unused.com", ["hello-world@example.com"]))
		result.get()
		self.assertEqual(len(mail.outbox), 1)
	
	def test_create_message_commands_task(self):
		mail.outbox = []
		result = create_message_commands_task.delay(3)
		time.sleep(1)
		self.assertEqual(len(mail.outbox), 1)
	
	def test_list_post_task(self):
		mail.outbox = []
		result = list_post_task.delay(2)
		time.sleep(1)
		self.assertEqual(len(mail.outbox), 1)
	
	def test_send_list_message_task(self):
		mail.outbox = []
		list_msg = ListMessage.objects.get(pk=1)
		prep_list_message(list_msg)
		result = send_list_message_task.delay(1, 1)
		time.sleep(1)
		self.assertEqual(len(mail.outbox), 1)
