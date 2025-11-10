@slice01 @critical
Feature: RSS Feed Fetcher
  As a news aggregator system
  I want to fetch and normalize articles from RSS feeds
  So that I can process consistent article data for summarization

  Background:
    Given the RSS feed fetcher is initialized

  @golden @happy-path
  Scenario: Successfully fetch articles from multiple RSS feeds
    Given the following RSS feed URLs:
      | url                                    |
      | https://techcrunch.com/feed/           |
      | https://www.theverge.com/rss/index.xml |
    When I fetch news from these sources
    Then I should receive a list of articles
    And each article should have the following fields:
      | field      |
      | title      |
      | link       |
      | source     |
      | date       |
      | content    |
    And the articles should be sorted by publication date in descending order

  @error-handling
  Scenario: Handle invalid RSS feed URL gracefully
    Given an invalid RSS feed URL "https://invalid-domain-xyz-12345.com/feed"
    When I attempt to fetch news from this source
    Then the system should not raise an exception
    And the result should be an empty list
    And an error should be logged with the message containing "Failed to fetch"

  @error-handling
  Scenario: Handle network timeout gracefully
    Given a RSS feed URL that times out
    When I attempt to fetch news from this source with a 5 second timeout
    Then the system should not raise an exception
    And the result should be an empty list
    And an error should be logged with timeout information

  @date-parsing
  Scenario: Parse various date formats correctly
    Given articles with different date formats:
      | format           | example                      |
      | RFC 822          | Mon, 10 Nov 2025 14:30:00 GMT |
      | ISO 8601         | 2025-11-10T14:30:00Z         |
      | Custom format    | November 10, 2025            |
    When I normalize these articles
    Then all dates should be converted to datetime objects
    And dates should be timezone-aware
    And all dates should use UTC timezone

  @normalization
  Scenario: Normalize article data structure
    Given a raw RSS feed entry with the following data:
      | field       | value                          |
      | title       | New AI Model Released          |
      | link        | https://example.com/ai-article |
      | description | Long article content here...   |
      | published   | Mon, 10 Nov 2025 14:30:00 GMT |
    When I normalize this entry
    Then the normalized article should have standardized field names
    And the "source" field should be extracted from the URL domain
    And the "content" field should contain the description
    And the "date" field should be a datetime object

  @edge-cases
  Scenario: Handle RSS feed with no articles
    Given a valid RSS feed URL with zero articles
    When I fetch news from this source
    Then the result should be an empty list
    And no errors should be logged

  @edge-cases
  Scenario: Handle RSS feed with malformed entries
    Given a RSS feed with some malformed entries
    When I fetch news from this source
    Then the system should skip malformed entries
    And valid entries should be included in the result
    And warnings should be logged for malformed entries

  @domain-extraction
  Scenario: Extract clean domain names from article URLs
    Given articles with URLs from different domains:
      | url                                      | expected_domain  |
      | https://techcrunch.com/2025/11/article   | techcrunch.com   |
      | https://www.theverge.com/tech/123        | theverge.com     |
      | https://arstechnica.com/science/article  | arstechnica.com  |
    When I extract domains from these URLs
    Then the extracted domains should match the expected values
    And the "www." prefix should be removed

  @performance
  Scenario: Fetch articles from multiple feeds in parallel
    Given 5 different RSS feed URLs
    When I fetch news from all sources simultaneously
    Then all articles should be fetched within 10 seconds
    And the results should be combined into a single list
    And articles should be sorted by date regardless of source
