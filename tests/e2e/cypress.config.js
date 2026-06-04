const { defineConfig } = require("cypress");

module.exports = defineConfig({
  allowCypressEnv: false,
  e2e: {
    env: {
      user: process.env["USER"],
      password: process.env["PASSWORD"],
      tokenEndpoint: process.env["TOKEN_ENDPOINT"],
      clientId: process.env["CLIENT_ID"],
      clientSecret: process.env["CLIENT_SECRET"]
    },
    failOnStatusCode: false,
    chromeWebSecurity: false,
    setupNodeEvents(on, config) {}
  },
});
