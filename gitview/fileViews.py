from django.shortcuts import render_to_response
from gitengine.core import GitRepo, GitDir,GitChange
from django.template import RequestContext
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper

import zipfile
import tempfile
from views import getGitPath
from os import sep

def diff(request):
    reposPath=request.GET['path']
    commitId=request.GET['commit']
    oldSha=request.GET['oldSha']
    newSha=request.GET['newSha']
    try:
        request.GET['ghDiff']
        ghDiff=True
    except KeyError:
        ghDiff=False
    repo = GitRepo(getGitPath()+sep+reposPath)
    commit = repo.getCommit(commitId)
    change=GitChange(commit=commit,oldSha=oldSha,newSha=newSha)
    return render_to_response("diff.html",RequestContext(request,{'ghDiff':ghDiff,'change':change}))

def view(request):
    """ View a single file of a commit """
    reposPath=request.GET['path']
    commitId=request.GET['commit']
    filePath=request.GET['filePath']
    try:
        branch=request.GET['branch']
    except KeyError:
        branch=''
    repo = GitRepo(getGitPath()+sep+reposPath)
    commit = repo.getCommit(commitId)
    fileSha = commit.getTree().getFile(filePath).blob.hexsha
    return render_to_response("view.html",RequestContext(request,{'repoPath':reposPath,'commitId':commitId,'fileName':filePath,'fileSha':fileSha,'branch':branch}))

def fileContent(request):
    reposPath=request.GET['path']
    commitId=request.GET['commitId']
    filePath=request.GET['filePath']
    try:
        branch=request.GET['branch']
    except KeyError:
        branch=''
    repo = GitRepo(getGitPath()+sep+reposPath)
    commit = repo.getCommit(commitId)
    gitFile=commit.getTree().getFile(filePath)
    return render_to_response("fileContent.html",RequestContext(request,{'repoPath':reposPath,'commitId':commitId,'gitFile':gitFile,'branch':branch}))

def rawContent(request):
    reposPath=request.GET['path']
    commitId=request.GET['commitId']
    filePath=request.GET['filePath']
    repo = GitRepo(getGitPath()+sep+reposPath)
    commit = repo.getCommit(commitId)
    gitFile=commit.getTree().getFile(filePath)
    response=HttpResponse(gitFile.getContent())
    response._headers['content-disposition'] = ('Content-Disposition', 'attachment; filename='+gitFile.blob.name)
    return response

def dirFiles(gitdir,files):
    subdir=gitdir.getSubDirs()
    for sd in subdir:
        dirFiles(sd,files)
    contentFiles=gitdir.getFiles()
    for fl in contentFiles:
        files.append(fl)

def zipTree(request):
    """ zip a tree of a commit """
    reposPath=request.GET['path']
    commitId=request.GET['commit']
    repo = GitRepo(getGitPath()+sep+reposPath)
    commit = repo.getCommit(commitId)
    tree=commit.getTree()
    content=tree.getRoot()
    rootFiles=[]
    for c in content:
        if isinstance(c, GitDir):
            dirFiles(c,rootFiles)
        else:
            rootFiles.append(c)
    temp = tempfile.TemporaryFile()
    archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
    for f in rootFiles:
        archive.writestr(f.blob.path,f.getContent())
    archive.close()
    wrapper = FileWrapper(temp)
    response = HttpResponse(wrapper, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename='+reposPath.replace('/','_').replace(".git","")+".zip"
    response['Content-Length'] = temp.tell()
    temp.seek(0)
    return response


def dir_to_ul(gitdir,repoPath):
    content="<li><span class=\"folder\">"+gitdir.tree.path.split("/")[-1]+"</span><ul>"
    subdir=gitdir.getSubDirs()
    for sd in subdir:
        content+=dir_to_ul(sd,repoPath)
    files=gitdir.getFiles()
    for fl in files:
        content+="<li><span class=\"file\">"
        content+="<a href='#' onclick=\"showContent('"+fl.blob.path+"') \">"
        content+=fl.blob.name+"</a></span></li>"
    content+="</ul></li>"
    return content

def tree(request):
    """ View a tree of a commit """
    reposPath=request.GET['path']
    commitId=request.GET['commit']
    try:
        branch=request.GET['branch']
    except KeyError:
        branch=''
    repo = GitRepo(getGitPath()+sep+reposPath)
    commit = repo.getCommit(commitId)
    tree=commit.getTree()
    content=tree.getRoot()
    treeContent=""
    rootFiles=[]
    for c in content:
        if isinstance(c, GitDir):
            treeContent+=dir_to_ul(c,reposPath)
        else:
            rootFiles.append(c)
    #add files at the end
    for f in rootFiles:
        treeContent+="<li><span class=\"file\">"
        treeContent+="<a href='#' onclick=\"showContent('"+f.blob.path+"') \">"
        treeContent+=f.blob.name+"</a></span></li>"
    return render_to_response("tree.html",RequestContext(request,{'repoPath':reposPath,'commitId':commitId,'treeContent':treeContent,'branch':branch}))
