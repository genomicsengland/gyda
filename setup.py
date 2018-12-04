from distutils.core import setup
from setuptools import find_packages

setup(
    name='gyda',
    version='0.2.0-SNAPSHOT',
    packages=find_packages(),
    scripts=['scripts/gyda_cli.py'],
    url='',
    license='',
    author='',
    author_email='',
    description='',
    install_requires=[
        'pandas==0.23.0',
        'pronto==0.10.2',
        'nltk==3.3',
        'requests',
        'nose'
    ]
)
