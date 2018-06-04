from distutils.core import setup
from setuptools import find_packages

setup(
    name='gyda',
    version='0.1.0',
    packages=find_packages(),
    scripts=['scripts/ontology_terms_mapper.py'],
    url='',
    license='',
    author='',
    author_email='',
    description='',
    install_requires=['pandas==0.23.0', 'pronto==0.10.2', 'nltk==3.3']
)
