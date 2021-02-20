![Build status](https://api.travis-ci.org/AUEB-BALab/RepoFS.png?branch=master)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.2525388.svg)](https://doi.org/10.5281/zenodo.2525388)

RepoFS
======

RepoFS represents the Git version control system as
a virtual file system where all commits and their contents
can be traversed concurrently in a read-only manner
using shell commands.

Read the complete description and methodology on
[SoftwareX](https://www.sciencedirect.com/science/article/pii/S2352711018300712)

You can cite RepoFS as follows.
Vitalis Salis and Diomidis Spinellis.
RepoFS: File system view of Git repositories.
SoftwareX, Volume 9, 2019, Pages 288-292, ISSN 2352-7110,
https://doi.org/10.1016/j.softx.2019.03.007.


# Installation

RepoFS requires Python >= 3.6 and an installation of libgit2@1.1.0 and fuse.
**Note**: If your vendor doesn't provide libgit2 v1.1.0 you can manually build
and install it from source, following the instructions outlined below.

## Debian & Ubuntu
```bash
~ ❯❯❯ apt install libffi-dev libgit2-dev=1.1.0 fuse python3-pip
~ ❯❯❯ pip3 install repofs
```

## Arch Linux
Available in the AUR: https://aur.archlinux.org/packages/repofs-git/.

Using `pacaur`:
```bash
~ ❯❯❯ pacaur -S repofs-git
```

## OSx
```bash
~ ❯❯❯ brew install libgit2 fuse python3
~ ❯❯❯ pip3 install repofs
```

## Manual installation of libgit2

```bash
~ ❯❯❯ wget https://github.com/libgit2/libgit2/archive/v1.1.0.tar.gz
~ ❯❯❯ tar xzf v1.1.0.tar.gz
~ ❯❯❯ cd libgit2-1.1.0/
~ ❯❯❯ cmake .
~ ❯❯❯ make
~ ❯❯❯ sudo make install
~ ❯❯❯ sudo ldconfig
```

Usage
=====

```bash
~ ❯❯❯ repofs -h
usage: repofs [-h] [--hash-trees] [--no-ref-symlinks] [--no-cache] repo mount

positional arguments:
  uri               URI of the Git repository to be processed.

optional arguments:
  -h, --help         show this help message and exit
  --git-path         Path where the Git repository will be cloned.
  --mount-path       Path where the file system will be mounted
  --foreground       Allow to execute the tool in foreground mode.
  --hash-trees       Store 256 entries (first two digits) at each levelof
                     commits-by-hash for the first three levels.
  --no-ref-symlinks  Do not create symlinks for commits of refs.
  --no-cache         Do not use the cache
```

The mount directory contains four directories:

- `commits-by-hash`: Directory containing all commits of the Git repository.
A commit directory will contain the state of the repository at the time the
commit was made. Since this directory can get large you can further organize it
using the `--hash-trees` command line parameter.
```bash
~ ❯❯❯ ls commits-by-hash
06f3d110140b7ac97d000aace0ef4a4233512b6c  47d3af84ddb24690a76ffac32971313cbe500841
082974029413f8c44a07912d1d581d26744fc994  491307a672a07f0354134953fd356998e07fef63
09b371c11e80eb3fe27415c4bdfce367f6bd0279  4a8c2daab3d21c016738a19e7dc8ad8eb3a02eca
...
...
```
- `commits-by-date`: Directory containing all commits of the Git repository
  organized by the time of their creation.
```bash
~ ❯❯❯ ls commits-by-date
2017    2018
~ ❯❯❯ ls commits-by-date/2017
01  02  03  04  05  06  07  08  09  10  11  12
~ ❯❯❯ ls commits-by-date/2017/12
01  02  03  04  05  06  07  08  09  10  11  12
13  14  15  16  17  18  19  20  21  22  23  24
25  26  27  28  29  30  31
~ ❯❯❯ ls commits-by-date/2017/12/18
1a6ca70a91f6ec1fb4de5a80bfb20a0d7b484680  2677b75fd531be570373fe25fc7d576c92e8acd3
58e16f66ae5df0b6e632144ac72c7dd9e3baea37  c5bbc3be37479b23e833d1cb6bddb31ca95f8293
```
- `tags`: Contains all tags of the Git repository. We represent the tag
  relationship as a symbolic link to the commit the tag points to. In order for
  the Unix command `find` to work properly we provide the `--no-ref-symlinks`
  option.
- `branches`: Similar to the tags directory. Contains all branch names and
  further organizes them to remote branches and local branches.
```bash
~ ❯❯❯ ls branches
heads  remotes
~ ❯❯❯ ls branches/remotes
origin
~ ❯❯❯ ls branches/remotes/origin
HEAD  master
```

Run `man repofs` after installation for a complete explanation of RepoFS'
usage.

To unmount a Git repository from a specific mount point run `umount <mount_dir>`.

