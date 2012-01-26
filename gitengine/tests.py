import unittest
from gitEngine import GitRepo
from os import mkdir
from shutil import rmtree
class mainTest(unittest.TestCase):
    
    def test_create(self):
        path="/tmp/testGitEngine"
        mkdir(path)
        nrp = GitRepo.create(path)
        self.assertNotEqual(nrp, None, "the new repository is None")
        self.assertFalse(nrp.is_bare(), "The new repository is Bare")
        rmtree(path)

if __name__ == '__main__':
    unittest.main()