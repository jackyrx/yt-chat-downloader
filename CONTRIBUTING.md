# Contributing to YouTube Chat Downloader

Thank you for considering contributing to this project! 

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/yt-chat-downloader.git
cd yt-chat-downloader
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest
```

## Code Style

This project follows PEP 8 style guidelines. Please format your code using Black:

```bash
black yt_chat_downloader/
```

And check with flake8:

```bash
flake8 yt_chat_downloader/
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Reporting Bugs

When reporting bugs, please include:

- Your Python version
- Operating system
- YouTube video ID (if applicable)
- Complete error message/traceback
- Steps to reproduce

## Feature Requests

Feature requests are welcome! Please open an issue describing:

- The use case
- Expected behavior
- Why this would be useful

## Code of Conduct

Be respectful and constructive in all interactions.

