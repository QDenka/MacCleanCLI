"""
Setup script for macOS Cleaner
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="MacCleanCLI",
    version="1.0.0",
    author="QDenka",
    author_email="denis@kaban.dev",
    description="A beautiful console application for cleaning and optimizing macOS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/qdenka/MacCleanCLI",
    project_urls={
        "Bug Tracker": "https://github.com/qdenka/MacCleanCLI/issues",
        "Documentation": "https://github.com/qdenka/MacCleanCLI/wiki",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    packages=find_packages(),
    py_modules=['main'],
    python_requires=">=3.10",
    install_requires=[
        "rich>=13.7.0",
        "psutil>=5.9.0",
        "click>=8.1.0",
    ],
    entry_points={
        "console_scripts": [
            "macos-cleaner=main:main",
            "mclean=main:main",  # Short alias
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.md"],
    },
)