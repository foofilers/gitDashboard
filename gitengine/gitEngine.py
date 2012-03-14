from dulwich.repo import Repo
from dulwich.objects import Commit
from dulwich.errors import NotGitRepository
from os import listdir,makedirs
from io import open
import os
from os.path import isdir,sep
from difflib  import unified_diff
import ghdiff
import re

class GitPathNotFound(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class GitChange:
    """ Represent a Single File Change inside a commit  """
    def __init__(self,commit,treeChange=None, oldSha=None,newSha=None,oldFileName=None,newFileName=None):
        self.commit=commit
        if treeChange:
            self.oldFileName=treeChange[0][0]
            self.newFileName=treeChange[0][1]
            self.oldSha=treeChange[2][0]
            self.newSha=treeChange[2][1]
        else:
            self.oldSha=oldSha
            self.newSha=newSha
            self.oldFileName=oldFileName
            self.newFileName=newFileName
        
    def getPrettyGHDiff(self):
        blobOld=self.commit.repo.get_blob(self.oldSha)
        blobNew=self.commit.repo.get_blob(self.newSha)
        return ghdiff.diff(str(blobOld).splitlines(),str(blobNew).splitlines())
    
    def getPrettyDiff(self):
        blobOld=self.commit.repo.get_blob(self.oldSha)
        blobNew=self.commit.repo.get_blob(self.newSha)
        diff=''
        for line in unified_diff(str(blobOld).splitlines(),str(blobNew).splitlines(),self.oldFileName,self.newFileName):
            diff+=line+'\n'
        diff=diff.replace('\n\n', '\n')
        return diff
    
    
class GitDir:
    def __init__(self,repo,sha,path,parent=None):
        self.repo=repo
        self.sha=sha
        self.path=path
        self.parent=parent
    def getFiles(self):
        entries=self.repo.get_object(self.sha).entries()
        files=[]
        for e in entries:
            obj = self.repo.get_object(e[2])
            if obj.get_type()==3:
                files.append(GitFile(self.repo,e[2],self.path+os.sep+e[1],self))
        return files
    
    def getSubDirs(self):
        dirs=[]
        curTree=self.repo.get_object(self.sha)
        entries=curTree.entries()
        for e in entries:
            obj = self.repo.get_object(e[2])
            if obj.get_type()==2:
                dirs.append(GitDir(self.repo,e[2],self.path+os.sep+e[1],self))
        return dirs
    
class GitFile:
    def __init__(self,repo,sha,fileName,parent=None):
        self.repo=repo
        self.sha=sha
        self.fileName=fileName
        self.parent=parent
    def getContent(self):
        return str(self.repo.get_blob(self.sha))
    
class GitTree():
    def __init__(self,repo,sha):
        self.repo=repo
        self.tree=repo.tree(sha)
        self.sha=sha
        
    def getFile(self,path):
        subdirs = path.split(os.sep)
        treeEntries = self.tree.iteritems()
        found=False
        for sd in subdirs[:-1]:
            for te in treeEntries:
                if te.path==sd:
                    treeEntries=self.repo.tree(te.sha).iteritems()
                    found=True
                    break
            if found==False:
                raise GitPathNotFound('Path:'+path+' not found')
            else:
                found=False
        fileName = subdirs[-1]
        for entry in treeEntries:
            if entry.path==fileName:
                return GitFile(self.repo, entry.sha, path)
        raise GitPathNotFound('Path:'+path+' not found')
    
    def getRoot(self):
        entries=self.repo.tree(self.sha).entries()
        root=[]
        for e in entries:
            obj = self.repo.get_object(e[2])
            if obj.get_type()==3:
                root.append(GitFile(self.repo,e[2],e[1]))
            else:
                root.append(GitDir(self.repo,e[2],e[1],))
        return root
    
    def __getTreeFiles(self,sha,path=""):
        files=[]
        entries=self.repo.tree(sha).entries()
        for e in entries:
            obj = self.repo.get_object(e[2])
            if obj.get_type()==3:
                #e' un file
                files.append(GitFile(self.repo,e[2],path+e[1]))
            else:
                if obj.get_type()==2:
                    #e' una directory
                    files.extend(self.__getTreeFiles(e[2],path+e[1]+os.sep))
        return files
    
    def getAllFiles(self):
        """ Retrieve all files in the tree 
            Return:
                return a GitFile list
        """
        return self.__getTreeFiles(self.sha)
    
class GitCommit(Commit):
    """ Represent A single Commit  """
    def __init__(self,c,repo):
        Commit.__init__(self)
        for slot in c.__slots__:
            setattr(self,slot,getattr(c,slot))
        self.repo=repo
    def parents(self):
        return self._get_parents()
    def getChanges(self):
        changes=[]
        parents=self.parents()
        if len(parents)>0:
            for p in parents:
                pc = self.repo.commit(p)
                chIter = self.repo.object_store.tree_changes(pc.tree,self.tree)
                try:
                    while True:
                        tc = chIter.next()
                        changes.append(GitChange(self,tc))
                except StopIteration:
                    pass
        else:
            #nessun parent(first commit)
            files=self.getTree().getAllFiles()
            for fl in files:
                treeChange=((None,fl.fileName),(None,None),(None,fl.sha))
                changes.append(GitChange(self,treeChange))
        return changes
    def getChange(self,fileName,parent=None):
        if parent==None:
            parents=self.parents()
            pc=self.repo.commit(parents[0])
        else:
            pc=self.repo.commit(parent)
        chIter = self.repo.object_store.tree_changes(pc.tree,self.tree)
        found=False
        try:
            while not found:
                tc = chIter.next()
                ch = GitChange(self,tc)
                if ch.newFileName==fileName:
                    found=True
        except StopIteration:
            pass
        if found:
            return ch
        else:
            return None
        
    def getTree(self):
        return GitTree(self.repo,self.tree)
    
    def getTags(self):
        repoTags=self.repo.getTagsRef()
        tags=[]
        for tagName in repoTags.keys():
            if repoTags[tagName]==self.id:
                tags.append(tagName[10:])
        return tags
    
    def getBranches(self):
        repoBranches=self.repo.getBranches()
        branches=[]
        for branch in repoBranches.keys():
            if repoBranches[branch]==self.id:
                branches.append(branch)
        return branches

def commitChanges(repo,sha1,sha2):
    """ Return a list of GitChange between two commit """
    c1=repo.getCommit(sha1)
    c2=repo.getCommit(sha2)
    chIter = repo.object_store.tree_changes(c1.tree,c2.tree)
    changes=[]
    try:
        while True:
            tc = chIter.next()
            changes.append(GitChange(c1,tc))
    except StopIteration:
        pass
    return changes

class GitRepo(Repo):
    """ Rapresent a Git Repository """
    def __init__(self,*args,**kwargs):
        super(GitRepo,self).__init__(*args,**kwargs)
        self.description=None
    def __cmp__(self,other):
        return cmp(self.path,other.path)
    def get_description(self):
        """ Get the repository description
            Returns:
                The content of 'description' files without CR
        """
        if self.description!=None:
            return self.description
        descFile = self.get_named_file('description')
        self.description=''
        if descFile!=None:
            try:
                for line in descFile.readlines():
                    self.description+=line.replace('\n',' ')
            finally:
                descFile.close()
        return self.description
    
    def getTagsRef(self):
        tags={}
        refs=self.get_refs()
        for ref in refs.keys():
            if ref.find('refs/tags/')!=-1:
                obj=self.get_object(refs[ref])
                if obj.get_type()==4:
                    tags[ref]=obj._object_sha
                else:
                    tags[ref]=refs[ref]
        return tags
    
    def getBranches(self):
        branches={}
        refs=self.get_refs()
        for ref in refs.keys():
            if ref.find('refs/tags/')==-1:
                branches[ref]=refs[ref]
        return branches
    
    def getCommit(self,commitId):
        """ Retrieve a GitCommit object represent single commit from reporistory  """
        return GitCommit(self.commit(commitId),self)
    
    def getCommits(self,num=None,since=None,until=None,branch=None,path=None):
        """ Retrieve the commits of repository
            Args:
                num: Number of commits to retrieve
                since: timestamp since retrieve commits
                until: timestamp until to retrieve commits
            Returns:
                A list of Commit object
        """
        if path:
            paths=[path]
        else:
            paths=None
            
        if branch:
            if not isinstance(branch, list):
                branch=[branch]
        try:
            w=self.get_walker(max_entries=num,since=since,until=until,include=branch,paths=paths)
        except KeyError:
            return []
        we=w._next()
        commits=[]
        while we !=None:
            commits.append(GitCommit(we.commit,self))
            we=w._next()
        return commits
        
    @staticmethod
    def getRepos(path,recursive=False,excludePath=[]):
        """ Retrieve a list of git repositories from a partent path
            Args:
                path: parent path of git repositories
                recursive: scan the parent path recursively
            Returns:
                A list of GitRepo
        """
        contents = listdir(path)
        repos=[]
        for content in contents:
            fullPath=path+sep+content
            if isdir(fullPath):
                try:
                    toAdd=True
                    for excl in excludePath:
                        if re.match(excl, content):
                            toAdd=False
                    if toAdd:
                        repos.append(GitRepo(fullPath))
                except NotGitRepository:
                    if recursive==True:
                        repos.extend(GitRepo.getRepos(fullPath,True))
        return sorted(repos)

    @staticmethod
    def create_bare( path, description=None):
        """ Create a Bare Repository 
            Args:
                path: path of new repository
                description: description of new repository
        """
        makedirs (path)
        nrp = GitRepo.init_bare(path)
        descFile = nrp.get_named_file('description')
        if description!=None and descFile!=None:
            descFilePath = descFile.name
            descFile.close()
            newdescFile = open (descFilePath,'w')
            try:
                newdescFile.write(description)
            finally:
                newdescFile.close()
        return nrp
    
    def getHead(self):
        try:
            return self.head()
        except KeyError:
            return None


