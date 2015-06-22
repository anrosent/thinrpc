from distutils.core import setup
import os.path

README = os.path.join(os.path.dirname(__file__), 'README')

version = '0.1.8'

with open(README) as fp:
    longdesc = fp.read()

setup(name='thinrpc',
    version=version,
    description='Thin RPC framework',
    long_description=longdesc,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
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
    url='https://github.com/anrosent/pyrpc.git',
    py_modules=['pyrpc'],
)

