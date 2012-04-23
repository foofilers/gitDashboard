from gitengine.core import GitRepo
from git.exc import GitCommandError
import os

class GitoliteAdmin(GitRepo):
    def __init__(self,path,url):
        self.url=url
        self.path=path
        if not os.path.isdir(path):
            self.createRepo()
        super(GitoliteAdmin,self).__init__(path)
    
    def createRepo(self):
        admRepo = GitRepo.init(self.path, True)
        admRepo.description="Gitolite-Admin for GitDashboard"
        admRepo.create_remote('origin',self.url)
            
    def pull(self):
        origin = self.remotes.origin
        origin.fetch()
        origin.pull('master')
    
    def getWkFileContent(self,filePath):
        """ Retrieve the content of path """
        confFile = open(self.working_dir+os.sep+filePath,"r")
        content = confFile.read()
        confFile.close();
        return content
    
    def push(self,message):
        index = self.index
        index.commit(message)
        origin = self.remotes.origin
        origin.push('master')
    
    def save(self,filePath,content):
        confFile = open(self.working_dir+os.sep+filePath,"w")
        confFile.write(content)
        confFile.close()
        index = self.index
        index.add([filePath])

    def remove(self,filePath):
        try:
            self.index.remove([filePath], working_tree=True)
        except GitCommandError:
            self.index.remove([filePath])
            os.remove(self.working_dir+os.sep+filePath)
        
    def resetHard(self):
        self.head.reset(working_tree=True)