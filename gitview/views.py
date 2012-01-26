from django.shortcuts import render_to_response,redirect
from django.template import RequestContext
from django.conf import settings
from gitengine.gitEngine import GitRepo,GitGraph, GitDir
import gitengine.gitEngine as gitEngine
from django import forms
from os import sep
import time
import tempfile
from django.http import HttpResponse
from django.core.urlresolvers import reverse

def index(request):
    repos=GitRepo.getRepos(settings.GIT_PATH, True)
    return render_to_response("index.html",{'gitPath':settings.GIT_PATH,'gitBasicUrl':settings.GIT_BASIC_URL,'repos':repos})

class BranchForm(forms.Form):
    def __init__(self,repo,*args,**kwargs):
        super(BranchForm,self).__init__(*args,**kwargs)
        refs = repo.getBranches()
        branches = []
        shas = {}
        try:
            shas[repo.head()]='HEAD'
            for key in refs.keys():
                if key!='HEAD':
                    if refs[key] in shas:
                        shas[refs[key]]=shas[refs[key]]+" - "+key
                    else:
                        shas[refs[key]]=key
                        
            branches.append( (repo.head(),shas[repo.head()]) )
            for sh in shas.keys():
                if sh!=repo.head():
                    branches.append( (sh,shas[sh]) )
            try:
                head=repo.head()
            except KeyError:
                head=''
        except KeyError:
            head=''
        self.fields['branch']=forms.ChoiceField(branches,initial=head);
        self.fields['path']=forms.CharField(initial=repo.path,widget=forms.HiddenInput())

class FilterForm(forms.Form):
    since=forms.DateTimeField(required=False)
    until=forms.DateTimeField(required=False)
    number=forms.IntegerField(initial="10",widget=forms.TextInput(attrs={'size':'5'}))
    page=forms.IntegerField(widget=forms.HiddenInput(),initial=1)

def commits(request):
    reposPath=request.GET['path']
    repo = GitRepo(reposPath)
    until=None
    since=None
    try:
        branch=request.GET['branch']
    except KeyError:
        branch=None
    page=1
    num=10
    numPerPages=15
    if (request.method=='POST'):
        filterForm = FilterForm(request.POST)
        if filterForm.is_valid():
            num=filterForm.cleaned_data['number']
            page=filterForm.cleaned_data['page']
            if filterForm.cleaned_data['since']!=None:
                since=int(time.mktime(filterForm.cleaned_data['since'].timetuple()))
            if filterForm.cleaned_data['until']!=None:
                until=int(time.mktime(filterForm.cleaned_data['until'].timetuple()))
            commits=repo.getCommits(num=num,since=since,until=until,branch=branch)
        else:
            commits=repo.getCommits(num,branch=branch)
    else:
        filterForm = FilterForm()
        commits=repo.getCommits(num,branch=branch)
    #The page number is +1
    page-=1
    if len(commits)>numPerPages:
        numPages=len(commits)/numPerPages
        if len(commits)%numPerPages>0:
            numPages+=1
        commits=commits[numPerPages*page:][:numPerPages]
    else:
        numPages=1
    if branch:
        branchForm=BranchForm(repo,request.GET)
    else:
        branchForm=BranchForm(repo)
    return render_to_response("commits.html",RequestContext(request,{
            'branchForm':branchForm,
            'filterForm':filterForm,
            'repoPath':reposPath,
            'branch':branch,
            'since':since,
            'until':until,
            'commits':commits,
            'num':num,
            'numPages':range(numPages+1)[1:],
            'page':page+1
            }))

def commit(request):
    """ View a single commit"""
    reposPath=request.GET['path']
    commitId=request.GET['id']
    repo = GitRepo(reposPath)
    commit = repo.getCommit(commitId)
    changes=commit.getChanges()
    return render_to_response("commit.html",{'repoPath':reposPath,'commit':commit,'changes':changes})

def compareCommit(request):
    """ Compare two commit"""
    reposPath=request.GET['path']
    commitIds=request.GET.getlist('compareCommitId')
    repo = GitRepo(reposPath)
    commit1=repo.getCommit(commitIds[0])
    commit2=repo.getCommit(commitIds[1])
    if (commit1.commit_time>commit2.commit_time):
        swp=commit1
        commit1=commit2
        commit2=swp
    changes=gitEngine.commitChanges(repo, commit1.id, commit2.id)
    return render_to_response("compareCommit.html",{'repoPath':reposPath,'commit1':commit1,'commit2':commit2,'changes':changes})

def view(request):
    """ View a single file of a commit """
    reposPath=request.GET['path']
    commitId=request.GET['commit']
    filePath=request.GET['filePath']
    repo = GitRepo(reposPath)
    commit = repo.getCommit(commitId)
    fileSha = commit.getTree().getFile(filePath).sha
    return render_to_response("view.html",{'repoPath':reposPath,'commitId':commitId,'fileName':filePath,'fileSha':fileSha})

def fileContent(request):
    reposPath=request.GET['path']
    sha=request.GET['sha']
    filePath=request.GET['filePath']
    repo = GitRepo(reposPath)
    fileContent=str(repo.get_blob(sha))
    return render_to_response("fileContent.html",{'repoPath':reposPath,'sha':sha,'fileName':filePath,'content':fileContent})

def rawContent(request):
    reposPath=request.GET['path']
    sha=request.GET['sha']
    repo = GitRepo(reposPath)
    fileContent=str(repo.get_blob(sha))
    return HttpResponse(fileContent,"text/plain")
    
def dir_to_ul(gitdir,repoPath):
    content="<li><span class=\"folder\">"+gitdir.path.split("/")[-1]+"</span><ul>"
    subdir=gitdir.getSubDirs()
    for sd in subdir:
        content+=dir_to_ul(sd,repoPath)
    files=gitdir.getFiles()
    for fl in files:
        content+="<li><span class=\"file\">"
        content+="<a href='#' onclick=\"showContent('"+fl.sha+"','"+fl.fileName+"') \">"
        content+=fl.fileName.split("/")[-1]+"</a></span></li>"
    content+="</ul></li>"
    return content
        
def tree(request):
    """ View a tree of a commit """
    reposPath=request.GET['path']
    commitId=request.GET['commit']
    repo = GitRepo(reposPath)
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
        treeContent+="<a href='#' onclick=\"showContent('"+f.sha+"','"+f.fileName+"') \">"
        treeContent+=f.fileName.split("/")[-1]+"</a></span></li>"
    return render_to_response("tree.html",{'repoPath':reposPath,'commitId':commitId,'treeContent':treeContent})
    
""" ######################### New Repository ######################"""
class NewReposForm(forms.Form):
    path=forms.CharField()
    description=forms.CharField(widget=forms.Textarea())
    
def new(request):
    """ Add New repository Page
    """
    gitPath=settings.GIT_PATH
    if request.method=='POST':
        newReposForm=NewReposForm(request.POST)
        if newReposForm.is_valid():
            newPath=newReposForm.data['path']
            if newPath[0]=='/':
                newPath=newPath[1:]
            GitRepo.create_bare(settings.GIT_PATH+sep+newPath,newReposForm.data['description'])
            return redirect('gitview.views.index')
    else:
        newReposForm=NewReposForm()
    return render_to_response("new.html",RequestContext(request,{'gitPath':gitPath,'newReposForm':newReposForm}))

def graphImg(request):
    """ Generate a Dynamic Graph Image called by graph method
    """
    repoPath = request.GET['path']
    branch = request.GET['branch']
    since = request.GET['since']
    until = request.GET['until']
    num = request.GET['num']
    repo=GitRepo(repoPath)
 
    graph=GitGraph(repo,branch=branch,size=num,since=since,until=until)
    graph.prepare();
    
    tfile = tempfile.NamedTemporaryFile()
    graph.draw(tfile, 'png')
    tfile.seek(0)
    return HttpResponse(tfile.read(),mimetype="image/png")

""" ################## GRAPH #################### """
def graph(request):
    """ Generate a Page with the graph image and related map
        called by ajax 
    """
    repoPath = request.GET['path']
    branch = request.GET['branch']
    since = request.GET['since']
    until = request.GET['until']
    num = request.GET['num']
    repo=GitRepo(repoPath)
    commitUrl=reverse('gitview.views.commit')
    commitUrl+="?path="+repoPath+"&id=$$"
    mapGraph=GitGraph(repo,branch=branch,size=num,since=since,until=until,commitUrl=str(commitUrl))
    mapGraph.prepare();
    mapTempFile = tempfile.NamedTemporaryFile()
    mapGraph.draw(mapTempFile, 'cmapx')
    mapTempFile.seek(0)
    graphUrl=str(reverse('gitview.views.graphImg'))+"?path="+repoPath+"&branch="+branch+"&since="+str(since)+"&until="+str(until)+"&num="+str(num)
    return render_to_response("graph.html",{'graphUrl':graphUrl,'mapContent':mapTempFile.read()})

    
    