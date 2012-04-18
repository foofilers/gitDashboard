from gitengine.gitEngine import GitRepo
import os

class GitoliteAdmin(GitRepo):
    def __init__(self,path,url):
        self.url=url
        self.path=path
        if not os.path.isdir(path):
            self.createRepo()
        super(GitoliteAdmin,self).__init__(path)
    
    def getConf(self):
        """ Retrieve the content of conf/gitolite.conf """
        tree=self.tree()
        for subT in tree.trees:
            if subT.path=='conf':
                for bl in subT.blobs:
                    if bl.name=='gitolite.conf':
                        return bl.data_stream.read()
        return None
    
    def createRepo(self):
        admRepo = GitRepo.init(self.path, True)
        admRepo.description="Gitolite-Admin for GitDashboard"
        admRepo.create_remote('origin',self.url)
            
    def pull(self):
        origin = self.remotes.origin
        origin.fetch()
        origin.pull('master')
        
    def push(self):
        origin = self.remotes.origin
        origin.push('master')
    
    def save(self,content,message):
        confFile = open(self.working_dir+"/conf/gitolite.conf","w")
        confFile.write(content)
        confFile.close()
        index = self.index
        index.add(['conf/gitolite.conf'])
        index.commit(message)
        
        