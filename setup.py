"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['sss.py']
DATA_FILES = ['English.lproj']
OPTIONS = dict(py2app=dict(plist='Info.plist'))

setup(
    app=APP,
    data_files=DATA_FILES,
    options=OPTIONS,
    setup_requires=['py2app'],
)
