from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-usage-tracker",
    version="0.1.0",
    author="Michael Verrilli",
    author_email="",
    description="Track AI API usage and costs across multiple providers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mverrilli/ai-usage-tracker-cli",
    project_urls={
        "Sponsor": "https://github.com/sponsors/mverrilli",
        "Source": "https://github.com/mverrilli/ai-usage-tracker-cli",
        "Tracker": "https://github.com/mverrilli/ai-usage-tracker-cli/issues",
        "Documentation": "https://github.com/mverrilli/ai-usage-tracker-cli#readme",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "sqlite3",
    ],
    entry_points={
        "console_scripts": [
            "ai-usage-tracker=ai_usage_tracker.cli:main",
        ],
    },
)