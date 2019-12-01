from setuptools import setup

setup(
    name='clients',
    version='1.1',
    description='HTTP for humanitarians.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Aric Coady',
    author_email='aric.coady@gmail.com',
    url='https://github.com/coady/clients',
    project_urls={'Documentation': 'https://clients.readthedocs.io'},
    license='Apache Software License',
    packages=['clients'],
    install_requires=['requests>=2.4.2'],
    extras_require={':python_version>="3.6"': ['httpx>=0.8']},
    python_requires='>=2.7',
    tests_require=['pytest>=3.7.2', 'pytest-cov', 'pytest-httpbin'],
    keywords='requests sessions responses resources asyncio',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: AsyncIO',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Internet :: WWW/HTTP :: Session',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
