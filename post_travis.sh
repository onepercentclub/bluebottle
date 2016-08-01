#!/bin/bash

URL="https://api.hipchat.com/v2/$GROUPNAME/notification?auth_token=$APIKEY"

if [[ $TRAVIS_BRANCH == 'develop' ]]; then
    ENV='development'
fi

if [[ $TRAVIS_BRANCH == 'master' ]]; then
    ENV='staging'
fi

if [[ $TRAVIS_BRANCH =~ ^release//* ]]; then
    ENV='testing'
fi

if [[ ($ENV && $TRAVIS_PULL_REQUEST == 'false') ]]; then
    curl -d "{\"color\": \"green\", \"message\": \"$TRAVIS_COMMIT_MSG\" }" $URL
    curl -d "{\"color\": \"green\", \"message\": \"hodor deploy backend $TRAVIS_COMMIT to $ENV\" }" $URL
fi