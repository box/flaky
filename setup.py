# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from os.path import dirname, join
import sys
from setuptools.command.test import test as TestCommand
from setuptools import setup, find_packages


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
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: Implementation :: CPython',
    'Programming Language :: Python :: Implementation :: PyPy',
    'Operating System :: OS Independent',
    'Operating System :: POSIX',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: MacOS :: MacOS X',
]


class Tox(TestCommand):
    user_options = [(b'tox-args=', b'a', 'Arguments to pass to tox')]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.tox_args = None

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import shlex
        import tox
        args = self.tox_args
        if args:
            args = shlex.split(self.tox_args)
        errno = tox.cmdline(args=args)
        sys.exit(errno)


def main():
    base_dir = dirname(__file__)
    setup(
        name='flaky',
        version='3.4.0',
        description='Plugin for nose or py.test that automatically reruns flaky tests.',
        long_description=open(join(base_dir, 'README.rst')).read(),
        author='Box',
        author_email='oss@box.com',
        url='https://github.com/box/flaky',
        license=open(join(base_dir, 'LICENSE')).read(),
        packages=find_packages(exclude=['test*']),
        test_suite='test',
        tests_require=['tox'],
        cmdclass={'test': Tox},
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
