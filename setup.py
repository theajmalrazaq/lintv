from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lintv",
    version="1.0.0",
    author="Ajmal Razaq",
    author_email="theajmalrazaq@gmail.com",
    description="Android TV Remote Control & Screen Streaming Center via Tailscale & ADB",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/theajmalrazaq/lintv",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Video",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "lintv=lintv.cli:main",
        ],
    },
    include_package_data=True,
)
