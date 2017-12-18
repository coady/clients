from setuptools import setup

setup(
    name='clients',
    version='0.4',
    description='HTTP for lazy, impatient, hubristic humans.',
    long_description=open('README.rst').read(),
    author='Aric Coady',
    author_email='aric.coady@gmail.com',
    url='https://bitbucket.org/coady/clients',
    license='Apache Software License',
    packages=['clients'],
    install_requires=['requests>=2.4.2'],
    extras_require={':python_version>="3.5"': ['aiohttp']},
    python_requires='>=2.7',
    tests_require=['pytest-cov', 'pytest-httpbin'],
    keywords='requests sessions responses resources asyncio',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP :: Session',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
