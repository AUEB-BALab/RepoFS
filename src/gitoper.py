import os

from subprocess import check_output, CalledProcessError


class GitOperations(object):
    def __init__(self, repo):
        self.repo = repo
        self._gitrepo = os.path.join(repo, '.git')

    def branches(self):
        """
        Returns branches in the form:
        <commit_hash> refs/heads/<branchname>
        """
        branchrefs = check_output(['git', '--git-dir', self._gitrepo, 'for-each-ref',\
                '--format=%(objectname) %(refname)', 'refs/heads/']).splitlines()
        branches = [ref.strip() for ref in branchrefs]
        return branches

    def tags(self):
        """
        Returns tags in the form:
        <commit_hash> refs/tags/<tagname>
        """
        tagrefs = check_output(['git', '--git-dir', self._gitrepo, 'for-each-ref',\
                '--format=%(objectname) %(refname)', 'refs/tags/']).splitlines()
        tags = [ref.strip() for ref in tagrefs]
        return tags

    def commits(self):
        """
        Returns a list of commit hashes
        """
        commits = check_output(['git', '--git-dir', self._gitrepo,\
                'log', '--pretty=format:%H']).splitlines()
        commits = [commit.strip() for commit in commits]
        return commits

    def commit_log(self, commit):
        """
        Returns commit log
        """
        return check_output(['git', '--git-dir', self._gitrepo, 'log', commit])

    def commit_parents(self, commit):
        """
        Returns commit parents
        """
        return []

    def commit_descendants(self, commit):
        """
        Returns commit descendants
        """
        return []

    def commit_names(self, commit):
        """
        Returns names associated with commit
        """
        return []

    def directory_contents(self, commit, path):
        """
        Returns the contents of the directory
        specified by `path`
        """
        if path:
            path += "/"

        contents = check_output(['git', '--git-dir', self._gitrepo, 'ls-tree',\
                '--name-only', commit, path]).splitlines()

        contents = [c.split("/")[-1] for c in contents]
        return contents

    def is_dir(self, commit, path):
        contents = self.directory_contents(commit, path)
        if contents:
            return True
        return False
