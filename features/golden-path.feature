@e2e @golden @critical
Feature: Golden Path - Full Pipeline Integration
  As a news aggregator system
  I want to execute the complete pipeline from fetch to LinkedIn post
  So that I can deliver weekly tech digests end-to-end

  Background:
    Given all system components are initialized
    And external dependencies are available

  @full-pipeline
  Scenario: Complete pipeline execution - Fetch → Summarize → Compose
    Given the following RSS feed sources are configured:
      | source                                    | expected_articles |
      | https://techcrunch.com/feed/              | at least 5        |
      | https://www.theverge.com/rss/index.xml   | at least 5        |
    When I execute the full pipeline
    Then articles should be fetched from all sources
    And at least 10 articles should be retrieved
    And each article should have all required fields
    And articles should be summarized using AI
    And at least 5 summaries should be generated
    And a LinkedIn post should be composed from summaries
    And the post should be valid and under 3000 characters
    And the post should include 3-6 article highlights
    And the post should include 5-8 hashtags
    And the entire pipeline should complete within 2 minutes

  @slice01-verification
  Scenario: Verify Slice 01 (Fetcher) in pipeline context
    When I fetch articles from live RSS feeds
    Then articles should be retrieved successfully
    And articles should have normalized structure
    And articles should be sorted by date
    And at least 3 different sources should be represented
    And no duplicate articles should be included
    And all dates should be valid datetime objects

  @slice02-verification
  Scenario: Verify Slice 02 (Summarizer) in pipeline context
    Given fetched articles from RSS feeds
    When I summarize the articles using AI
    Then summaries should be generated for all articles
    And each summary should be between 50-200 characters
    And Claude API or Ollama should be used
    And token usage should be tracked
    And provider information should be recorded
    And no summarization errors should occur

  @slice03-verification
  Scenario: Verify Slice 03 (Composer) in pipeline context
    Given articles have been fetched and summarized
    When I compose a LinkedIn post from the summaries
    Then a valid post should be generated
    And post metadata should include all required fields
    And the character count should be within LinkedIn limits
    And the week key should match current week
    And hashtags should be relevant to content
    And article sources should be diverse

  @integration-points
  Scenario: Verify data flow between components
    Given the pipeline is executed end-to-end
    Then fetcher output should be valid input for summarizer
    And summarizer output should be valid input for composer
    And data structure should be consistent across components
    And no data transformation errors should occur
    And metadata should be preserved through pipeline

  @error-recovery
  Scenario: Pipeline handles partial failures gracefully
    Given 5 RSS feeds are configured
    And 2 of the feeds are temporarily unavailable
    When I execute the full pipeline
    Then articles should be fetched from available feeds
    And the pipeline should continue with available data
    And warnings should be logged for failed feeds
    And a post should still be generated if sufficient data exists
    And the final post should indicate the number of sources used

  @performance-baseline
  Scenario: Pipeline meets performance requirements
    Given 20 articles need to be processed
    When I execute the full pipeline
    Then fetching should complete within 30 seconds
    And summarization should complete within 60 seconds
    And composition should complete within 5 seconds
    And total pipeline time should be under 2 minutes
    And memory usage should remain under 500MB

  @data-quality
  Scenario: End-to-end data quality validation
    Given the pipeline processes real RSS feeds
    When the pipeline completes successfully
    Then all article URLs should be valid and accessible
    And all summaries should be coherent and relevant
    And the final post should be grammatically correct
    And hashtags should match article topics
    And no placeholder or mock data should remain

  @idempotency
  Scenario: Pipeline produces consistent results
    Given the same set of articles and configuration
    When I run the pipeline twice
    Then the week key should be identical
    And the article selection should be consistent
    And the post structure should be the same
    And hashtag selection should be deterministic

  @monitoring
  Scenario: Pipeline execution is observable
    When I execute the full pipeline
    Then start time should be recorded
    And end time should be recorded
    And component execution times should be tracked
    And success/failure status should be logged
    And error details should be captured if any
    And performance metrics should be available

  @post-merge-verification
  Scenario: Verify no regressions after new slice
    Given Slice 03 has been merged
    When I run the golden path test suite
    Then Slice 01 tests should still pass
    And Slice 02 tests should still pass
    And Slice 03 tests should pass
    And integration between all slices should work
    And no previous functionality should be broken

  @weekly-execution
  Scenario: Simulate weekly scheduled execution
    Given it is Thursday at 6:00 PM
    And articles have been published in the past week
    When the scheduled pipeline job executes
    Then articles from the past 7 days should be fetched
    And the most recent articles should be prioritized
    And a weekly digest post should be composed
    And the post should reference the current week
    And the post should be ready for LinkedIn publishing

  @realistic-content
  Scenario: Process realistic tech news articles
    Given real tech news from the past week
    When the pipeline processes these articles
    Then summaries should capture key technical points
    And the LinkedIn post should be engaging
    And hashtags should include relevant tech topics
    And the post should appeal to a tech/AI audience
    And URLs should link to actual articles

  @failure-scenarios
  Scenario: Handle complete AI provider failure
    Given both Claude API and Ollama are unavailable
    When I attempt to execute the pipeline
    Then the system should detect provider unavailability
    And an appropriate error should be raised
    And the error should suggest corrective actions
    And no partial or invalid post should be created
