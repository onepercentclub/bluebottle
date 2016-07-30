#!/bin/bash

PARAMS="auth_token=$APIKEY&room_id=$GROUPNAME&from=Travis&message_format=html&color=green"
URL="stream.onepercentclub.com/v1/rooms/message"

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
    curl -d "$PARAMS&message=$TRAVIS_COMMIT_MSG" $URL
    curl -d "$PARAMS&message=hodor deploy backend $TRAVIS_COMMIT to $ENV" $URL
fi