metadata_dirs = ['.git-parents', '.git-descendants', '.git-names']

def get_full_ref(path, refs):
    elements = path.split("/")
    for ref in refs:
        ref = ref.split("/")[1:]
        joined_ref = "/".join(ref)
        if (path.startswith(joined_ref) and
                "/".join(elements[:len(ref)]) == joined_ref):
            return "/".join(ref)
    return ""

def demux_ref_path(path, refs):
    elements = path.split("/")
    ref_type = elements[0]

    full_ref = get_full_ref(path, refs)

    if full_ref:
        commit_path = "/".join(elements[len(full_ref.split("/")):])
    else:
        full_ref = "/".join(elements)
        commit_path = ""

    return {
        'type': ref_type,
        'ref': full_ref,
        'commit_path': commit_path
    }

def demux_commits_by_hash_path(path, hash_trees):
    elements = path.split("/")
    htree_prefix = ""
    commit = ""
    commit_path = ""

    if hash_trees:
        htree_prefix = "/".join(elements[:3])
        elements = elements[3:]

    if elements:
        commit = elements[0]
        commit_path = "/".join(elements[1:])

    return {
        'commit': commit,
        'commit_path': commit_path,
        'htree_prefix': htree_prefix
    }

def is_metadata_symlink(path, commits):
    elements = path.split("/")
    if (len(elements) != 2 or
            elements[0] not in metadata_dirs or
            elements[1] not in commits):
        return False
    return True

def is_metadata_dir(path):
    elements = path.split("/")
    if len(elements) != 1 or elements[0] not in metadata_dirs:
        return False
    return True

def metadata_names():
    return metadata_dirs
