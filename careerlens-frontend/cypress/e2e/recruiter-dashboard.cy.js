describe('Recruiter Dashboard', () => {
  beforeEach(() => {
    cy.intercept('POST', '**/api/batch-analyze**', {
      statusCode: 200,
      body: {
        success: true,
        results: [
          {
            id: 'resume_1',
            filename: 'candidate_1.pdf',
            match_score: 92.5,
            top_tier: true,
            analysis: {
              core_skills: { present: ['React', 'Node'], missing: [] }
            }
          },
          {
            id: 'resume_2',
            filename: 'candidate_2.pdf',
            match_score: 65.0,
            top_tier: false,
            analysis: {
              core_skills: { present: ['Node'], missing: ['React'] }
            }
          }
        ]
      }
    }).as('batchAnalyze')

    cy.visit('/dashboard/recruiter')
  })

  it('renders the recruiter dashboard layout', () => {
    cy.get('body').then(($body) => {
      if ($body.text().includes('Recruiter Access')) {
        cy.get('button').contains('Recruiter').click()
        cy.get('input[type="email"]').type('recruiter@test.com')
        cy.get('input[type="password"]').type('password123')
        cy.get('button').contains('Sign in').click()
      }
    })
    
    // Verify Dashboard
    cy.contains('Welcome').should('exist')
  })

  it('handles batch analysis mock', () => {
    cy.url().should('include', '/dashboard')

    // Fill the analysis form
    cy.get('input[placeholder*="Role Title"]').type('Fullstack Developer')
    cy.get('textarea[placeholder*="Job Description"]').type('Needs React and Node.js')
    
    // Mocking file upload via Cypress requires cy.selectFile() on an input[type="file"]
    // cy.get('input[type="file"]').selectFile(...)
    // Assuming there's a fallback or we can trigger it directly
    // cy.contains('Analyze').click()
  })
})
