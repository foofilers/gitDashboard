import os
from base64 import b64decode

import settings


def checkRepoAuthorization(request, reposPath=None):
	if settings.GITOLITE_EXEC_PATH is None or settings.GITOLITE_EXEC_PATH == "":
		return True
	try:
		auth_header = request.META['HTTP_AUTHORIZATION'].replace("Basic ", "")
		decoded = b64decode(auth_header)
		user = decoded[0:decoded.index(':')]
		if reposPath is None:
			reposPath = request.GET['path'].replace("//", "/")
		if settings.GITOLITE_HOME is None or settings.GITOLITE_HOME == "":
			gitolite_home = os.environ['HOME']
		else:
			gitolite_home = settings.GITOLITE_HOME
		cmd = "export HOME=" + gitolite_home + ";" + settings.GITOLITE_EXEC_PATH + " access -q " + reposPath + " "+user

		if os.system(cmd) != 0:
			return False
	except:
		return False
	return True