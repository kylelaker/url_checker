from setuptools import setup

setup(
    name='url_checker',
    version='0.1',
    packages=['url_checker'],
    install_requires=['pyyaml', 'requests'],
    url='https://github.com/kylelaker/url_checker',
    license='MIT',
    author='Kyle Laker',
    author_email='lakerka@dukes.jmu.edu',
    description='Checks if files can be downloaded, emails if they can\'t',
    entry_points={
        'console_scripts': ['url_checker = url_checker.url_checker:main']
    },
)
