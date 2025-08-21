"""Setup script for Benjamin Graham Stock Screener"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="benjamin-graham-screener",
    version="1.0.0",
    author="Graham Screener Contributors",
    author_email="noreply@example.com",
    description="Conservative stock screener using Benjamin Graham's value investing principles",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/benjamin-graham-screener",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "graham-scan=graham_scan:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml"],
    },
    keywords="stock screening, value investing, benjamin graham, financial analysis",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/benjamin-graham-screener/issues",
        "Source": "https://github.com/yourusername/benjamin-graham-screener",
        "Documentation": "https://github.com/yourusername/benjamin-graham-screener/blob/main/README.md",
    },
)