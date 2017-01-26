#!/usr/bin/env bash
VERSION=`$PWD/bin/version_bump.sh --print-current`

echo "Checking if $VERSION exists at https://api.github.com/repos/$WERCKER_GIT_OWNER/$WERCKER_GIT_REPOSITORY/releases/tags/$VERSION"

RESPONSE=`curl --fail -s -S -X GET https://api.github.com/repos/$WERCKER_GIT_OWNER/$WERCKER_GIT_REPOSITORY/releases/tags/$VERSION \
    -A "wercker-create-release" \
    -H "Accept: application/vnd.github.v3+json" \
    -H "Authorization: token $MC_GITHUB_TOKEN"`

if [ $? == 0 ]
then
    >&2 echo "The version already exists"
    exit 1
fi

echo "No version $VERSION was found"