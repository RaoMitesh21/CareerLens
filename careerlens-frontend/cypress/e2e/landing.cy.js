describe('Landing Page', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('successfully loads the home page', () => {
    cy.contains('Built for Students & Recruiters', { matchCase: false }).should('be.visible')
    cy.contains('Upload your resume', { matchCase: false }).should('be.visible')
  })

  it('renders the founder story', () => {
    cy.contains('It started with a question').scrollIntoView().should('be.visible')
  })

  it('has working navigation to auth', () => {
    // Click 'Analyse My Resume' CTA (goes to /signup)
    cy.contains('Analyse My Resume').click()
    cy.url().should('include', '/signup')
    cy.contains('Student').should('be.visible')

    // Go back and try Sign In
    cy.visit('/')
    cy.contains('Sign In').click()
    cy.url().should('include', '/signin')
    cy.contains('Welcome back').should('be.visible')
  })
})
