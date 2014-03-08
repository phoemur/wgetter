from distutils.core import setup
            
setup(
    name='pyget',
    version='0.1',
    author='Fernando Giannasi <phoemur@gmail.com>',
    url='https://github.com/phoemur/pyget',
    download_url = 'https://github.com/phoemur/pyget/tarball/0.1',

    description="Another command line download utility written in python",
    license="Public Domain",
    classifiers=[
        'Environment :: Console',
        'License :: Public Domain',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
        'Topic :: Utilities',
    ],

    py_modules=['pyget'],

    long_description='''Pyget is another command line download utility written completely in python.
It is based on python-wget (https://bitbucket.org/techtonik/python-wget/src)
with some improvements.

It works on python >= 2.6 or python >=3.0
Runs on Windows or Linux or Mac ''',
)
