TOKEN_AUTH_SETTINGS = {
    'backend': 'token_auth.auth.booking.SAMLAuthentication',
    'assertion_mapping': {
        'email': 'mail',
        'remote_id': 'nameId',
        'username': 'uid'
    },
    "strict": False,
    "debug": False,
    "custom_base_path": "../../../tests/data/customPath/",
    "sp": {
        "entityId": "http://stuff.com/endpoints/metadata.php",
        "assertionConsumerService": {
            "url": "http://stuff.com/endpoints/endpoints/acs.php"
        },
        "singleLogoutService": {
            "url": "http://stuff.com/endpoints/endpoints/sls.php"
        },
        "NameIDFormat": "urn:oasis:names:tc:SAML:2.0:nameid-format:unspecified"
    },
    "idp": {
        "entityId": "http://idp.example.com/",
        "singleSignOnService": {
            "url": "http://idp.example.com/SSOService.php"
        },
        "singleLogoutService": {
            "url": "http://idp.example.com/SingleLogoutService.php"
        },
        "x509cert": (
            "MIICgTCCAeoCCQCbOlrWDdX7FTANBgkqhkiG9w0BAQUFADCBhDELMAkGA1UEBhMCTk"
            "8xGDAWBgNVBAgTD0FuZHJlYXMgU29sYmVyZzEMMAoGA1UEBxMDRm9vMRAwDgYDVQQK"
            "EwdVTklORVRUMRgwFgYDVQQDEw9mZWlkZS5lcmxhbmcubm8xITAfBgkqhkiG9w0BCQ"
            "EWEmFuZHJlYXNAdW5pbmV0dC5ubzAeFw0wNzA2MTUxMjAxMzVaFw0wNzA4MTQxMjAx"
            "MzVaMIGEMQswCQYDVQQGEwJOTzEYMBYGA1UECBMPQW5kcmVhcyBTb2xiZXJnMQwwCg"
            "YDVQQHEwNGb28xEDAOBgNVBAoTB1VOSU5FVFQxGDAWBgNVBAMTD2ZlaWRlLmVybGFu"
            "Zy5ubzEhMB8GCSqGSIb3DQEJARYSYW5kcmVhc0B1bmluZXR0Lm5vMIGfMA0GCSqGSI"
            "b3DQEBAQUAA4GNADCBiQKBgQDivbhR7P516x/S3BqKxupQe0LONoliupiBOesCO3SH"
            "bDrl3+q9IbfnfmE04rNuMcPsIxB161TdDpIesLCn7c8aPHISKOtPlAeTZSnb8QAu7a"
            "RjZq3+PbrP5uW3TcfCGPtKTytHOge/OlJbo078dVhXQ14d1EDwXJW1rRXuUt4C8QID"
            "AQABMA0GCSqGSIb3DQEBBQUAA4GBACDVfp86HObqY+e8BUoWQ9+VMQx1ASDohBjwOs"
            "g2WykUqRXF+dLfcUH9dWR63CtZIKFDbStNomPnQz7nbK+onygwBspVEbnHuUihZq3Z"
            "UdmumQqCw4Uvs/1Uvq3orOo/WJVhTyvLgFVK2QarQ4/67OZfHd7R+POBXhophSMv1ZOo"
        )
    },
    "security": {
        "authnRequestsSigned": False,
        "requestedAuthnContext": False,
        "wantAssertionsSigned": False,
        "signMetadata": False
    },
    "contactPerson": {
        "technical": {
            "givenName": "technical_name",
            "emailAddress": "technical@example.com"
        },
        "support": {
            "givenName": "support_name",
            "emailAddress": "support@example.com"
        }
    },
    "organization": {
        "en-US": {
            "name": "sp_test",
            "displayname": "SP test",
            "url": "http://sp.example.com"
        }
    }
}


TOKEN_AUTH2_SETTINGS = {
    'backend': 'token_auth.auth.booking.SAMLAuthentication',
    'assertion_mapping': {
        'email': 'mail',
        'remote_id': 'mail',
        'username': 'uid'
    },
    "strict": False,
    "debug": False,
    "custom_base_path": "../../../tests/data/customPath/",
    "sp": {
        "entityId": "http://stuff.com/endpoints/metadata.php",
        "assertionConsumerService": {
            "url": "http://stuff.com/endpoints/endpoints/acs.php"
        },
        "singleLogoutService": {
            "url": "http://stuff.com/endpoints/endpoints/sls.php"
        },
        "NameIDFormat": "urn:oasis:names:tc:SAML:2.0:nameid-format:unspecified"
    },
    "idp": {
        "entityId": "http://idp.example.com/",
        "singleSignOnService": {
            "url": "http://idp.example.com/SSOService.php"
        },
        "singleLogoutService": {
            "url": "http://idp.example.com/SingleLogoutService.php"
        },
        "x509cert": (
            "MIICgTCCAeoCCQCbOlrWDdX7FTANBgkqhkiG9w0BAQUFADCBhDELMAkGA1UEBhMCTk"
            "8xGDAWBgNVBAgTD0FuZHJlYXMgU29sYmVyZzEMMAoGA1UEBxMDRm9vMRAwDgYDVQQK"
            "EwdVTklORVRUMRgwFgYDVQQDEw9mZWlkZS5lcmxhbmcubm8xITAfBgkqhkiG9w0BCQ"
            "EWEmFuZHJlYXNAdW5pbmV0dC5ubzAeFw0wNzA2MTUxMjAxMzVaFw0wNzA4MTQxMjAx"
            "MzVaMIGEMQswCQYDVQQGEwJOTzEYMBYGA1UECBMPQW5kcmVhcyBTb2xiZXJnMQwwCg"
            "YDVQQHEwNGb28xEDAOBgNVBAoTB1VOSU5FVFQxGDAWBgNVBAMTD2ZlaWRlLmVybGFu"
            "Zy5ubzEhMB8GCSqGSIb3DQEJARYSYW5kcmVhc0B1bmluZXR0Lm5vMIGfMA0GCSqGSI"
            "b3DQEBAQUAA4GNADCBiQKBgQDivbhR7P516x/S3BqKxupQe0LONoliupiBOesCO3SH"
            "bDrl3+q9IbfnfmE04rNuMcPsIxB161TdDpIesLCn7c8aPHISKOtPlAeTZSnb8QAu7a"
            "RjZq3+PbrP5uW3TcfCGPtKTytHOge/OlJbo078dVhXQ14d1EDwXJW1rRXuUt4C8QID"
            "AQABMA0GCSqGSIb3DQEBBQUAA4GBACDVfp86HObqY+e8BUoWQ9+VMQx1ASDohBjwOs"
            "g2WykUqRXF+dLfcUH9dWR63CtZIKFDbStNomPnQz7nbK+onygwBspVEbnHuUihZq3Z"
            "UdmumQqCw4Uvs/1Uvq3orOo/WJVhTyvLgFVK2QarQ4/67OZfHd7R+POBXhophSMv1ZOo"
        )
    },
    "security": {
        "requestedAuthnContext": [
            "urn:oasis:names:tc:SAML:2.0:ac:classes:Password",
            "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
            "urn:oasis:names:tc:SAML:2.0:ac:classes:TLSClient",
            "urn:oasis:names:tc:SAML:2.0:ac:classes:X509",
            "urn:federation:authentication:windows",
            "urn:oasis:names:tc:SAML:2.0:ac:classes:Kerberos"
        ],
        "requestedAuthnContextComparison": "minimal",
    },
    "contactPerson": {
        "technical": {
            "givenName": "technical_name",
            "emailAddress": "technical@example.com"
        },
        "support": {
            "givenName": "support_name",
            "emailAddress": "support@example.com"
        }
    },
    "organization": {
        "en-US": {
            "name": "sp_test",
            "displayname": "SP test",
            "url": "http://sp.example.com"
        }
    }
}
