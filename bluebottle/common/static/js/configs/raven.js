if (RAVEN_DSN) {
    Raven.config(RAVEN_DSN, {
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