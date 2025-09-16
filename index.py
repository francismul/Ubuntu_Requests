"""
Ubuntu-Inspired Image Fetcher
"I am because we are" - Ubuntu Philosophy

A mindful tool for collecting and sharing images from the web community,
built with respect for connections and graceful error handling.
"""

import requests
import os
import time
from urllib.parse import urlparse, unquote
from pathlib import Path
from tqdm import tqdm


class UbuntuImageFetcher:
    """
    Image fetcher embodying Ubuntu principles:
    - Community: Connects to the web community
    - Respect: Handles errors gracefully
    - Sharing: Organizes images for community use
    - Practicality: Serves real needs
    """

    def __init__(self, directory_name="Fetched_Images"):
        """Initialize the fetcher with Ubuntu wisdom."""
        self.directory_name = directory_name
        self.session = requests.Session()
        # Set a respectful user agent
        self.session.headers.update({
            'User-Agent': 'Ubuntu-Image-Fetcher/1.0 (Respectful Community Tool)'
        })
        self.total_fetched = 0
        self.total_size = 0

    def create_directory(self):
        """Create the directory with Ubuntu principle of sharing."""
        try:
            os.makedirs(self.directory_name, exist_ok=True)
            if not hasattr(self, '_directory_created'):
                print(f"📁 Community space prepared: {self.directory_name}/")
                self._directory_created = True
            return True
        except PermissionError:
            print(
                f"❌ Permission denied: Cannot create directory '{self.directory_name}'")
            print("   Ubuntu wisdom: Respect system boundaries")
            return False
        except Exception as e:
            print(f"❌ Unexpected error creating directory: {e}")
            return False

    def extract_filename_from_url(self, url):
        """Extract filename from URL with Ubuntu practicality."""
        try:
            # Parse the URL and get the path
            parsed_url = urlparse(url)
            path = unquote(parsed_url.path)  # Decode URL encoding

            # Extract filename from path
            filename = os.path.basename(path)

            # If no filename or no extension, generate one
            if not filename or '.' not in filename:
                # Try to get extension from URL or use default
                if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']):
                    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
                        if ext in url.lower():
                            filename = f"ubuntu_image_{int(time.time())}{ext}"
                            break
                else:
                    filename = f"ubuntu_image_{int(time.time())}.jpg"

            # Ensure filename is safe for filesystem
            filename = self.sanitize_filename(filename)
            return filename

        except Exception:
            # Ubuntu principle: Graceful fallback
            return f"ubuntu_image_{int(time.time())}.jpg"

    def sanitize_filename(self, filename):
        """Sanitize filename with Ubuntu respect for system conventions."""
        # Remove or replace problematic characters
        problematic_chars = '<>:"/\\|?*'
        for char in problematic_chars:
            filename = filename.replace(char, '_')

        # Limit filename length (Ubuntu practicality)
        name, ext = os.path.splitext(filename)
        if len(name) > 100:
            name = name[:100]

        return name + ext

    def validate_url(self, url):
        """Validate URL with Ubuntu wisdom."""
        if not url.strip():
            return False, "Empty URL - Ubuntu wisdom: Share meaningful connections"

        if not url.startswith(('http://', 'https://')):
            return False, "URL must start with http:// or https:// - Ubuntu principle: Clear communication"

        # Check for common image extensions
        image_extensions = [
            '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.ico']
        url_lower = url.lower()

        # Allow URLs that might serve images even without explicit extensions
        return True, "URL validated with Ubuntu trust"

    def fetch_image(self, url):
        """Fetch image with Ubuntu principles of respect and community."""
        print(f"🌐 Connecting to community resource...")
        print(f"   URL: {url}")

        try:
            # Make request with timeout (respectful of resources)
            response = self.session.get(url, timeout=30, stream=True)

            # Check for HTTP errors
            if response.status_code == 404:
                return None, "Resource not found in the community (404) - Ubuntu acceptance: Not all paths exist"
            elif response.status_code == 403:
                return None, "Access respectfully denied (403) - Ubuntu wisdom: Honor boundaries"
            elif response.status_code == 429:
                return None, "Community requests patience (429) - Ubuntu principle: Mindful consumption"
            elif not response.ok:
                return None, f"Community connection issue (HTTP {response.status_code}) - Ubuntu resilience: Try again later"

            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if not any(img_type in content_type for img_type in ['image/', 'application/octet-stream']):
                # Still try to download - some servers don't set correct content-type
                print(
                    f"⚠️  Content type '{content_type}' may not be an image, but continuing with Ubuntu optimism...")

            # Get content length for progress indication
            content_length = response.headers.get('content-length')
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                print(f"📊 Resource size: {size_mb:.2f} MB")

                # Ubuntu practicality: Warn about large files
                if size_mb > 50:
                    print(
                        "⚠️  Large resource detected - Ubuntu consideration: Be mindful of bandwidth")

            return response, "Community connection established with Ubuntu gratitude"

        except requests.exceptions.Timeout:
            return None, "Connection timed out - Ubuntu patience: The community may be busy"
        except requests.exceptions.ConnectionError:
            return None, "Cannot reach community resource - Ubuntu understanding: Networks have limitations"
        except requests.exceptions.RequestException as e:
            return None, f"Community connection challenge: {e} - Ubuntu resilience: Try again with wisdom"
        except Exception as e:
            return None, f"Unexpected challenge: {e} - Ubuntu acceptance: Learn from all experiences"

    def save_image(self, response, filename):
        """Save image with Ubuntu sharing spirit."""
        filepath = os.path.join(self.directory_name, filename)

        # Check if file already exists
        if os.path.exists(filepath):
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(f"{self.directory_name}/{base}_{counter}{ext}"):
                counter += 1
            filename = f"{base}_{counter}{ext}"
            filepath = os.path.join(self.directory_name, filename)
            print(f"🔄 File exists, Ubuntu wisdom suggests: {filename}")

        try:
            content_length = response.headers.get('content-length')
            if content_length:
                total_size = int(content_length)
            else:
                total_size = None
            
            bytes_downloaded = 0
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                with open(filepath, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:  # Filter out keep-alive chunks
                            file.write(chunk)
                            bytes_downloaded += len(chunk)
                            pbar.update(len(chunk))

            # Update statistics
            self.total_fetched += 1
            self.total_size += bytes_downloaded

            # Ubuntu celebration of success
            size_kb = bytes_downloaded / 1024
            print(f"✓ Ubuntu success: {filename}")
            print(f"✓ Community resource saved: {filepath}")
            print(f"✓ Size: {size_kb:.1f} KB")
            print(f"✓ Connection strengthened. Community enriched.")

            return True, filename

        except PermissionError:
            return False, f"Permission denied saving to {filepath} - Ubuntu respect: Honor system permissions"
        except OSError as e:
            return False, f"System challenge saving image: {e} - Ubuntu adaptability: Try different approach"
        except Exception as e:
            return False, f"Unexpected challenge: {e} - Ubuntu learning: Grow from difficulties"

    def fetch_single_image(self, url):
        """Fetch a single image with complete Ubuntu workflow."""
        print("🔗 Beginning Ubuntu connection ritual...")

        # Validate URL
        is_valid, message = self.validate_url(url)
        if not is_valid:
            print(f"❌ {message}")
            return False

        # Create directory
        if not self.create_directory():
            return False

        # Extract filename
        filename = self.extract_filename_from_url(url)
        print(f"📝 Ubuntu naming wisdom: {filename}")

        # Fetch the image
        response, message = self.fetch_image(url)
        print(f"📡 {message}")

        if response is None:
            print(f"❌ {message}")
            return False

        # Save the image
        success, result = self.save_image(response, filename)
        if success:
            print("🌟 Ubuntu mission accomplished with community spirit!")
            return True
        else:
            print(f"❌ {result}")
            return False

    def interactive_mode(self):
        """Interactive mode embodying Ubuntu dialogue."""
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
                success = self.fetch_single_image(url)

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
        print(f"Images gathered: {self.total_fetched}")
        if self.total_size > 0:
            total_mb = self.total_size / (1024 * 1024)
            print(f"Community resources shared: {total_mb:.2f} MB")
        print("Ubuntu blessing: 'May our connections enrich the community'")
        print("="*60)


def main():
    """Main function with Ubuntu hospitality."""
    try:
        fetcher = UbuntuImageFetcher()
        fetcher.interactive_mode()
    except Exception as e:
        print(f"Ubuntu wisdom in challenge: {e}")
        print("Remember: Every ending is a new beginning")


if __name__ == "__main__":
    main()
