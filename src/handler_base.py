import utils

class HandlerBase:
    def __init__(self, *args, **kwargs):
        pass

    def is_dir(self, *args, **kwargs):
        raise NotImplementedError("is_dir not implemented in child class")

    def is_symlink(self, *args, **kwargs):
        raise NotImplementedError("is_symlink not implemented in child class")

    def file_contents(self, *args, **kwargs):
        raise NotImplementedError("file_contents not implemented in child class")

    def readdir(self, *args, **kwargs):
        raise NotImplementedError("readdir not implemented in child class")

    def _get_metadata_dir(self, commit):
        metaname = self.path_data['commit_path']
        if metaname == '.git-parents':
            return self.oper.commit_parents(commit)
        elif metaname == '.git-descendants':
            return self.oper.commit_descendants(commit)
        elif metaname == '.git-names':
            return self.oper.commit_names(commit)
        else:
            return []

    def _is_metadata_dir(self):
        return utils.is_metadata_dir(self.path_data['commit_path'])

    def _is_metadata_symlink(self):
        return utils.is_metadata_symlink(self.path_data['commit_path'], self.oper.all_commits())

    def _get_metadata_names(self):
        return utils.metadata_names()

    def _is_metadata_symlink(self):
        return utils.is_metadata_symlink(self.path_data['commit_path'], self.oper.all_commits())

