#!/bin/sh

rm -rf test_repo
mkdir test_repo
cd test_repo
git init

date_commit()
{
  local d="$1T12:00:00"
  shift
  GIT_COMMITTER_DATE="$d" GIT_AUTHOR_DATE="$d" git commit "$@"
}

touch file_a file_b file_c file_d

# Top level files
git add file_a file_b
date_commit 2005-06-07 -a -m 'Add files a, b'
git tag t20050607
git tag tdir/tname

echo "Contents" >> file_a

git add file_a
date_commit 2005-06-10 -a -m 'Update file a'

# Commit in different day
git add file_c
date_commit 2005-06-30 -m 'Add file c'
git tag t20050630

# Commit in the next month
echo phantom >file_r
git add file_d file_r
date_commit 2005-07-01 -m 'Add file d,r'
echo hi >file_d
date_commit 2005-07-01 -am 'Change file d'
git tag t20050701

git checkout -b b20050701
git checkout -b feature/a
git checkout -b private/john/b
git checkout -b private/john/c
git checkout master

# Files in directory
mkdir -p dir_a/dir_b/dir_c
touch dir_a/file_aa dir_a/dir_b/dir_c/file_ca

# Two commits on same day
git add dir_a/file_aa
date_commit 2009-10-11 -m 'Add files aa, ca'
git tag t20091011aa

git add dir_a/dir_b/dir_c/file_ca
date_commit 2009-10-11 -m 'Add files aa, ca'
git tag t20091011ca
