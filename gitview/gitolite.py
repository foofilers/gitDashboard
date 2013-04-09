from os import listdir
from os.path import isdir, sep

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.conf import settings
from django.contrib.auth.decorators import login_required

from gitengine.gitolite import GitoliteAdmin, PushException


def dir_to_ul(dirName, repoPath):
	content = "<li><span class=\"folder\">" + dirName.split("/")[-1] + "</span><ul>"
	for sd in sorted(listdir(repoPath + sep + dirName)):
		fullPath = repoPath + sep + dirName + sep + sd
		fullPath = fullPath.replace('//', '/')
		if isdir(fullPath):
			content += dir_to_ul(dirName + sep + sd, repoPath)
		else:
			content += "<li><span class=\"file\">"
			content += "<a href='#' onclick=\"showContent('" + dirName + sep + sd + "') \">"
			content += sd + "</a></span></li>"
	content += "</ul></li>"
	return content


@login_required(login_url='login')
def index(request):
	if not request.user.is_staff:
		return render_to_response("notAlowed.html", RequestContext(request))
	admin = GitoliteAdmin(settings.GITOLITE_PATH, settings.GITOLITE_URL)
	feedback = ""
	fbcolor = 'green'
	filePath = None
	popupMessage = None
	if request.method == "POST":
		action = request.POST['action']
		if action.lower() == 'newfile':
			newFilePath = request.POST['newFilePath']
			if newFilePath == '':
				feedback = 'Error filePath cannot be empty'
				fbcolor = 'red'
			else:
				admin.save(newFilePath, "")
				feedback = "File " + newFilePath + " added"

		if action.lower() == 'delete':
			delFilePath = request.POST['delFilePath']
			if delFilePath == 'conf/gitolite.conf':
				feedback = "Error: cannot delete gitolite.conf it's the main gitolite file"
				fbcolor = 'red'
			else:
				admin.remove(delFilePath)
				feedback = "File " + delFilePath + " deleted"

		if action.lower() == "save" != -1:
			content = request.POST['content']
			filePath = request.POST['filePath']
			admin.save(filePath, content)
			feedback = "Saved"

		if action.lower() == "push" != -1:
			message = request.POST['message']
			if message == '':
				feedback = 'Error message cannot be empty'
				fbcolor = 'red'
			else:
				try:
					pm = admin.push(message)
					feedback = 'Pushed'
					popupMessage = pm
				except PushException as pe:
					popupMessage = pe.message
					feedback = 'Error: PUSH FAILED'
					fbcolor = 'red'

		if action.lower().find("reset") != -1:
			admin.resetHard()
			feedback += "Reset Complete"
	else:
		admin.pull()
	treeContent = ""
	rootFiles = []
	wkDir = admin.working_dir
	for c in sorted(listdir(wkDir)):
		if c != '.git':
			fullPath = wkDir + sep + c
			fullPath = fullPath.replace('//', '/')
			if isdir(fullPath):
				treeContent += dir_to_ul(c, settings.GITOLITE_PATH)
			else:
				rootFiles.append(c)
		#add files at the end
	for f in rootFiles:
		treeContent += "<li><span class=\"file\">"
		treeContent += "<a href='#' onclick=\"showContent('" + f + "') \">"
		treeContent += f + "</a></span></li>"
	return render_to_response("gitolite.html", RequestContext(request, {'repo': admin, 'treeContent': treeContent,
	                                                                    'filePath': filePath, 'fbcolor': fbcolor,
	                                                                    'feedback': feedback,
	                                                                    'popupMessage': popupMessage}))


@login_required(login_url='login')
def fileContent(request):
	if not request.user.is_staff:
		return render_to_response("notAlowed.html", RequestContext(request))
	filePath = request.GET['filePath']
	admin = GitoliteAdmin(settings.GITOLITE_PATH, settings.GITOLITE_URL)
	content = admin.getWkFileContent(filePath)
	return render_to_response("gitoliteFile.html", RequestContext(request, {'content': content}))