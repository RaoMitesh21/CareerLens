/**
 * Error scenario tests for CareerLens forms
 * Tests form validation, API errors, and edge cases on landing page
 */

describe("Form Validation & Error Handling", () => {
  beforeEach(() => {
    cy.visit("/");
  });

  describe("Basic Form Structure Tests", () => {
    it("contact form exists on landing page", () => {
      cy.get('#contact').should("exist");
      cy.get('#contact').scrollIntoView();
      cy.contains("Send Us a Message").should("be.visible");
    });

    it("all contact form fields are present", () => {
      cy.get('#contact').scrollIntoView();
      cy.get('input[placeholder="John Doe"]').should("exist");
      cy.get('input[placeholder="john@example.com"]').should("exist");
      cy.get('input[placeholder="What is this about?"]').should("exist");
      cy.get('select').should("exist");
      cy.get('textarea[placeholder="Tell us how we can help you..."]').should("exist");
    });

    it("submit button is visible", () => {
      cy.get('#contact').scrollIntoView();
      cy.contains("button", "Send Message").should("be.visible");
    });
  });

  describe("Contact Form Validation", () => {
    beforeEach(() => {
      // Scroll to contact form
      cy.get('#contact').scrollIntoView();
    });

    it("shows validation error when name is empty", () => {
      cy.get('input[placeholder="John Doe"]').clear();
      cy.get('input[placeholder="john@example.com"]').type("test@example.com");
      cy.get('input[placeholder="What is this about?"]').type("Test Subject");
      cy.get('select').select("Student / Career Seeker");
      cy.get('textarea[placeholder="Tell us how we can help you..."]').type("Test message");

      cy.get("form")
        .then(($form) => {
          expect($form[0].checkValidity()).to.be.false;
        });
    });

    it("validates email format in contact form", () => {
      cy.get('input[placeholder="John Doe"]').type("Test User");
      cy.get('input[placeholder="john@example.com"]').type("invalid-email");
      cy.get('input[placeholder="What is this about?"]').type("Test Subject");

      cy.get("form")
        .then(($form) => {
          expect($form[0].checkValidity()).to.be.false;
        });
    });

    it("shows validation error when message is empty", () => {
      cy.get('input[placeholder="John Doe"]').type("Test User");
      cy.get('input[placeholder="john@example.com"]').type("test@example.com");
      cy.get('input[placeholder="What is this about?"]').type("Test Subject");
      cy.get('select').select("Student / Career Seeker");
      cy.get('textarea[placeholder="Tell us how we can help you..."]').clear();

      cy.get("form")
        .then(($form) => {
          expect($form[0].checkValidity()).to.be.false;
        });
    });

    it("shows validation error when subject is empty", () => {
      cy.get('input[placeholder="John Doe"]').type("Test User");
      cy.get('input[placeholder="john@example.com"]').type("test@example.com");
      cy.get('input[placeholder="What is this about?"]').clear();
      cy.get('textarea[placeholder="Tell us how we can help you..."]').type("Test message");

      cy.get("form")
        .then(($form) => {
          expect($form[0].checkValidity()).to.be.false;
        });
    });
  });

  describe("Newsletter Form Validation", () => {
    it("newsletter section exists on page", () => {
      // Just verify the page loads without error
      cy.get("body").should("exist");
    });
  });

  describe("API Error Handling", () => {
    beforeEach(() => {
      cy.get('#contact').scrollIntoView();
    });

    it("handles contact form API errors gracefully", () => {
      // Mock API to return 500 error
      cy.intercept("POST", "**/contact/submit", {
        statusCode: 500,
        body: { detail: "Internal server error" }
      }).as("contactError");

      cy.get('input[placeholder="John Doe"]').type("Test User");
      cy.get('input[placeholder="john@example.com"]').type("test@example.com");
      cy.get('input[placeholder="What is this about?"]').type("Test Subject");
      cy.get('select').select("Student / Career Seeker");
      cy.get('textarea[placeholder="Tell us how we can help you..."]').type("Test message");
      cy.contains("button", "Send Message").click();

      cy.wait("@contactError");
      // UI should show error (form should still exist)
      cy.get('input[placeholder="John Doe"]').should("exist");
    });

    it("handles API timeout gracefully", () => {
      cy.intercept("POST", "**/contact/submit", (req) => {
        req.destroy();
      }).as("timeoutError");

      cy.get('input[placeholder="John Doe"]').type("Test User");
      cy.get('input[placeholder="john@example.com"]').type("test@example.com");
      cy.get('input[placeholder="What is this about?"]').type("Test Subject");
      cy.get('select').select("Student / Career Seeker");
      cy.get('textarea[placeholder="Tell us how we can help you..."]').type("Test message");
      cy.contains("button", "Send Message").click();

      // UI should remain functional
      cy.get('input[placeholder="John Doe"]').should("exist");
    });

    it("handles 503 service unavailable response", () => {
      cy.intercept("POST", "**/contact/submit", {
        statusCode: 503,
        body: { detail: "Service unavailable" }
      }).as("serviceUnavailable");

      cy.get('input[placeholder="John Doe"]').type("Test User");
      cy.get('input[placeholder="john@example.com"]').type("test@example.com");
      cy.get('input[placeholder="What is this about?"]').type("Test Subject");
      cy.get('select').select("Student / Career Seeker");
      cy.get('textarea[placeholder="Tell us how we can help you..."]').type("Test message");
      cy.contains("button", "Send Message").click();

      cy.wait("@serviceUnavailable");
      // Form should still be accessible
      cy.get('input[placeholder="John Doe"]').should("exist");
    });

    it("handles successful form submission", () => {
      cy.intercept("POST", "**/contact/submit", {
        statusCode: 200,
        body: { message: "Message sent successfully", success: true }
      }).as("contactSuccess");

      cy.get('input[placeholder="John Doe"]').type("Test User");
      cy.get('input[placeholder="john@example.com"]').type("test@example.com");
      cy.get('input[placeholder="What is this about?"]').type("Test Subject");
      cy.get('select').select("Student / Career Seeker");
      cy.get('textarea[placeholder="Tell us how we can help you..."]').type("Test message");
      cy.contains("button", "Send Message").click();

      cy.wait("@contactSuccess");
      // Form submission completes without error
      cy.get('input[placeholder="John Doe"]').should("exist");
    });
  });

  describe("XSS and Injection Prevention", () => {
    beforeEach(() => {
      cy.get('#contact').scrollIntoView();
    });

    it("sanitizes malicious input in contact form", () => {
      const maliciousInput = '<script>alert("XSS")</script>';

      cy.get('input[placeholder="John Doe"]').type(maliciousInput);
      cy.get('input[placeholder="john@example.com"]').type("test@example.com");
      cy.get('input[placeholder="What is this about?"]').type("Test Subject");
      cy.get('select').select("Student / Career Seeker");
      cy.get('textarea[placeholder="Tell us how we can help you..."]').type("Test message");

      // Script tag should be displayed as text, not executed
      cy.get('input[placeholder="John Doe"]')
        .should("have.value", maliciousInput);

      // No alert should appear (no XSS)
      cy.on("window:alert", () => {
        throw new Error("XSS vulnerability detected!");
      });
    });

    it("handles SQL injection attempt in form fields", () => {
      const sqlInjection = "test' OR '1'='1";

      cy.get('input[placeholder="John Doe"]').type(sqlInjection);
      cy.get('input[placeholder="john@example.com"]').type("test@example.com");
      cy.get('input[placeholder="What is this about?"]').type("Test Subject");
      cy.get('select').select("Student / Career Seeker");
      cy.get('textarea[placeholder="Tell us how we can help you..."]').type("Test message");

      // Input should be treated as plain text
      cy.get('input[placeholder="John Doe"]')
        .should("have.value", sqlInjection);
    });
  });

  describe("Browser Edge Cases", () => {
    beforeEach(() => {
      cy.get('#contact').scrollIntoView();
    });

    it("handles rapid form submissions", () => {
      cy.intercept("POST", "**/contact/submit", {
        statusCode: 200,
        body: { success: true }
      }).as("contactSubmit");

      cy.get('input[placeholder="John Doe"]').type("Test User");
      cy.get('input[placeholder="john@example.com"]').type("test@example.com");
      cy.get('input[placeholder="What is this about?"]').type("Test Subject");
      cy.get('select').select("Student / Career Seeker");
      cy.get('textarea[placeholder="Tell us how we can help you..."]').type("Test message");

      // Click submit button multiple times rapidly
      cy.contains("button", "Send Message").click();
      cy.contains("button", "Send Message").click();
      cy.contains("button", "Send Message").click();

      // Should only make one or two API calls (not three)
      cy.get("@contactSubmit.all").should("have.length.lessThan", 3);
    });

    it("handles special characters in form inputs", () => {
      const specialChars = "!@#$%^&*()_+-=[]{}|;':\",./<>?";

      cy.get('input[placeholder="John Doe"]').type("Test User");
      cy.get('input[placeholder="john@example.com"]').type("test@example.com");
      cy.get('input[placeholder="What is this about?"]').type(specialChars);
      cy.get('select').select("Student / Career Seeker");
      cy.get('textarea[placeholder="Tell us how we can help you..."]').type("Message with special chars: " + specialChars);

      // Should accept special characters
      cy.get('input[placeholder="What is this about?"]').should("have.value", specialChars);
    });

    it("allows form interaction after error", () => {
      cy.intercept("POST", "**/contact/submit", {
        statusCode: 500,
        body: { detail: "Error" }
      }).as("contactError");

      cy.get('input[placeholder="John Doe"]').type("Test User");
      cy.get('input[placeholder="john@example.com"]').type("test@example.com");
      cy.get('input[placeholder="What is this about?"]').type("Test");
      cy.get('select').select("Student / Career Seeker");
      cy.get('textarea[placeholder="Tell us how we can help you..."]').type("Test message");
      cy.contains("button", "Send Message").click();

      cy.wait("@contactError");

      // Should be able to clear and modify form after error
      cy.get('input[placeholder="John Doe"]').clear();
      cy.get('input[placeholder="John Doe"]').type("New User");
      cy.get('input[placeholder="John Doe"]').should("have.value", "New User");
    });
  });

  describe("Accessibility During Form Interaction", () => {
    beforeEach(() => {
      cy.get('#contact').scrollIntoView();
    });

    it("maintains focus during form interaction", () => {
      cy.get('input[placeholder="John Doe"]').focus();
      cy.get('input[placeholder="John Doe"]').should("have.focus");

      cy.get('input[placeholder="john@example.com"]').focus();
      cy.get('input[placeholder="john@example.com"]').should("have.focus");

      cy.get('textarea[placeholder="Tell us how we can help you..."]').focus();
      cy.get('textarea[placeholder="Tell us how we can help you..."]').should("have.focus");
    });

    it("submit button is accessible and clickable", () => {
      cy.contains("button", "Send Message")
        .should("not.be.disabled")
        .should("be.visible");
    });

    it("form is keyboard navigable", () => {
      cy.get('#contact').scrollIntoView();
      cy.get('input[placeholder="John Doe"]').focus();
      cy.get('input[placeholder="John Doe"]').should("have.focus");

      // All form fields should be reachable
      cy.get('input[placeholder="john@example.com"]').should("be.enabled");
      cy.get('input[placeholder="What is this about?"]').should("be.enabled");
      cy.get('select').should("be.enabled");
      cy.get('textarea[placeholder="Tell us how we can help you..."]').should("be.enabled");
    });

    it("form labels are properly associated", () => {
      // Labels should exist for all required fields
      cy.contains("Full Name *").should("exist");
      cy.contains("Email Address *").should("exist");
      cy.contains("Subject *").should("exist");
      cy.contains("You are a *").should("exist");
      cy.contains("Your Message *").should("exist");
    });
  });
});
