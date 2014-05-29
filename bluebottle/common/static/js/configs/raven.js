if (SENTRY_DSN) {
    Raven.config(SENTRY_DSN, {
        whitelistUrls: ['/static/assets/js'],
        ignoreErrors: [
            // Random plugins/extensions
            'top.GLOBALS',
        ],
        ignoreUrls: [
            // Chrome extensions
            (/extensions\//i),
            (/^chrome:\/\//i),
        ],
        tags: {
            git_commit: GIT_COMMIT
        }
    }).install();
}