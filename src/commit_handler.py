from handler_base import HandlerBase
from gitoper import GitOperError

class CommitHandler(HandlerBase):
    def _get_commit_content(self):
        # root isn't a commit hash
        if self.path_data['commit'] not in self.oper.all_commits():
            self._not_exists()

        if self._is_metadata_dir():
            return self._get_metadata_dir(self.path_data['commit'])

        try:
            dirents = self.oper.directory_contents(self.path_data['commit'], self.path_data['commit_path'])
        except GitOperError:
            self._dir_not_exists()

        if not self.path_data['commit_path']:
            dirents += self._get_metadata_names()

        return dirents
