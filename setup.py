from setuptools import setup, find_packages

NAME = 'VideoLingo'
VERSION = '3.0.4'

with open('requirements.txt', encoding='utf-8') as f:
    requirements = f.read().splitlines()

setup(
    name=NAME,
    version=VERSION,
    python_requires='>=3.10,<3.14',
    packages=find_packages(include=[NAME, f'{NAME}.*']),
    install_requires=requirements
)
