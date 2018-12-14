from git import Repo
import os

# rorepo is a Repo instance pointing to the git-python repository.
# For all you know, the first argument to Repo is a path to the repository
# you want to work with
class VersionInfo:
    def __init__(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.repo = Repo(dir_path)
        assert not self.repo.bare
    def latest_commit_log(self):
        head = self.repo.head       # the head points to the active branch/ref
        master = head.reference     # retrieve the reference the head points to
        return master.log()[-1].message
