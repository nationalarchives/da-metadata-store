interface Credentials {
    username: string
    password: string
    clientId: string
    clientSecret: string
    tokenEndpoint: string
}

declare namespace Cypress {
    interface Chainable {
        /**
         * Login via OIDC provider
         * @param username The username to use for login
         * @param password The password to use for login
         */
        loginViaOIDC(username: string, password: string): Chainable<void>;

        /**
         * Get the credentials, either from environment variables or ssm
         */
        getCredentials(): Chainable<Credentials>
    }
}
