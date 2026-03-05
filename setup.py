from setuptools import setup, find_packages

setup(
    name="git-weekly",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["click>=8.0", "rich>=13.0"],
    entry_points={"console_scripts": ["git-weekly=git_weekly.cli:main"]},
)
