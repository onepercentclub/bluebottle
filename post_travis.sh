#!/bin/bash

if [[ $TRAVIS_BRANCH == develop ]]; then
    ENV='development'
fi

if [[ $TRAVIS_BRANCH == master ]]; then
    ENV='staging'
fi

if [[ $TRAVIS_BRANCH == release* ]]; then
    ENV='testing'
fi

if [[ ($ENV && $TRAVIS_PULL_REQUEST == 'false') ]]; then
    MESSAGES=( $TRAVIS_COMMIT_MSG "hodor deploy backend $TRAVIS_COMMIT to $ENV" )

    for m in "${MESSAGES[@]}"
    do
        curl -H "Content-Type: application/json" \
             -X POST \
             -d "{\"color\": \"purple\", \"message_format\": \"html\", \"message\": \"$m\" }" \
             https://api.hipchat.com/v2/room/$GROUPNAME/notification?auth_token=$APIKEY
    done
fi
