from setuptools import setup

setup(
    name='clients',
    version='1.2',
    description='HTTP for humanitarians.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Aric Coady',
    author_email='aric.coady@gmail.com',
    url='https://github.com/coady/clients',
    project_urls={'Documentation': 'https://coady.github.io/clients'},
    license='Apache Software License',
    packages=['clients'],
    package_data={'clients': ['py.typed']},
    zip_safe=False,
    install_requires=['requests>=2.23', 'httpx>=0.15'],
    python_requires='>=3.6',
    tests_require=['pytest-cov', 'pytest-httpbin'],
    keywords='requests sessions responses resources asyncio',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: AsyncIO',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Internet :: WWW/HTTP :: Session',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Typing :: Typed',
    ],
)
