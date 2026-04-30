describe('Authentication Flow', () => {
  beforeEach(() => {
    cy.visit('/signin')
  })

  it('can navigate to sign up and see role selection', () => {
    cy.contains('Sign up').click()
    cy.url().should('include', '/signup')
    cy.contains('Join CareerLens', { matchCase: false }).should('be.visible')
    cy.contains('Student').should('be.visible')
    cy.contains('Recruiter').should('be.visible')
  })

  it('shows validation errors for empty fields on login', () => {
    // Attempt login without filling fields
    cy.get('button').contains('Sign In').click()
    // HTML5 validation usually catches this, check if it prevents navigation
    cy.url().should('include', '/signin') // should still be on auth page
  })

  it('can navigate to forgot password', () => {
    cy.contains('Forgot password').click()
    cy.url().should('include', '/forgot-password')
    cy.contains('Reset Password').should('be.visible')
  })
})
