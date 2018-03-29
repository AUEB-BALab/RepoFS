import utils

from handler_base import HandlerBase

BRANCH_TYPE = "BRANCH"
TAG_TYPE = "TAG"
BRANCH_REFS = ['refs/heads/', 'refs/remotes/']
TAG_REFS = ['refs/tags']
class RefHandler(HandlerBase):
    def __init__(self, path, oper, refs, no_ref_symlinks):
        self.path = path
        self.oper = oper
        self.no_ref_symlinks = no_ref_symlinks
        self.refs = self.oper.refs(refs)
        self.path_data = utils.demux_ref_path(path, self.refs)

    def _is_ref_prefix(self):
        elements = self.path_data['ref'].split("/")
        for ref in self.refs:
            ref = ref.split('/')[1:]
            if elements == ref[:len(elements)] and len(elements) < len(ref):
                return True
        return False

    def _is_full_ref(self):
        """Return true if the specified path (e.g. branches/master, or
        tags/V1.0) refers to one of the specified refs, (e.g.
        refs/heads or refs/tags). """
        for ref in self.refs:
            ref = ref.split('/')[1:]
            # print('Check path [%s] == ref [%s]' % (path, ref))
            if self.path_data['ref'] == "/".join(ref):
                return True
        return False

    def _get_commit(self):
        if self._is_full_ref():
            return self.oper.commit_of_ref(self.path_data['ref'])
        return ""

    def _is_metadata_dir(self):
        return utils.is_metadata_dir(self.path_data['commit_path'])

    def _is_metadata_symlink(self):
        return utils.is_metadata_symlink(self.path_data['commit_path'], self.oper.all_commits())

    def is_dir(self):
        if not self.path_data['ref']:
            return True

        if self._is_ref_prefix():
            return True
        if self.no_ref_symlinks:
            if self.path_data['type'] not in ['tags', 'heads', 'remotes']:
                return False
            if not self._is_full_ref():
                return False
            return self._is_metadata_dir() or self.oper.is_dir(self._get_commit(), self.path_data['commit_path'])
        return False


    def is_symlink(self):
        if (self._is_metadata_symlink() or
                (self._is_full_ref() and not self.no_ref_symlinks)):
            return True
        return False
