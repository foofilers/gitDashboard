from django import template
register = template.Library()

@register.filter(name='relpath')
def relpath(fullPath,basePath):
    return fullPath.replace('//','/').replace(basePath,'')
