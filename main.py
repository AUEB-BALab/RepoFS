import sys
import os
import argparse
import datetime
from fuse import FUSE

from repofs.repofs import RepoFS

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="Git repository to be processed.")
    parser.add_argument("mount", help="Path where the FileSystem will be mounted." \
    "If it doesn't exist it is created and if it exists and contains files RepoFS exits.")
    parser.add_argument(
        "--hash-trees",
        help="Store 256 entries (first two digits) at each level" \
            "of commits-by-hash for the first three levels.",
        action="store_true",
        default=False
    )
    parser.add_argument(
        "--no-ref-symlinks",
        help="Do not create symlinks for commits of refs.",
        action="store_true",
        default=False
    )
    parser.add_argument(
        "-nocache",
        "--nocache",
        help="Do not cache repository metadata. FileSystem updates when the repository changes.",
        action="store_true",
        default=False
    )
    args = parser.parse_args()

    if not os.path.exists(os.path.join(args.repo, '.git')):
        raise Exception("Not a git repository")

    foreground = True
    if sys.argv[0].endswith("repofs"):
        foreground = False

    sys.stderr.write("Examining repository.  Please wait..\n")
    start = datetime.datetime.now()
    repo = RepoFS(os.path.abspath(args.repo), os.path.abspath(args.mount), args.hash_trees, args.no_ref_symlinks, args.nocache)
    end = datetime.datetime.now()
    sys.stderr.write("Ready! Repository mounted in %s\n" % (end - start))
    sys.stderr.write("Repository %s is now visible at %s\n" % (args.repo,
                                                               args.mount))
    FUSE(repo, args.mount, nothreads=True, foreground=foreground)

if __name__ == '__main__':
    main()
