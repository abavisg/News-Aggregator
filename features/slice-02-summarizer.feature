@slice02 @critical
Feature: AI Article Summarizer
  As a news aggregator system
  I want to generate concise AI-powered summaries of articles
  So that readers can quickly understand article content

  Background:
    Given the AI summarizer is initialized

  @golden @happy-path
  Scenario: Summarize article using Claude API
    Given a valid article with the following data:
      | field   | value                                      |
      | title   | OpenAI Releases GPT-5 with New Capabilities |
      | link    | https://techcrunch.com/2025/11/gpt5        |
      | content | OpenAI today announced the release of GPT-5, featuring breakthrough reasoning capabilities and achieving 95% accuracy on complex logic benchmarks. The model demonstrates significant improvements in mathematical reasoning and code generation. |
    And the Claude API is available and configured
    When I request a summary of this article
    Then a summary should be generated successfully
    And the summary should be between 50 and 200 characters
    And the summary should capture the key point about GPT-5
    And the token count should be tracked and returned

  @provider-detection
  Scenario: Auto-detect available AI provider
    Given no specific AI provider is configured
    When I initialize the summarizer
    Then the system should detect available providers
    And Claude API should be checked first
    And Ollama should be checked as fallback
    And the first available provider should be selected

  @provider-fallback
  Scenario: Fallback to Ollama when Claude API unavailable
    Given the Claude API is unavailable or not configured
    And Ollama is running locally with model "llama2"
    When I request a summary of an article
    Then the system should automatically use Ollama
    And a summary should be generated successfully
    And the provider should be recorded as "ollama"

  @error-handling
  Scenario: Handle Claude API rate limit gracefully
    Given the Claude API returns a rate limit error
    When I request a summary of an article
    Then the system should log the rate limit error
    And the system should retry with exponential backoff
    And after max retries, an appropriate error should be raised

  @error-handling
  Scenario: Handle invalid API key
    Given the Claude API key is invalid or missing
    When I attempt to summarize an article
    Then the system should raise an authentication error
    And the error message should indicate API key issue
    And the error should be logged with severity "ERROR"

  @token-tracking
  Scenario: Track token usage for cost monitoring
    Given a Claude API request is made
    When a summary is generated
    Then the input token count should be recorded
    And the output token count should be recorded
    And the total tokens should be calculated correctly
    And token counts should be included in the summary metadata

  @content-validation
  Scenario: Handle article with missing content
    Given an article with no content field
    When I attempt to summarize this article
    Then the system should raise a validation error
    And the error should indicate missing content
    And no API calls should be made

  @content-validation
  Scenario: Handle article with very short content
    Given an article with content less than 20 characters
    When I attempt to summarize this article
    Then the system should return the original content as summary
    And no AI API calls should be made
    And a warning should be logged

  @prompt-engineering
  Scenario: Use appropriate prompt for tech article summarization
    Given a technical article about AI/ML
    When I generate a summary
    Then the prompt should request a concise technical summary
    And the prompt should specify the character limit
    And the prompt should emphasize key technical details
    And the prompt should be sent to the AI provider

  @multiple-articles
  Scenario: Summarize multiple articles in batch
    Given a list of 5 articles to summarize
    When I request batch summarization
    Then all 5 articles should be summarized
    And summaries should be returned in the same order
    And each summary should include metadata
    And total token usage should be aggregated

  @ollama-integration
  Scenario: Successfully summarize using local Ollama
    Given Ollama is running on localhost:11434
    And the "llama2" model is available
    And an article needs summarization
    When I summarize using Ollama
    Then a POST request should be made to the Ollama API
    And the summary should be extracted from the response
    And the provider should be marked as "ollama"
    And no external API calls should be made

  @performance
  Scenario: Summarization completes within timeout
    Given a typical tech article
    When I request summarization with a 30 second timeout
    Then the summary should be generated within the timeout
    And the response time should be logged

  @quality-assurance
  Scenario: Verify summary quality and relevance
    Given an article about quantum computing
    When a summary is generated
    Then the summary should mention quantum computing
    And the summary should be grammatically correct
    And the summary should not include generic phrases
    And the summary should focus on the main innovation or news
