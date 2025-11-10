"""
Integration demo: Fetch → Summarize → Compose pipeline

This demonstrates the full pipeline from Slices 01, 02, and 03 working together.
Note: This is a demo script, not an automated test.
"""

from datetime import datetime


def demo_full_pipeline():
    """Demonstrate the complete news aggregation pipeline"""

    print("=" * 70)
    print("NEWS AGGREGATOR - FULL PIPELINE DEMO")
    print("=" * 70)
    print()

    # Mock data for demo (in real scenario, this would come from fetcher + summarizer)
    mock_summaries = [
        {
            "article_url": "https://techcrunch.com/2025/11/10/openai-gpt5",
            "summary": "OpenAI releases GPT-5 with breakthrough reasoning capabilities, achieving 95% accuracy on complex logic tasks.",
            "source": "techcrunch.com",
            "published_at": datetime(2025, 11, 10, 10, 0, 0),
            "tokens_used": 150,
            "provider": "claude",
        },
        {
            "article_url": "https://www.theverge.com/2025/11/09/quantum-computing",
            "summary": "Google announces quantum computing breakthrough with error correction enabling practical quantum computers.",
            "source": "theverge.com",
            "published_at": datetime(2025, 11, 9, 14, 30, 0),
            "tokens_used": 140,
            "provider": "claude",
        },
        {
            "article_url": "https://www.wired.com/2025/11/08/ai-chip-shortage",
            "summary": "Global AI chip shortage intensifies with lead times extending to 18 months for H100 GPUs.",
            "source": "wired.com",
            "published_at": datetime(2025, 11, 8, 9, 15, 0),
            "tokens_used": 135,
            "provider": "claude",
        },
        {
            "article_url": "https://arstechnica.com/2025/11/07/rust-linux-kernel",
            "summary": "Linux kernel 6.7 ships with 15% of drivers in Rust, marking major milestone in systems programming.",
            "source": "arstechnica.com",
            "published_at": datetime(2025, 11, 7, 16, 45, 0),
            "tokens_used": 120,
            "provider": "claude",
        },
        {
            "article_url": "https://venturebeat.com/2025/11/06/microsoft-copilot",
            "summary": "Microsoft Copilot reaches 1 million enterprise customers, generating $1.5B in annual revenue.",
            "source": "venturebeat.com",
            "published_at": datetime(2025, 11, 6, 11, 20, 0),
            "tokens_used": 145,
            "provider": "claude",
        },
    ]

    print("📰 Step 1: Fetch News (Slice 01)")
    print(f"   Fetched {len(mock_summaries)} articles from RSS feeds")
    print()

    print("🤖 Step 2: Summarize Articles (Slice 02)")
    print(f"   Generated AI summaries using Claude API")
    print()

    print("✍️  Step 3: Compose LinkedIn Post (Slice 03)")
    print()

    # Import and use composer
    from src.core.composer import compose_weekly_post

    post = compose_weekly_post(mock_summaries)

    print("📊 Post Metadata:")
    print(f"   Week: {post['week_key']}")
    print(f"   Articles: {post['article_count']}")
    print(f"   Characters: {post['character_count']}/3000")
    print(f"   Sources: {', '.join(post['sources'])}")
    print(f"   Hashtags: {len(post['hashtags'])}")
    print()

    print("=" * 70)
    print("GENERATED LINKEDIN POST")
    print("=" * 70)
    print()
    print(post['content'])
    print()
    print("=" * 70)
    print("✅ Pipeline completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    demo_full_pipeline()
