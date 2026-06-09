import { defineConfig } from 'cypress'

import {SSMClient, GetParameterCommand} from "@aws-sdk/client-ssm";

export default defineConfig({
  allowCypressEnv: false,
  e2e: {
    env: {
      user: process.env["USER"],
      password: process.env["PASSWORD"],
      passwordPath: process.env["PASSWORD_PATH"],
      tokenEndpoint: process.env["TOKEN_ENDPOINT"],
      clientId: process.env["CLIENT_ID"],
      clientIdPath: process.env["CLIENT_ID_PATH"],
      clientSecret: process.env["CLIENT_SECRET"],
      clientSecretPath: process.env["CLIENT_SECRET_PATH"],
      credentialsFromSsm: process.env["CREDENTIALS_FROM_SSM"]
    },
    chromeWebSecurity: false,
    setupNodeEvents(on, config) {
      on('task', {
        async getSsmCredentials(parameterPaths: string[]) {
          const client = new SSMClient({region: "eu-west-2"})
          const results: {[x: string]: string} = {}
          for (const path of parameterPaths) {
            const command = new GetParameterCommand({Name: path, WithDecryption: true})
            const result = await client.send(command)
            results[path] = result.Parameter!.Value!
          }
          return results
        },
      })
    }
  },
});
