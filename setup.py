from setuptools import setup, find_packages

setup(
    name='lunyamwi',
    version='1.7',
    author='Martin Luther Bironga',
    description='Lunyamwi is a social media management and automation tool.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/lunyamwis/boostedchat-scrapper-dev.git',
    packages=find_packages(),
    install_requires=[
        'requests',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)