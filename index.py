"""
Ubuntu-Inspired Image Fetcher
"I am because we are" - Ubuntu Philosophy

A mindful tool for collecting and sharing images from the web community,
built with respect for connections and graceful error handling.
"""

from ubuntu_fetcher_core import UbuntuImageFetcher


def interactive_mode():
    """Interactive mode embodying Ubuntu dialogue."""
    fetcher = UbuntuImageFetcher()
    print("Welcome to the Ubuntu Image Fetcher")
    print("A tool for mindfully collecting images from the web community")
    print("Ubuntu philosophy: 'I am because we are'\n")

    while True:
        try:
            print("─" * 60)
            url = input(
                "🔗 Please share the image URL (or 'quit' to exit): ").strip()

            if url.lower() in ['quit', 'exit', 'q']:
                break

            if not url:
                print(
                    "Ubuntu patience: Please provide a URL to continue our journey together")
                continue

            print()  # Ubuntu spacing for clarity
            success = fetcher.fetch_single_image(url)

            if success:
                print(
                    "\n🤝 Ubuntu gratitude: Thank you for strengthening our community")
            else:
                print("\n💪 Ubuntu resilience: Every attempt teaches us wisdom")

            print()

        except KeyboardInterrupt:
            print("\n\n🙏 Ubuntu farewell: Connection interrupted with understanding")
            break
        except Exception as e:
            print(f"\n❌ Ubuntu learning opportunity: {e}")
            print("Ubuntu persistence: Let's try again with renewed wisdom")

    # Ubuntu summary
    print("\n" + "="*60)
    print("🌍 Ubuntu Community Summary")
    print(f"Images gathered: {fetcher.total_fetched}")
    if fetcher.total_size > 0:
        total_mb = fetcher.total_size / (1024 * 1024)
        print(f"Community resources shared: {total_mb:.2f} MB")
    print("Ubuntu blessing: 'May our connections enrich the community'")
    print("="*60)


def main():
    """Main function with Ubuntu hospitality."""
    try:
        interactive_mode()
    except Exception as e:
        print(f"Ubuntu wisdom in challenge: {e}")
        print("Remember: Every ending is a new beginning")


if __name__ == "__main__":
    main()
