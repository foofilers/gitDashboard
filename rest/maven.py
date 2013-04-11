import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from pomparser.core import PomParser, ArtifactParserException
from django.conf import settings

log = logging.getLogger('gitDashboard')


def jsonMavenDep(art, children, scope='all'):
	try:
		for dep in art.dependencies[scope]:
			data = {}
			name = str(dep)
			if scope == 'all':
				if dep.scope:
					name += " [" + dep.scope + "]"
			data['data'] = name
			data['children'] = []
			children.append(data)
			jsonMavenDep(dep, data['children'], scope)
	except KeyError:
		#no depends for this scope
		pass


@api_view(['GET'])
def dependencies(request):
	res = {}
	groupId = request.GET['groupId']
	artifactId = request.GET['artifactId']
	version = request.GET['version']

	parser = PomParser(settings.MAVEN_RELEASES_URLS,settings.MAVEN_SNAPSHOTS_URLS)
	recursive = False
	scope = 'compile'
	if request.GET['recursive'] == 'true':
		recursive = True
	if request.GET['scope']:
		scope = request.GET['scope']

	try:
		art = parser.parsePom(groupId, artifactId, version, recursive)
		res["data"] = str(art)
		attr = dict()
		attr['id'] = "dep_me"
		res["attr"] = attr
		res["children"] = []
		jsonMavenDep(art, res["children"], scope)
		return Response(res)
	except ArtifactParserException, e:
		res["data"] = e.message
		return Response(res)