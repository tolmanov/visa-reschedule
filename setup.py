import os
from distutils.core import setup

def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths

extra_files = package_files('config')

setup(name='WebForms',
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
      package_data={'config': extra_files},
      include_package_data=True,
      )
