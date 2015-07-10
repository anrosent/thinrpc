from distutils.core import setup
import os.path

README = os.path.join(os.path.dirname(__file__), 'README.md')

version = '0.1.23'

with open(README) as fp:
    longdesc = fp.read()

setup(name='thinrpc',
    include_package_data=True,
    version=version,
    description='A Lightweight RPC framework for Python',
    long_description=longdesc,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Topic :: Software Development',
        'Intended Audience :: Developers'
    ],
    author='Anson Rosenthal',
    author_email='anson.rosenthal@gmail.com',
    license='MIT License',
    url='https://github.com/anrosent/thinrpc.git',
    packages=['thinrpc']
)

