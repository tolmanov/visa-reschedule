import os
from pathlib import Path
from typing import List

import setuptools


def get_files_in_folder(folder_name: str) -> List[str]:
    return [str(Path(folder_name).joinpath(p.name))
            for p in Path(__file__).parent.joinpath(folder_name).glob('*.*')]


setuptools.setup(name='WebForms',
                 version='1.0',
                 description='Python Web Forms Automation',
                 author='Peter Tolmanov',
                 author_email='ptolmanov@nes.ru',
                 packages=setuptools.find_packages(),
                 install_requires=[
                     'click',
                     'dynaconf',
                     'notify-run',
                     'python-telegram-handler',
                     'selenium',
                 ],
                 data_files=[
                     ('config', get_files_in_folder('config')),
                     ('etc', get_files_in_folder('config/etc')),
                 ],
                 include_package_data=True,
                 )
