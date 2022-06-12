import os

import setuptools


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


setuptools.setup(name='WebForms',
                 version='1.0',
                 description='Python Web Forms Automation',
                 author='Peter Tolmanov',
                 author_email='ptolmanov@nes.ru',
                 packages=['webforms'],
                 install_requires=[
                     'dynaconf',
                     'click',
                     'selenium',
                     'python-telegram-handler',
                 ],
                 data_files=[('config', package_files('config'))],
                 include_package_data=True,
                 )
