import hashlib

from django import template


register = template.Library()


@register.filter(name='gravatarImageUrl')
def gravatarImageUrl(email, size):
	md5 = hashlib.md5()
	md5.update(email)
	md5Email = md5.hexdigest()
	return "http://www.gravatar.com/avatar/" + md5Email + "?d=mm&s=" + str(size)

