import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyterraform",
    version="0.0.1",
    author="Riccardo Scartozzi <risca>",
    author_email="info@risca.eu",
    description="A wrapper to terraform tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="terraform",
    url="https://github.com/terraform-great-modules/pyterraform",
    packages=setuptools.find_packages(),
    #entry_points={
    #    'console_scripts': [
    #        'my_project = my_project.__main__:main'
    #    ]
    #}
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
