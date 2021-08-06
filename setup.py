from setuptools import setup

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, '\docs', 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='PSID_Inequality',
    # other arguments omitted
    long_description=long_description,
    long_description_content_type='text/markdown'
)