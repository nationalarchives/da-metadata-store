/// <reference types="cypress" />

Cypress.Commands.add('loginViaOIDC', (username: string, password: string) => {
    let sessionId: string | null = null;

    cy.intercept('GET', '/login*', (req) => {
        req.reply((res) => {
            const setCookie = res.headers['set-cookie'];
            if (Array.isArray(setCookie)) {
                const match = setCookie[0]?.match?.(/sessionid=([^;]+)/);
                if (match) sessionId = match[1];
            } else if (setCookie) {
                const match = setCookie.toString().match(/sessionid=([^;]+)/);
                if (match) sessionId = match[1];
            }
        });
    });

    cy.intercept('GET', '/auth*', (req) => {
        if (sessionId) {
            req.headers['cookie'] = `sessionid=${sessionId}`;
        }
    });

    cy.visit('/login?next=1');

    cy.get("input[name='username']").last().type(username)
    cy.get("input[name='password']").last().type(password)
    cy.get("form[method='post']").last().submit()


    cy.url({ timeout: 10000 }).should('equal', Cypress.config().baseUrl);
});
