from setuptools import setup, find_packages

NAME = 'VideoLingo'
VERSION = '3.0.0'

with open('requirements.txt', encoding='utf-8') as f:
    requirements = f.read().splitlines()

setup(
    name=NAME,
    version=VERSION,
    packages=find_packages(include=[NAME, f'{NAME}.*']),
    install_requires=requirements
)
