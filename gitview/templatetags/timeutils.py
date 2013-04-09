from django import template

register = template.Library()
from datetime import datetime


@register.filter(name='timestamp')
def timestamp(timestamp, timeFormat):
	dt = datetime.fromtimestamp(timestamp)
	return dt.strftime(timeFormat)