# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from setuptools import setup, find_packages
from os.path import dirname, join

CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Apache Software License',
    'Topic :: Software Development :: Testing',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: Implementation :: CPython',
    'Programming Language :: Python :: Implementation :: PyPy',
    'Operating System :: OS Independent',
    'Operating System :: POSIX',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: MacOS :: MacOS X',
]


def main():
    base_dir = dirname(__file__)
    setup(
        name='flaky',
        version='1.1.0',
        description='Plugin for nose or py.test that automatically reruns flaky tests.',
        long_description=open(join(base_dir, 'README.rst')).read(),
        author='Box',
        author_email='oss@box.com',
        url='https://github.com/box/flaky',
        license=open(join(base_dir, 'LICENSE')).read(),
        packages=find_packages(exclude=['test']),
        test_suite='test',
        tests_require=['pytest', 'nose'],
        zip_safe=False,
        entry_points={
            'nose.plugins.0.10': [
                'flaky = flaky.flaky_nose_plugin:FlakyPlugin'
            ],
            'pytest11': [
                'flaky = flaky.flaky_pytest_plugin'
            ]
        },
        keywords='nose pytest plugin flaky tests rerun retry',
        classifiers=CLASSIFIERS,
    )


if __name__ == '__main__':
    main()
