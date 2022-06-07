from distutils.core import setup

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
      )
