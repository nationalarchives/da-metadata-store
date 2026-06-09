import * as os from "os"

describe('template spec', () => {

    let username: string
    let password: string
    let tokenEndpoint: string
    let clientId: string
    let clientSecret: string

    before(() => {
        cy.getCredentials()
            .then(({username: user, password: pass, tokenEndpoint: endpoint, clientId: id, clientSecret: secret}) => {
            username = user
            password = pass
            tokenEndpoint = endpoint
            clientId = id
            clientSecret = secret
        })
    })

    it('redirects to the login page', () => {
        cy.intercept("GET", "/").as("login");
        cy.visit('/')

        // @ts-ignore
        cy.wait("@login").should(({_, response}) => {
            if (response) {
                expect(response.statusCode).to.equal(302);
                expect(response.headers["location"]).to.equal("/login?next=/");
            }
        });
    })

    it("searches for a record", () => {
        cy.loginViaOIDC(username, password)
        cy.get("#search").type("ABC")
        cy.get("#search-form").submit()
        cy.get("a[href='/records/20726b87-33d0-4fec-b6ff-3ce76a988c84']").should("contain.text", "ABC/123")
        cy.get(".tna-card__body").should("contain.text", "A description")
    })

    it("renders a record", () => {
        cy.loginViaOIDC(username, password)
        cy.visit("/records/20726b87-33d0-4fec-b6ff-3ce76a988c84")
        cy.get(".tna-hgroup-xl > .tna-hgroup__title").should("contain.text", "ABC/123")
        cy.get("#details").should("contain.text", "Details")
        const summaryFields: { [key: string]: string } = {};
        cy.get(".tna-dl--lined > dt")
            .each((dt) => {
                summaryFields[dt.text().trim()] = dt.next("dd").text().trim();
            })
            .then((_) => {
                expect(summaryFields["Description"]).to.equal("A description")
                expect(summaryFields["Field1"]).to.equal("value1")
            })
    })

    it('downloads the json file', () => {
        cy.loginViaOIDC(username, password)
        cy.visit("/records/20726b87-33d0-4fec-b6ff-3ce76a988c84")
        cy.get("a[href='/records/20726b87-33d0-4fec-b6ff-3ce76a988c84/download']").click()
        const downloadsFolder = Cypress.config("downloadsFolder");
        const expectedJson = {
            "field1": "value1",
            "description": "A description"
        }
        cy.readFile(`${downloadsFolder}/20726b87-33d0-4fec-b6ff-3ce76a988c84.json`).should("deep.equal", expectedJson)
    });

    it("uploads a modified file", () => {
        cy.loginViaOIDC(username, password)
        cy.visit("/upload/0905a1ad-c816-4201-a77d-c914032faf1f")
        const dir = os.tmpdir()
        const path = `${dir}/upload.json`
        const jsonToUpload = {
            recordId: '20726b87-33d0-4fec-b6ff-3ce76a988c84',
            reference: 'ABC/123',
            description: 'A different description',
            field1: 'value2',
            field2: 'value1'
        }
        cy.writeFile(path, JSON.stringify(jsonToUpload))
        cy.get('input[type=file]').selectFile(path)
        cy.get("#reason").select("043dee8b-afca-44c3-affb-6eabcaf4366e")
        cy.get("form[method='POST']").submit()

        cy.get("h1").should("contain.text", "Record ABC/456 has been updated")

        cy.visit("/records/0905a1ad-c816-4201-a77d-c914032faf1f")
        const summaryFields: { [key: string]: string } = {};
        cy.get(".tna-dl--lined > dt")
            .each((dt) => {
                summaryFields[dt.text().trim()] = dt.next("dd").text().trim();
            }).then((_) => {
            expect(summaryFields["Description"]).to.equal("A different description")
            expect(summaryFields["Field1"]).to.equal("value2")
            expect(summaryFields["Field2"]).to.equal("value1")
        })
    })

    it("returns the expected result from the API", async () => {
        cy.request({
            url: tokenEndpoint,
            method: "POST",
            auth: {username: clientId, password: clientSecret},
            body: {"client_id": clientId, "client_secret": clientSecret, grant_type: "client_credentials"},
            form: true
        }).then(tokenResponse => {
            cy.request({
                url: "/api/records/20726b87-33d0-4fec-b6ff-3ce76a988c84",
                headers: {'Authorization': `Bearer ${tokenResponse.body.access_token}`}
            }).then(apiResponse => {
                const body = apiResponse.body
                expect(body.audit).to.equal([])
                expect(body.metadata.field1).to.equal("value2")
                expect(body.metadata.field2).to.equal("value1")
            })
        })

    })
})