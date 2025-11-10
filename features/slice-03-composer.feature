@slice03 @critical
Feature: LinkedIn Post Composer
  As a news aggregator system
  I want to compose engaging LinkedIn posts from article summaries
  So that I can share weekly tech digests with my network

  Background:
    Given the LinkedIn post composer is initialized

  @golden @happy-path
  Scenario: Compose weekly post from 5 article summaries
    Given 5 article summaries from the current week:
      | url                              | summary                                                           | source         | date       |
      | https://tc.com/gpt5              | OpenAI releases GPT-5 with 95% accuracy on logic tasks           | techcrunch.com | 2025-11-10 |
      | https://verge.com/quantum        | Google achieves quantum computing breakthrough                    | theverge.com   | 2025-11-09 |
      | https://wired.com/chips          | AI chip shortage intensifies with 18-month lead times            | wired.com      | 2025-11-08 |
      | https://ars.com/rust             | Linux kernel 6.7 ships with 15% drivers in Rust                  | arstechnica.com| 2025-11-07 |
      | https://vb.com/copilot           | Microsoft Copilot hits 1M enterprise customers                    | venturebeat.com| 2025-11-06 |
    When I compose a weekly LinkedIn post
    Then a post should be generated successfully
    And the post should start with an engaging headline containing an emoji
    And the post should include exactly 5 article highlights
    And each highlight should have a bullet point, summary, and link
    And the post should end with 5-8 relevant hashtags
    And the total character count should be under 3000

  @character-limit
  Scenario: Enforce LinkedIn 3000 character limit
    Given article summaries that would exceed 3000 characters
    When I compose a weekly post
    Then the post content should be truncated intelligently
    And the character count should be exactly 3000 or less
    And hashtags should still be included
    And no article highlight should be cut mid-sentence

  @article-selection
  Scenario: Select optimal number of articles (3-6 range)
    Given 10 available article summaries
    When I compose a weekly post
    Then the post should include between 3 and 6 articles
    And articles should be selected based on recency
    And the most recent articles should be prioritized
    And the post should indicate how many articles are included

  @headline-generation
  Scenario: Generate engaging headline with emoji
    Given article summaries from week 45 of 2025
    When I compose a weekly post
    Then the headline should include a tech-related emoji
    And the headline should mention "Tech & AI Weekly Digest"
    And the headline should include the week number
    And the headline should include the date range

  @hashtag-selection
  Scenario: Select 5-8 relevant hashtags
    Given summaries containing keywords: AI, machine learning, quantum, cloud
    When I compose a weekly post
    Then 5 to 8 hashtags should be included
    And hashtags should be relevant to article topics
    And hashtags should include "#AI" or "#MachineLearning"
    And hashtags should include "#TechNews"
    And hashtags should be placed at the end of the post
    And hashtags should be space-separated

  @week-key-generation
  Scenario: Generate ISO week key
    Given the current date is November 10, 2025
    When I compose a weekly post
    Then the week key should be in format "YYYY.Www"
    And the week key should be "2025.W45" for this date
    And the week key should be included in the post metadata

  @source-attribution
  Scenario: Include diverse sources in post
    Given summaries from TechCrunch, The Verge, and Wired
    When I compose a weekly post
    Then the post should include articles from multiple sources
    And each article highlight should show the source domain
    And source diversity should be tracked in metadata

  @validation
  Scenario: Reject composition with insufficient summaries
    Given only 2 article summaries are provided
    When I attempt to compose a weekly post
    Then the system should raise a validation error
    And the error should indicate minimum 3 articles required
    And no post should be generated

  @validation
  Scenario: Reject summaries without required fields
    Given summaries missing the "article_url" field
    When I attempt to compose a weekly post
    Then the system should raise a validation error
    And the error should indicate missing required field
    And all required fields should be listed in error message

  @formatting
  Scenario: Format article highlights consistently
    Given valid article summaries
    When I compose a weekly post
    Then each article highlight should follow the format:
      """
      📌 [Summary]
      🔗 [URL]
      """
    And bullet points should use emoji markers
    And URLs should be on separate lines
    And spacing should be consistent between highlights

  @metadata-tracking
  Scenario: Track post composition metadata
    Given 5 article summaries
    When I compose a weekly post
    Then metadata should include:
      | field           |
      | week_key        |
      | article_count   |
      | character_count |
      | hashtags        |
      | sources         |
      | timestamp       |
    And metadata should be returned with the post content

  @edge-cases
  Scenario: Handle summaries with special characters
    Given summaries containing emojis, quotes, and unicode
    When I compose a weekly post
    Then special characters should be preserved
    And the post should be valid UTF-8
    And character counting should handle multibyte characters
    And LinkedIn character limits should be respected

  @truncation-intelligence
  Scenario: Intelligently truncate long posts
    Given summaries that total 3500 characters
    When I compose a weekly post
    Then the composer should truncate at sentence boundaries
    And no article highlight should be partially cut
    And if an article doesn't fit, it should be omitted entirely
    And remaining content should remain coherent
    And ellipsis should indicate truncation if needed

  @date-range
  Scenario: Include date range in headline
    Given articles published between Nov 4-10, 2025
    When I compose a weekly post
    Then the headline should mention the date range
    And the format should be readable (e.g., "Nov 4-10")
    And the week year should be included (2025)
