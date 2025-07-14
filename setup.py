from setuptools import find_packages, setup

with open("requirements.txt") as f:
    required = f.read().splitlines()

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="vipwrap",
    version="0.1.5",
    description="Python package that allows interacting with VIP.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Jordan Maynor",
    author_email="jmaynor@pepsimidamerica.com",
    url="https://github.com/pepsimidamerica/vipwrap",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: The Unlicense (Unlicense)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12",
    install_requires=required,
)
