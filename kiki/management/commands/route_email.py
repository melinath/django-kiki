from django.core.management.base import BaseCommand, CommandError
from stepping_out.mail.mail import route_email
from sys import stdin
from cStringIO import StringIO

class Command(BaseCommand):
    help = 'Routes an email from stdin to a mailing list'
    
    def handle(self, *args, **options):
        if __name__ == '__main__':
            route_email()
        else:
            fp = StringIO()
            fp.write(stdin.read())
            route_email(fp)
