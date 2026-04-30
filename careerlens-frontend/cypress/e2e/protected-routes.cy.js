describe('Protected Routes', () => {
  it('redirects unauthenticated students to sign in', () => {
    cy.visit('/student/dashboard')

    cy.url().should('include', '/signin')
    cy.contains('Welcome back', { matchCase: false }).should('be.visible')
  })

  it('redirects unauthenticated recruiters to sign in', () => {
    cy.visit('/recruiter/dashboard')

    cy.url().should('include', '/signin')
    cy.contains('Welcome back', { matchCase: false }).should('be.visible')
  })

  it('allows an authenticated student into the dashboard', () => {
    cy.visit('/student/dashboard', {
      onBeforeLoad(win) {
        win.localStorage.setItem('authToken', 'cypress-student-token')
        win.localStorage.setItem(
          'user',
          JSON.stringify({
            name: 'Cypress Student',
            email: 'student@test.com',
            role: 'student',
          })
        )
      },
    })

    cy.contains('Student Dashboard').should('be.visible')
  })
})