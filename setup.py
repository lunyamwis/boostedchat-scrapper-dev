from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="lunyamwi",
    version="1.0.21",
    author="Martin Luther Bironga",
    description="Lunyamwi is a social media management and automation tool.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lunyamwis/boostedchat-scrapper-dev.git",
    packages=find_packages(),
    install_requires=[
        "requests",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
