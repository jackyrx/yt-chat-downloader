# Installation & Publishing Guide

## For End Users

### Install from PyPI (once published)

```bash
pip install yt-chat-downloader
```

### Install from GitHub

```bash
pip install git+https://github.com/yourusername/yt-chat-downloader.git
```

### Install from Source

```bash
git clone https://github.com/yourusername/yt-chat-downloader.git
cd yt-chat-downloader
pip install -e .
```

## For Developers

### Development Installation

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

3. Install in editable mode with dev dependencies:
```bash
pip install -e ".[dev]"
```

### Verify Installation

Test the command-line tool:
```bash
yt-chat-downloader --help
```

Test the Python API:
```python
from yt_chat_downloader import YouTubeChatDownloader
downloader = YouTubeChatDownloader()
print("Installation successful!")
```

## Publishing to PyPI

### Prerequisites

1. Create accounts on:
   - PyPI: https://pypi.org/account/register/
   - TestPyPI: https://test.pypi.org/account/register/

2. Install build tools:
```bash
pip install --upgrade build twine
```

### Step 1: Build the Package

```bash
python -m build
```

This creates:
- `dist/yt_chat_downloader-1.0.0-py3-none-any.whl` (wheel)
- `dist/yt-chat-downloader-1.0.0.tar.gz` (source distribution)

### Step 2: Test on TestPyPI (Optional but Recommended)

Upload to TestPyPI:
```bash
python -m twine upload --repository testpypi dist/*
```

Test installation from TestPyPI:
```bash
pip install --index-url https://test.pypi.org/simple/ yt-chat-downloader
```

### Step 3: Upload to PyPI

```bash
python -m twine upload dist/*
```

You'll be prompted for your PyPI username and password.

### Step 4: Verify Publication

```bash
pip install yt-chat-downloader
```

### Using API Tokens (Recommended)

1. Generate API token on PyPI (Account Settings → API tokens)

2. Create `~/.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE

[testpypi]
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

3. Upload:
```bash
python -m twine upload dist/*
```

## Version Management

Update version in:
- `pyproject.toml` → `[project] version`
- `setup.py` → `version`
- `yt_chat_downloader/__init__.py` → `__version__`

## Creating a Release

1. Update version numbers
2. Update CHANGELOG (if you have one)
3. Commit changes
4. Tag the release:
```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```
5. Build and publish to PyPI

## Troubleshooting

### "Package already exists"
Increment the version number and rebuild.

### Import errors after installation
Make sure you're not in the package directory when testing:
```bash
cd ~
python -c "from yt_chat_downloader import YouTubeChatDownloader"
```

### Command not found
Reinstall or check your PATH:
```bash
pip uninstall yt-chat-downloader
pip install yt-chat-downloader
```

## Continuous Integration (CI/CD)

Consider setting up GitHub Actions to automatically:
- Run tests on push
- Build package
- Publish to PyPI on release tags

Example `.github/workflows/publish.yml`:
```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v2
      with:
        python-version: '3.x'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

