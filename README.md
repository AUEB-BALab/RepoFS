![Build status](https://api.travis-ci.org/AUEB-BALab/RepoFS.png?branch=master)

RepoFS
======
Filesystem view of version control repositories

Installation
=======================

We currently support only Debian Stretch.

1. `apt-get install libffi-dev libgit2-dev fuse python-pip`
2. `pip install repofs`

Usage
=====

`repofs [--no-ref-symlinks] [--hash-trees] <git_repo> <mount_dir>`

Run `man repofs` after installation, for a detailed explanation of RepoFS'
usage.

To unmount a Git repository from a specific mount point run `umount <mount_dir>`.
