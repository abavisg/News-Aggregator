@slice04 @critical
Feature: News Aggregation Scheduler
  As a news aggregator system
  I want to automatically schedule and execute weekly news aggregation tasks
  So that content is generated and published consistently without manual intervention

  Background:
    Given the scheduler is properly configured
    And the timezone is set to "Europe/London"

  @golden @happy-path
  Scenario: Schedule weekly preview and publish jobs
    Given a scheduler instance is created
    When I configure the scheduler with:
      | setting      | value     |
      | preview_day  | 3         |
      | preview_time | 18:00     |
      | publish_day  | 4         |
      | publish_time | 10:00     |
    And I schedule the jobs
    Then a preview job should be scheduled for Thursday at 18:00
    And a publish job should be scheduled for Friday at 10:00
    And both jobs should be in the scheduled jobs list

  @job-execution @preview
  Scenario: Execute preview job successfully
    Given the scheduler is running
    And it is Thursday at 18:00 Europe/London time
    And there are 15 available tech articles from RSS feeds
    When the preview job executes
    Then articles should be fetched from configured sources
    And 10 articles should be summarized using AI
    And a LinkedIn post should be composed
    And the job result should have status "success"
    And the job metadata should include:
      | field                | type    |
      | job_id              | string  |
      | job_type            | preview |
      | week_key            | string  |
      | articles_fetched    | integer |
      | articles_summarized | integer |
      | post_created        | boolean |
      | duration_seconds    | float   |

  @job-execution @publish
  Scenario: Execute publish job successfully
    Given the scheduler is running
    And it is Friday at 10:00 Europe/London time
    And a preview was generated yesterday
    When the publish job executes
    Then the full pipeline should execute
    And a new post should be composed for the current week
    And the job result should have status "success"
    And the post should be ready for publishing

  @pipeline-orchestration
  Scenario: Execute complete pipeline (fetch → summarize → compose)
    Given the scheduler needs to generate a weekly post
    When the pipeline executes for week "2025.W46"
    Then step 1 should fetch articles from RSS sources
    And step 2 should summarize each article using AI
    And step 3 should compose a LinkedIn post
    And the final result should contain the complete post
    And each pipeline step should be logged

  @error-handling @fetch-failure
  Scenario: Handle fetcher failure gracefully
    Given the scheduler is executing a job
    When the RSS fetcher fails with a network error
    Then the job should fail gracefully
    And the error should be logged with full context
    And the job result status should be "failed"
    And the error message should indicate "fetch failed"
    And the scheduler should remain operational

  @error-handling @summarizer-failure
  Scenario: Handle partial summarization failures
    Given the scheduler fetched 10 articles
    When 3 articles fail to summarize due to API errors
    Then the pipeline should continue with 7 successful summaries
    And failures should be logged
    And the composer should receive 7 summaries
    And a post should still be created
    And the job status should be "success"

  @error-handling @composer-failure
  Scenario: Handle composer failure
    Given the scheduler has summarized articles
    When the composer fails due to invalid input
    Then the job should fail with status "failed"
    And the error should include composer error details
    And previous pipeline steps should be logged as successful
    And no partial post should be created

  @graceful-shutdown
  Scenario: Gracefully shutdown scheduler
    Given the scheduler is running with active jobs
    When a shutdown signal is received
    Then the scheduler should wait for current jobs to complete
    And all jobs should finish within 30 seconds
    And the scheduler should stop cleanly
    And no jobs should be interrupted mid-execution

  @timezone-handling
  Scenario: Respect configured timezone
    Given the scheduler timezone is "America/New_York"
    And the preview_time is set to "18:00"
    When jobs are scheduled
    Then the preview job should run at 18:00 Eastern Time
    And timezone conversion should be handled correctly
    And logs should show times in the configured timezone

  @manual-execution
  Scenario: Manually trigger preview job
    Given the scheduler is configured but not started
    When I manually execute the preview job
    Then the pipeline should run immediately
    And a result should be returned synchronously
    And the week_key should be for the current week
    And the scheduler should not start as a daemon

  @manual-execution
  Scenario: Manually trigger publish job
    Given the scheduler is configured but not started
    When I manually execute the publish job
    Then the pipeline should run immediately
    And a post should be generated for the current week
    And the result should indicate "publish" job type

  @idempotency
  Scenario: Handle duplicate job execution safely
    Given a preview job was already executed for week "2025.W46"
    When the preview job is triggered again for the same week
    Then the pipeline should execute again
    And a new post should be generated
    And both executions should be logged separately
    And no data corruption should occur

  @job-isolation
  Scenario: Prevent overlapping job execution
    Given the scheduler has max_instances=1
    And a preview job is currently running
    When the same preview job triggers again
    Then the second job should be skipped
    And a warning should be logged
    And only one instance should execute

  @jobstore-persistence
  Scenario: Persist jobs using SQLite jobstore
    Given the scheduler uses SQLite jobstore
    When jobs are scheduled and the scheduler starts
    Then job definitions should be saved to SQLite database
    And jobs should survive scheduler restarts
    And the jobstore file should exist at configured path

  @jobstore-memory
  Scenario: Use in-memory jobstore for testing
    Given the scheduler uses memory jobstore
    When jobs are scheduled
    Then jobs should exist only in memory
    And no database file should be created
    And jobs should be lost after shutdown

  @week-key-generation
  Scenario: Generate correct week key for jobs
    Given the current date is November 14, 2025
    When a job executes
    Then the week_key should be "2025.W46"
    And the week_key should follow ISO 8601 format
    And the week_key should be included in all logs

  @configuration-validation
  Scenario: Validate scheduler configuration
    Given invalid configuration with preview_time="invalid"
    When I try to initialize the scheduler
    Then a SchedulerError should be raised
    And the error should indicate invalid time format
    And the scheduler should not start

  @logging
  Scenario: Log all scheduler events
    Given the scheduler is running
    When a preview job executes successfully
    Then logs should include:
      | event                | level |
      | scheduler_started    | INFO  |
      | job_scheduled        | INFO  |
      | job_started          | INFO  |
      | pipeline_step_start  | INFO  |
      | pipeline_step_end    | INFO  |
      | job_completed        | INFO  |
    And all logs should be structured JSON
    And logs should include week_key and job_type

  @resource-tracking
  Scenario: Track pipeline resource usage
    Given a job executes the full pipeline
    When the job completes
    Then the result should include:
      | metric              |
      | articles_fetched    |
      | articles_summarized |
      | api_tokens_used     |
      | duration_seconds    |
    And metrics should be accurate
    And metrics should be available for observability

  @startup-time
  Scenario: Fast scheduler startup
    Given the scheduler is not running
    When I start the scheduler
    Then startup should complete in under 5 seconds
    And all jobs should be scheduled
    And the scheduler should be ready to execute jobs
    And startup time should be logged

  @dry-run
  Scenario: Execute pipeline in dry-run mode
    Given the scheduler is in dry-run mode
    When a job executes
    Then the pipeline should simulate execution
    And no actual API calls should be made
    And no post should be published
    And the result should indicate "dry_run: true"
    And logs should show dry-run mode is active
