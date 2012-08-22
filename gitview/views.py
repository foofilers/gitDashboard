from django.shortcuts import render_to_response,redirect
from django.template import RequestContext
from django.conf import settings
from gitengine.core import GitRepo
from gitengine.graph import  GitGraphCanvas
import gitengine.core as gitEngine
from django import forms
from os import sep,listdir
from os.path import isdir
import time
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
import re
from issue import Mantis1_7IssuePane,NoIssueFoundException

def getGitPath():
    if settings.GIT_PATH[-1]=='/':
        gitPath=settings.GIT_PATH
    else:
        gitPath=settings.GIT_PATH+"/"
    return gitPath

def index(request):
    gitPath=getGitPath()
    try:
        pathpar=request.GET['path']
    except KeyError:
        pathpar=""
    currPath=getGitPath()+pathpar
    subDirs=[]
    contents = listdir(currPath)
    for content in contents:
        fullPath=currPath+sep+content
        if isdir(fullPath):
            if not isdir(fullPath+sep+".git") and not isdir(fullPath+sep+"refs") :
                toAdd=True
                for excl in settings.GIT_EXCLUDE_PATH:
                    if re.match(excl, content):
                        toAdd=False
                if toAdd:
                    subDirs.append(content)
    subDirs=sorted(subDirs)
    repos=GitRepo.getRepos(currPath, False,settings.GIT_EXCLUDE_PATH)
    return render_to_response("index.html",RequestContext(request,{'gitPath':gitPath,'currPath':currPath,'gitBasicUrl':settings.GIT_BASIC_URL,'subDirs':subDirs,'repos':repos}))

def sortBranch (curr,nxt):
    if (curr.find('tag')>-1):
        if (nxt.find('tag')):
            return cmp(curr,nxt)
        else:
            return 1
    else:
        if (nxt.find('tag')):
            return -1
        else:
            return cmp(curr,nxt)

class BranchForm(forms.Form):
    def __init__(self,repo,*args,**kwargs):
        super(BranchForm,self).__init__(*args,**kwargs)
        refs = repo.getBranches()
        refs.update(repo.getTagsRef())
        branches = []
        shas = {}
        try:
            shas[repo.head.commit.hexsha]='HEAD'
            keys = refs.keys()
            for key in keys:
                if key!='HEAD':
                    if refs[key] in shas:
                        shas[refs[key]]=shas[refs[key]]+" - "+key
                    else:
                        shas[refs[key]]=key
            branches.append( (repo.head.commit.hexsha,shas[repo.head.commit.hexsha]) )
            nameBranches={}
            for sh in shas.keys():
                nameBranches[shas[sh]]=sh
            sortedNameBranches = nameBranches.keys()
            sortedNameBranches.sort()
            for br in sortedNameBranches:
                if nameBranches[br]!=repo.head.commit.hexsha:
                    branches.append( (nameBranches[br],br) )
            try:
                head=repo.head.commit.hexsha
            except KeyError:
                head=''
        except KeyError:
            head=''
        self.fields['branch']=forms.ChoiceField(branches,initial=head,widget=forms.Select(attrs={'class':'ui-corner-all'}));
        self.fields['path']=forms.CharField(initial=repo.path,widget=forms.HiddenInput())

class FilterForm(forms.Form):
    since=forms.DateTimeField(required=False,widget=forms.DateInput(attrs={'class':'ui-corner-all'}))
    until=forms.DateTimeField(required=False,widget=forms.DateInput(attrs={'class':'ui-corner-all'}))
    number=forms.IntegerField(initial="10",widget=forms.TextInput(attrs={'size':'5','class':'ui-corner-all'}))
    page=forms.IntegerField(widget=forms.HiddenInput(),initial=1)

def commits(request):
    reposPath=request.GET['path'].replace("//","/")
    repo = GitRepo(getGitPath()+sep+reposPath)
    until=None
    since=None
    try:
        branch=request.GET['branch']
        if branch=='':
            branch=repo.head.commit.hexsha
    except KeyError:
        branch=repo.head.commit.hexsha
    try:
        filePath=request.GET['filePath']
    except KeyError:
        filePath=None
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
            commits=repo.getCommits(num=num,since=since,until=until,branch=branch,path=filePath)
        else:
            commits=repo.getCommits(num,branch=branch,path=filePath)
    else:
        filterForm = FilterForm()
        commits=repo.getCommits(num,branch=branch,path=filePath)
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
    
    repoName=reposPath.split('/')[-1]
    if reposPath.rfind('/')>0:
        moduleName=reposPath[:reposPath.rfind('/')]
    else:
        moduleName=''
    return render_to_response("commits.html",RequestContext(request,{
            'branchForm':branchForm,
            'filterForm':filterForm,
            'repoPath':reposPath,
            'moduleName':moduleName,
            'repoName':repoName,
            'branch':branch,
            'since':since,
            'until':until,
            'commits':commits,
            'num':num,
            'numPages':range(numPages+1)[1:],
            'page':page+1,
            'filePath':filePath,
            'gitPath':getGitPath(),
            'gitBasicUrl':settings.GIT_BASIC_URL
            }))

def commit(request):
    """ View a single commit"""
    reposPath=request.GET['path']
    commitId=request.GET['id']
    try:
        branch=request.GET['branch']
    except KeyError:
        branch=''
    repo = GitRepo(getGitPath()+sep+reposPath)
    commit = repo.getCommit(commitId)
    changes=commit.getChanges()
    
    issueSystem=settings.ISSUE_SYSTEM
    try:
        if issueSystem.lower()=='mantis_1.7':
            issuePanelContent = Mantis1_7IssuePane(commit.commit.message,settings.MESSAGE_ID_PATTERN,settings.ISSUE_WSDL,settings.ISSUE_URL,settings.ISSUE_USERNAME,settings.ISSUE_PASSWORD).renderHtml()
    except AttributeError:
        issueSystem=""
        issuePanelContent=""
    except NoIssueFoundException:
        issueSystem=""
        issuePanelContent=""
    
    
    return render_to_response("commit.html",RequestContext(request,{'gitPath':getGitPath(),'repoPath':reposPath,'commit':commit,'changes':changes,'branch':branch,'issueSystem':issueSystem,'issuePanelContent':issuePanelContent}))

def compareCommit(request):
    """ Compare two commit"""
    reposPath=request.GET['path']
    commitIds=request.GET.getlist('compareCommitId')
    repo = GitRepo(getGitPath()+sep+reposPath)
    commit1=repo.getCommit(commitIds[0])
    commit2=repo.getCommit(commitIds[1])
    if (commit1.commit.committed_date>commit2.commit.committed_date):
        swp=commit1
        commit1=commit2
        commit2=swp
    changes=gitEngine.commitChanges(repo, commit1.commit.hexsha, commit2.commit.hexsha)
    return render_to_response("compareCommit.html",RequestContext(request,{'repoPath':reposPath,'commit1':commit1,'commit2':commit2,'changes':changes}))

    
""" ######################### New Repository ######################"""
class NewReposForm(forms.Form):
    path=forms.CharField()
    description=forms.CharField(widget=forms.Textarea())

@login_required(login_url='login')
def new(request):
    """ Add New repository Page
    """
    if not request.user.is_staff:
        return render_to_response("notAlowed.html",RequestContext(request))
    try:
        if settings.SECURITY_SYSTEM.lower()=='gitolite':
            return redirect('gitview.gitolite.index')
    except AttributeError:
        pass 
    if request.method=='POST':
        newReposForm=NewReposForm(request.POST)
        if newReposForm.is_valid():
            newPath=newReposForm.data['path']
            if newPath[0]=='/':
                newPath=newPath[1:]
            GitRepo.create_bare(getGitPath()+sep+newPath,newReposForm.data['description'])
            return redirect('gitview.views.index')
    else:
        newReposForm=NewReposForm()
    return render_to_response("new.html",RequestContext(request,{'gitPath':getGitPath(),'newReposForm':newReposForm}))

""" ################## GRAPH #################### """
def graph(request):
    """ Generate a Page with the graph image and related map
        called by ajax 
    """
    repoPath = request.GET['path']
    try:
        branch=request.GET['branch']
    except KeyError:
        branch=''
    
    if len(request.GET['since'])>0:
        try:
            since= int(request.GET['since'])
        except ValueError:
            since=int(time.mktime(time.strptime(request.GET['since'],"%Y-%m-%d %H:%M")))
    else:
        since=None
        
    if len(request.GET['until'])>0:
        try:
            until=int(request.GET['until'])
        except ValueError:
            until=int(time.mktime(time.strptime(request.GET['until'],"%Y-%m-%d %H:%M")))
    else:
        until=None
    try:
        cmtId=request.GET['id']
        highlights="highlightsCircle(stage,circlesLayer,circle_"+cmtId+",width);"
    except KeyError:
        highlights=None;
    
    repo=GitRepo(getGitPath()+sep+repoPath)
    commitUrl=reverse('gitview.views.commit')
    commitUrl+="?path="+repoPath+'&branch='+branch+"&id=$$"
    graph=GitGraphCanvas(repo,since=since,until=until,commitUrl=str(commitUrl))
    (branches,commits)=graph.render()
    return render_to_response("graph.html",RequestContext(request,{'repoPath':repoPath,'branch':branch,'canvasCommit':commits,'canvasBranchName':branches,'branchNamesWidth':graph.branchNamesWidth,'width':graph.getWidth(),'height':graph.getHeight(),'highlights':highlights}))

""" redirect per compatibilita' con viewgit"""
def viewgit(request):
    try:
        projectName=request.GET['p']
        commitId=request.GET['h']
    except KeyError:
        return redirect('gitview.views.index')
    try:
        viewGitMap = settings.VIEWGIT_MAP_PROJECTS
        repoPath = viewGitMap[projectName]
    except AttributeError:
        repoPath=projectName
    return redirect(reverse('gitview.views.commit')+"?path="+repoPath+"&id="+commitId)
