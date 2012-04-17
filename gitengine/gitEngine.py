from os import listdir,makedirs
from io import open
import os
from os.path import isdir,sep
from difflib  import unified_diff
import ghdiff
import re
from django.utils.encoding import smart_unicode,DjangoUnicodeDecodeError

from git import Repo,Commit,Blob
from git.repo.fun import is_git_dir
from git.exc import InvalidGitRepositoryError
from binascii import unhexlify

class GitRepo(Repo):
    """ Rapresent a Git Repository """
    def __init__(self,*args,**kwargs):
        super(GitRepo,self).__init__(*args,**kwargs)
        self.path=self.working_dir
    def __cmp__(self,other):
        return cmp(self.path,other.path)

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
        for ref in self.branches:
            branches[ref.name]=ref.commit.hexsha
        return branches
    
    def getCommit(self,commitId):
        """ Retrieve a GitCommit object represent single commit from reporistory  """
        return GitCommit(self.commit(commitId))
        
    def getCommits(self,num=None,since=None,until=None,branch=None,path=None):
        """ Retrieve the commits of repository
            Args:
                num: Number of commits to retrieve
                since: timestamp since retrieve commits
                until: timestamp until to retrieve commits
            Returns:
                A list of Commit object
        """ 
        params={}
        if since:
            params['since']=since
        if until:
            params['until']=until
        cmts=self.iter_commits(rev=branch,paths=path,max_count=num,**params)
        commits=[]
        for cmt in cmts:
            commits.append(GitCommit(cmt))
        return commits
            
    def getHead(self):
        try:
            return self.head
        except KeyError:
            return None
    
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
            fullPath=fullPath.replace('//','/')
            if isdir(fullPath):
                try:
                    toAdd=True
                    for excl in excludePath:
                        if re.match(excl, content):
                            toAdd=False
                    if toAdd:
                        repos.append(GitRepo(fullPath))
                except InvalidGitRepositoryError:
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

class GitCommit():
    """ Represent A single Commit  """
    def __init__(self,commit):
        self.commit=commit
    
    """ Retireve the tree changes from parents"""
    def getChanges(self):
        parents=self.commit.parents
        if len(parents)>0:
            for p in parents:
                pc = self.commit.repo.commit(p)
                return pc.diff(self.commit)
        else:
            #nessun parent(first commit)
            """files=self.getTree().getAllFiles()
            for fl in files:
                treeChange=((None,fl.fileName),(None,None),(None,fl.sha))
                changes.append(GitChange(self,treeChange))"""
            pass

    def getChange(self,fileName,parent=None):
        """if parent==None:
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
            return None"""
        pass
        
    def getTree(self):
        return GitTree(self.commit.repo,self.commit.tree)
    
    def getTags(self):
        repoTags=self.commit.repo.tags
        tags=[]
        for tag in repoTags:
            if tag.commit.hexsha==self.commit.hexsha:
                tags.append(tag.name)
        return tags
        
    def getBranches(self):
        repoBranches=self.commit.repo.branches
        branches=[]
        for branch in repoBranches:
            if branch.commit.hexsha == self.commit.hexsha:
                branches.append(branch.name)
        return branches


class GitTree():
    def __init__(self,repo,tree):
        self.repo=repo
        self.tree=tree
        
    def getFile(self,path):
        try:
            blob = self.tree[path]
            return GitFile(blob)
        except KeyError:
            raise GitPathNotFound('Path:'+path+' not found')
    
    def getRoot(self):
        """ Retreive the root tree"""
        root=[]
        for subTree in  self.tree.trees:
            root.append(GitDir(subTree))
        for blob in self.tree.blobs:
            root.append(GitFile(blob))
        return root
    
    def __getTreeFiles(self,tree,path=""):
        files=[]
        for subTree in tree.trees:
            files.extend(self.__getTreeFiles(subTree, path))
        for blob in tree.tree.blobs:
            files.append(GitFile(blob))
        return files
    
    def getAllFiles(self):
        """ Retrieve all files in the tree 
            Return:
                return a GitFile list
        """
        return self.__getTreeFiles(self.sha)

class GitPathNotFound(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class GitChange:
    """ Represent a Single File Change inside a commit  """
    def __init__(self,commit,oldSha=None,newSha=None):
        self.commit=commit
        self.oldSha=oldSha
        self.newSha=newSha
        
    def getPrettyGHDiff(self):
        blobOld=Blob(self.commit.commit.repo,unhexlify(self.oldSha)).data_stream.read()
        blobNew=Blob(self.commit.commit.repo,unhexlify(self.newSha)).data_stream.read()
        try:
            diffContent =  ghdiff.diff(smart_unicode(blobOld).splitlines(),smart_unicode(blobNew).splitlines())
        except DjangoUnicodeDecodeError:
            diffContent =  ghdiff.diff(str(blobOld).decode('latin1').splitlines(),str(blobNew).decode('latin1').splitlines())
        return diffContent
    def getPrettyDiff(self):
        blobOld=Blob(self.commit.commit.repo,unhexlify(self.oldSha)).data_stream.read()
        blobNew=Blob(self.commit.commit.repo,unhexlify(self.newSha)).data_stream.read()
        diff=''
        try:
            diffs=unified_diff(smart_unicode(blobOld).splitlines(),smart_unicode(blobNew).splitlines())
        except DjangoUnicodeDecodeError:
            diffs=unified_diff(str(blobOld).decode('latin1').splitlines(),str(blobNew).decode('latin1').splitlines())
        for line in diffs:
            diff+=line+'\n'
        diff=diff.replace('\n\n', '\n')
        return diff
    
    
class GitDir:
    def __init__(self,tree,parent=None):
        self.tree=tree
        self.parent=parent
    def getFiles(self):
        files=[]
        for blob in self.tree.blobs:
            files.append(GitFile(blob))
        return files
    
    def getSubDirs(self):
        dirs=[]
        for subTree in self.tree.trees:
            dirs.append(GitDir(subTree))
        return dirs
    
class GitFile:
    def __init__(self,blob):
        self.blob=blob
    def getContent(self):
        return self.blob.data_stream.read()

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


