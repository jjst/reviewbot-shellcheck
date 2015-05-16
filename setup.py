from setuptools import setup, find_packages


PACKAGE_NAME = "reviewbotshellcheck"
VERSION = "0.1.0"


setup(
    name=PACKAGE_NAME,
    version=VERSION,
    description=("A Review Bot tool that runs shellcheck, "
                 "a static analysis tool for bash/shell scripts"),
    author="Jeremie Jost",
    author_email="jeremiejost@gmail.com",
    packages=find_packages(),
    entry_points={
        'reviewbot.tools': [
            'shellcheck = reviewbotshellcheck.shellcheck:ShellCheckTool',
        ],
    },
    install_requires=[
        'reviewbot',
        'python-magic',
    ],
    tests_require=[
        'nose',
        'mock',
    ],
    test_suite = 'nose.collector',
)
