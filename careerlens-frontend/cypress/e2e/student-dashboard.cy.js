describe('Student Dashboard', () => {
  beforeEach(() => {
    // 1. Mock the user login context
    cy.window().then((win) => {
      // Stubbing local storage for auth or bypassing login is application specific.
      // Assuming visiting the dashboard might redirect to /auth if not logged in.
      // We will intercept the analysis API to provide mock data.
    })

    // Mock API Analysis Call
    cy.intercept('POST', '**/api/analyze**', {
      statusCode: 200,
      body: {
        success: true,
        match_score: 75.5,
        analysis: {
          core_skills: {
            score: 80,
            present: ['Python', 'SQL'],
            missing: ['Docker']
          },
          secondary_skills: {
            score: 70,
            present: ['Git'],
            missing: ['AWS']
          },
          bonus_skills: {
            score: 60,
            present: [],
            missing: ['Redis']
          }
        },
        roadmap: {
          timeline_months: 2,
          phases: [
            { phase: 1, title: 'Foundations', duration: 'Month 1', focus_area: 'Backend', skills_to_learn: ['Docker'] }
          ]
        }
      }
    }).as('analyzeResume')

    cy.visit('/dashboard/student')
  })

  it('renders the dashboard layout correctly', () => {
    // Note: If authentication redirects you to login, you may need a programmatic login command here.
    cy.get('body').then(($body) => {
      if ($body.text().includes('Student Access')) {
        // Handle login manually if needed for test
        cy.get('input[type="email"]').type('student@test.com')
        cy.get('input[type="password"]').type('password123')
        cy.get('button').contains('Sign in').click()
      }
    })
    
    // Verify Sidebar
    cy.contains('Student Dashboard').should('exist')
  })

  it('handles resume analysis mock', () => {
    // Ensure we are on the dashboard
    cy.url().should('include', '/dashboard')

    // Fill the analysis form
    cy.get('input[placeholder="e.g. Frontend Developer, Data Scientist"]').type('Backend Developer')
    cy.get('textarea[placeholder*="Paste your resume"]').type('I know Python and SQL and Git.')
    
    cy.contains('Analyze Resume').click()

    // Wait for the mock API call
    cy.wait('@analyzeResume')

    // Verify Results UI
    cy.contains('75.5%').should('be.visible')
    cy.contains('Core Skills').should('be.visible')
    cy.contains('Docker').should('be.visible')
  })
})
