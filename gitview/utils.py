import os

import settings


def checkRepoAuthorization(request, reposPath=None):
	if settings.GITOLITE_EXEC_PATH is None or settings.GITOLITE_EXEC_PATH == "":
		return True
	try:
		user = request.META['REMOTE_USER']
		if reposPath is None:
			reposPath = request.GET['path'].replace("//", "/")
		reposPath = reposPath[:reposPath.rindex('.git')]
		if settings.GITOLITE_HOME is None or settings.GITOLITE_HOME == "":
			gitolite_home = os.environ['HOME']
		else:
			gitolite_home = settings.GITOLITE_HOME
		cmd = "export HOME=" + gitolite_home + ";" + settings.GITOLITE_EXEC_PATH + " access -q " + reposPath + " "+user
		if os.system(cmd) != 0:
			return False
	except Exception as e:
		print e
		return False
	return True