from django.conf import settings
from django import template

register = template.Library()
import re


@register.filter(name='issueLink')
def issueLink(message):
	try:
		pattern = settings.MESSAGE_ID_PATTERN.replace("%ID%", '([0-9]*)')
		link = settings.ISSUE_URL
		gr = re.search(pattern, message)
		link = link.replace('%ID%', gr.group(1))
		return '<a href="' + link + '">' + message + '</a>'
	except AttributeError:
		return message

    

