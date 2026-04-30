describe('Landing Page Forms', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('submits the contact form successfully', () => {
    cy.intercept('POST', '**/api/contact/submit', {
      statusCode: 200,
      body: {
        success: true,
        message: "Thank you for contacting us! We'll get back to you within 24 hours.",
      },
    }).as('contactSubmit')

    cy.contains('Send Us a Message').scrollIntoView()
    cy.get('input[placeholder="John Doe"]').type('Jane Tester')
    cy.get('input[placeholder="john@example.com"]').type('jane@example.com')
    cy.get('input[placeholder="What is this about?"]').type('Product demo')
    cy.get('select').select('Student / Career Seeker')
    cy.get('textarea[placeholder="Tell us how we can help you..."]').type('I would like to know more about the platform.')

    cy.contains('Send Message').click()
    cy.wait('@contactSubmit')
    cy.contains("We'll get back to you within 24 hours").should('be.visible')
  })

  it('subscribes to the newsletter successfully', () => {
    cy.intercept('POST', '**/api/newsletter/subscribe', {
      statusCode: 200,
      body: {
        success: true,
        message: 'You\'ve successfully subscribed to the CareerLens newsletter! Check your inbox for a confirmation.',
      },
    }).as('newsletterSubscribe')

    cy.contains('Stay in the loop').scrollIntoView()
    cy.get('input[placeholder="you@email.com"]').type('reader@example.com')
    cy.contains('Subscribe').click()

    cy.wait('@newsletterSubscribe')
    cy.contains('successfully subscribed').should('be.visible')
  })
})
