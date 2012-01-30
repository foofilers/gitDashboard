from django import template
from django.core.urlresolvers import reverse
from django.conf import settings
register = template.Library()

@register.filter(name='relpath')
def relpath(fullPath,basePath):
    newPath= fullPath.replace('//','/').replace(basePath,'')
    if newPath[0]=='/':
        return newPath[1:]
    else:
        return newPath
