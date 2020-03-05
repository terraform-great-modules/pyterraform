"""Packaging information"""
import os
import codecs
import re
import setuptools

CWD = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
    """Read subfile"""
    with codecs.open(os.path.join(CWD, *parts), 'r') as file_:
        return file_.read()

def find_version(*file_paths):
    """Search for VERSION definition"""
    version_file = read(*file_paths)
    version_match = re.search(r"^VERSION = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

def read_description():
    """Pip package description"""
    return read("README.md")

setuptools.setup(
    name="pyterraform",
    version=find_version("pyterraform", "constants.py"),
    author="Riccardo Scartozzi <risca>",
    author_email="info@risca.eu",
    description="A wrapper to terraform tool",
    long_description=read_description(),
    long_description_content_type="text/markdown",
    keywords="terraform",
    url="https://github.com/terraform-great-modules/pyterraform",
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'pyterraform = pyterraform.__main__:main'
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "Operating System :: POSIX :: Linux"
    ],
    python_requires='>=3.6',
    install_requires=['boto3',
                      'colorlog',
                      'schema',
                      'pyyaml',
                      'requests',
                      'deep_merge']
)
