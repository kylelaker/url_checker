from setuptools import setup

setup(
    name='url_checker',

    version='1.0.0',

    packages=['url_checker'],

    url='https://github.com/kylelaker/url_checker',

    license='MIT',

    author='Kyle Laker',

    author_email='lakerka@dukes.jmu.edu',

    description='Checks if files can be downloaded, emails if they can\'t',

    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
    ],

    entry_points={
        'console_scripts': ['url_checker = url_checker.url_checker:main']
    },

    install_requires=[
        'pyyaml>=3.13,<4.0',
        'requests>=2.19,<3.0',
    ],
)
