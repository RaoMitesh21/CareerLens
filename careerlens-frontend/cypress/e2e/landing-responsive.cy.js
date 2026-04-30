describe('Landing Page Responsiveness', () => {
  it('renders the main landing content on mobile', () => {
    cy.viewport(375, 667)
    cy.visit('/')

    cy.contains('Built for Students & Recruiters in India', { matchCase: false }).should('be.visible')
    cy.contains('Upload your resume').should('be.visible')
    cy.contains('It started with a question').scrollIntoView().should('be.visible')
  })
})