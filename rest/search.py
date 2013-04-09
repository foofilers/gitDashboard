import logging
import os

from rest_framework.decorators import api_view
from rest_framework.response import Response

from gitview.views import getGitPath


log = logging.getLogger("gitDashboard")


def __recSearch(dir, search):
	contentDir = os.listdir(dir)
	res = []
	log.debug("search repos on directory " + dir + "with search:" + search)
	for cnt in contentDir:
		if os.path.isdir(dir + os.path.sep + cnt):
			if cnt.lower().find('.git') > 0 or os.path.exists(dir + os.path.sep + cnt + os.path.sep + ".git"):
				if cnt.lower().find(search.lower()) > -1:
					# git repos
					res.append(dir + os.path.sep + cnt)
			else:
				if cnt.lower() != '.git':
					res += __recSearch(dir + os.path.sep + cnt, search)
	return res


@api_view(['GET'])
def searchRepos(request):
	srcQuery = request.GET['search']
	basePath = getGitPath()
	autoCompleteJson = []
	for path in __recSearch(basePath, srcQuery):
		autoCompleteJson.append({'repo': path.replace(os.path.sep + os.path.sep, os.path.sep).replace(basePath, '')})
	return Response(autoCompleteJson)