# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from setuptools import setup, find_packages
from os.path import dirname, join


def main():
    base_dir = dirname(__file__)
    setup(
        name='flaky',
        version='0.1.0',
        description='Plugin for nose that automatically reruns flaky tests.',
        long_description=open(join(base_dir, 'README.rst')).read(),
        author='Box',
        author_email='oss@box.com',
        url='https://github.com/box/flaky',
        license=open(join(base_dir, 'LICENSE')).read(),
        packages=find_packages(exclude=['test']),
        namespace_packages=[b'box', b'box.test'],
        test_suite='test',
        zip_safe=False,
        entry_points={
            'nose.plugins.0.10': [
                'flaky = box.test.flaky.flaky_plugin:FlakyPlugin'
            ]
        },
        install_requires=['nose'],
        keywords='nose plugin flaky tests rerun retry'
    )


if __name__ == '__main__':
    main()
