"""
Setup script for backward compatibility.
Modern installations should use pyproject.toml.
"""

from setuptools import setup, find_packages

# Read the contents of README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="yt-chat-downloader",
    version="0.0.1",
    author="Dev Maker",
    author_email="devmaker@example.com",
    description="Download YouTube live chat replays and comments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/yt-chat-downloader",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Video",
    ],
    python_requires=">=3.7",
    install_requires=[
        "click>=8.0.0",
        "requests>=2.25.0",
        "yt-dlp>=2023.1.1",
        "python-dateutil>=2.8.0",
    ],
    entry_points={
        'console_scripts': [
            'yt-chat-downloader=yt_chat_downloader.__main__:main',
        ],
    },
    keywords="youtube chat downloader live-chat comments yt-dlp",
)

