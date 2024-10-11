# backend/setup.py

from setuptools import setup, find_packages

setup(
    name='chatclicks',
    version='0.4.1',  # Update the version for each release
    description='A package for handling chat clicks through websockets.',
    author='WillPiledriver',
    author_email='smifthsmurfth@gmail.com',
    url='https://github.com/WillPiledriver/chatclicks',
    packages=find_packages(),
    install_requires=[
        'python-socketio==5.5.0',
        'scikit-learn==1.2.2',
        'numpy==1.24.3',
        'aiohttp==3.8.4',
        'asyncio',
        'pydirectinput==1.1.1'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
)
