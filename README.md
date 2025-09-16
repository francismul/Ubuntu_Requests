# Ubuntu Image Fetcher

*"I am because we are" - Ubuntu Philosophy*

A mindful and respectful tool for collecting and sharing images from the web community, built with Python and inspired by Ubuntu principles of community, respect, and shared humanity.

## 🌟 Features

- **Community-Focused**: Connects respectfully with web resources
- **Interactive Mode**: User-friendly interface for entering image URLs
- **Progress Tracking**: Real-time download progress with tqdm progress bars
- **Graceful Error Handling**: Ubuntu-inspired error messages and recovery
- **Smart File Management**: Automatic filename sanitization and duplicate handling
- **Statistics Tracking**: Monitors total images fetched and data transferred
- **Respectful Connections**: Proper user agents and timeout handling

## 📋 Requirements

- Python 3.6+
- Dependencies listed in `requirements.txt`

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/francismul/Ubuntu_Requests.git
cd Ubuntu_Requests
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 💡 Usage

### Interactive Mode (Recommended)

Run the script and follow the prompts:

```bash
python index.py
```

You'll be greeted with:
```
Welcome to the Ubuntu Image Fetcher
A tool for mindfully collecting images from the web community
Ubuntu philosophy: 'I am because we are'

────────────────────────────────────────────────────────────
🔗 Please share the image URL (or 'quit' to exit):
```

Simply enter image URLs when prompted. The tool will:
- Validate the URL
- Download the image with a progress bar
- Save it to the `Fetched_Images/` directory
- Provide Ubuntu-themed feedback

### Example Session

```
🔗 Please share the image URL: https://example.com/image.jpg

🔗 Beginning Ubuntu connection ritual...
📝 Ubuntu naming wisdom: image.jpg
🌐 Connecting to community resource...
📊 Resource size: 2.45 MB
image.jpg: 100%|██████████| 2.45M/2.45M [00:01<00:00, 1.85MB/s]
✓ Ubuntu success: image.jpg
✓ Community resource saved: Fetched_Images/image.jpg
✓ Size: 2450.3 KB
✓ Connection strengthened. Community enriched.

🌟 Ubuntu mission accomplished with community spirit!
```

## 🏗️ Project Structure

```
Ubuntu_Requests/
├── index.py              # Main application script
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── Fetched_Images/      # Directory for downloaded images
    ├── ubuntu_image_1758032043.jpg
    ├── ubuntu_image_1758032103.jpg
    └── ...
```

## 🔧 How It Works

The `UbuntuImageFetcher` class embodies Ubuntu principles:

- **Community**: Establishes respectful connections to web resources
- **Respect**: Handles errors gracefully and honors server boundaries
- **Sharing**: Organizes downloaded images for community use
- **Practicality**: Provides real utility with mindful resource usage

### Key Components

- **URL Validation**: Ensures proper HTTP/HTTPS URLs
- **Filename Extraction**: Intelligently extracts and sanitizes filenames
- **Progress Monitoring**: Uses tqdm for visual download progress
- **Error Recovery**: Provides meaningful feedback for various error conditions
- **Statistics**: Tracks download metrics and community impact

## 🌍 Ubuntu Philosophy Integration

This tool incorporates Ubuntu values:

- **"I am because we are"**: Emphasizes community and shared humanity
- **Respectful Connections**: Mindful of server resources and user privacy
- **Graceful Degradation**: Handles failures with wisdom and patience
- **Community Building**: Organizes images for shared benefit

## 📊 Supported Image Formats

The tool supports common image formats:
- JPEG/JPG
- PNG
- GIF
- WebP
- BMP
- SVG
- ICO

## 🤝 Contributing

Contributions are welcome! Please:
1. Follow Ubuntu principles of respect and community
2. Test your changes thoroughly
3. Update documentation as needed
4. Maintain the project's mindful and respectful tone

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

Inspired by the Ubuntu philosophy of community and shared humanity. Special thanks to the open-source community for the excellent libraries that make this tool possible.

---

*"May our connections enrich the community"*