from os import sep

from django import template


register = template.Library()


@register.filter(name='relpath')
def relpath(fullPath, basePath):
	newPath = fullPath.replace('//', '/').replace(basePath.replace('//', '/'), '')
	if len(newPath) > 0:
		if newPath[0] == '/':
			return newPath[1:]
		else:
			return newPath
	else:
		return ""


@register.filter(name='parent')
def parent(fullPath, basePath):
	subdir = relpath(fullPath, basePath)
	if subdir[-1] == sep:
		subdir = subdir[:-1]
	dir_list = subdir.split(sep)
	if len(dir_list) == 1:
		return ""
	new_dir_list = dir_list[:-1]
	newPath = ""
	for dr in new_dir_list:
		newPath += dr + sep
	return newPath