#! /bin/bash

# Function to print usage instructions
function usage {
  echo ""
  echo "Usage: $0 [--patch|--minor|--major] | [-h]"
  echo ""
  echo "Should this be a patch/minor/major release."
  echo "To pull the command out of your last git commit, you can add [bump major] or [bump minor] to your git commit."
  echo ""
  echo "Options:"
  echo "  --patch     Patch release - increment x.x.N"
  echo "  --minor     Minor release - increment x.N.x"
  echo "  --major     Major release - increment N.x.x"
  exit 1
}

ACTION="$(git log -1 --pretty=%B)"

# Parse command line arguments
while [ "$1" != "" ]; do
    case $1 in
        --patch )     shift
                      ACTION="patch"
                      ;;
        --minor )     shift
                      ACTION="minor"
                      ;;
        --major )     shift
                      ACTION="major"
                      ;;
        -h | --help ) usage
                      exit
                      ;;
        * )           shift
                      ;;
    esac
    shift
done

git fetch --tags # checkout action does not get these

# git describe has issues with GitHub Actions: https://github.com/treeder/firetils/commit/160ef4560d8855c9c05f4cae207baeb71b7791f3/checks?check_suite_id=414542684
# oldv=$(git describe --match "v[0-9]*" --abbrev=0 HEAD)
# This new way seems to work better and avoids the issue above:
# -v:refname is a version sort
oldv=$(git tag --sort=-v:refname --list "v[0-9]*" | head -n 1)

# if there is no version tag yet, let's start at 0.0.0
if [ -z "$oldv" ]; then
   echo "No existing version, starting at 0.0.0"
   oldv="0.0.0"
fi

newv=$(docker run --rm -v "$PWD":/app treeder/bump --input "$oldv" $ACTION)
echo "$oldv -> v$newv"
echo $newv > VERSION
