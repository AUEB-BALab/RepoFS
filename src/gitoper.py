import os

from subprocess import check_output, CalledProcessError, call


class GitOperations(object):
    def __init__(self, repo):
        self.repo = repo
        self._gitrepo = os.path.join(repo, '.git')

    def branches(self):
        """
        Returns branches in the form:
        <commit_hash> refs/heads/<branchname>
        """
        try:
            branchrefs = check_output(['git', '--git-dir', self._gitrepo, 'for-each-ref',\
                    '--format=%(objectname) %(refname)', 'refs/heads/']).splitlines()
            branches = [ref.strip() for ref in branchrefs]
            return branches
        except CalledProcessError as e:
            print str(e)
            return None

    def tags(self):
        """
        Returns tags in the form:
        <commit_hash> refs/tags/<tagname>
        """
        try:
            tagrefs = check_output(['git', '--git-dir', self._gitrepo, 'for-each-ref',\
                    '--format=%(objectname) %(refname)', 'refs/tags/']).splitlines()
            tags = [ref.strip() for ref in tagrefs]
            return tags
        except CalledProcessError as e:
            print str(e)
            return None

    def commits(self):
        """
        Returns a list of commit hashes
        """
        try:
            commits = check_output(['git', '--git-dir', self._gitrepo,\
                    'log', '--pretty=format:%H']).splitlines()
            commits = [commit.strip() for commit in commits]
            return commits
        except CalledProcessError as e:
            print str(e)
            return None

    def commit_log(self, commit):
        """
        Returns commit log
        """
        try:
            return check_output(['git', '--git-dir', self._gitrepo, 'log', commit])
        except CalledProcessError as e:
            print str(e)
            return None

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

        try:
            contents = check_output(['git', '--git-dir', self._gitrepo, 'ls-tree',\
                    '--name-only', commit, path]).splitlines()

            contents = [c.split("/")[-1] for c in contents]
            return contents
        except CalledProcessError as e:
            print str(e)
            return None

    def is_dir(self, commit, path):
        contents = self.directory_contents(commit, path)
        if contents:
            return True
        return False

    def file_contents(self, commit, path):
        try:
            call(['git', '--git-dir', self._gitrepo, 'cat-file',\
                    '-e', "%s:%s" % (commit, path)])

            return check_output(['git', '--git-dir', self._gitrepo, 'show',\
                    "%s:%s" % (commit, path)])
        except CalledProcessError as e:
            return None

    def file_size(self, commit, path):
        contents = self.file_contents(commit, path)
        if not contents:
            return 0

        return len(contents.encode('utf-8'))
