class Cache(object):
    def __init__(self):
        self._storage = {}

    def store_commits(self, commitNames):
        if 'commits' not in self._storage:
            self._storage['commits'] = {}

        for commit in commitNames:
            self._storage['commits'][commit] = {}

    def store_commit_data(self, chash, data):
        self._storage['commits'][chash] = data

    def store_tag(self, tag, chash):
        if 'tags' not in self._storage:
            self._storage['tags'] = {}

        self._storage['tags'][tag] = chash

    def store_branch(self, branch, chash):
        if 'branches' not in self._storage:
            self._storage['branches'] = {}

        self._storage['branches'][branch] = chash

    def get_commit_names(self):
        if 'commits' not in self._storage:
            return None

        return self._storage['commits'].keys()

    def get_commit_data(self, chash):
        if 'commits' not in self._storage or\
                chash not in self._storage['commits'] or\
                not self._storage['commits'][chash]:
            return None

        return self._storage['commits'][chash]

    def get_tags(self):
        if 'tags' not in self._storage:
            return None

        return self._storage['tags']

    def get_branches(self):
        if 'branches' not in self._storage:
            return None

        return self._storage['branches']
