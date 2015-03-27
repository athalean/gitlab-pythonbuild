#!/bin/sh
# git fetch script

#$1: repo_url
#$2: repo_name
#$3: commit_id
#$4: version string
#$5: sdist/bdist
#$6: destination directory (where the built .tar.gz files end up)

mkdir tmp/$2_$3 -p
cd tmp/$2_$3

COMPILE_DIR=$(pwd)

git clone $1 .
git checkout $3

# run a prebuild script, if present
if [ -f .prebuild-script ]; then
    ./.prebuild-script
fi

# look for a file '.build-path' that gives a hint on where the setup.py is
if [ -f .build-path ]; then
    cd $(cat .build-path)
fi

# call sdist or bdist on setup.py, and copy the generated eggs to the folder in $6 (from config.py)
VERSION_STRING=$4 python setup.py "$5" --dist-dir "$6"

cd "$COMPILE_DIR"
cd ..
rm -rf $2_$3