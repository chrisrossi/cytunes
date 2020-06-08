from setuptools import setup, find_packages

version = '2.0'

INSTALL_REQUIRES = [
    'ansible',
    'droplets',
    'Jinja2',
    'markdown',
    'pyyaml',
]

setup(
    name='cytunes',
    version=version,
    description="",
    packages=find_packages(),
    zip_safe=False,
    install_requires=INSTALL_REQUIRES,
    entry_points={
        'console_scripts': [
            'publish=cytunes.publish:main',
        ],
    }
)
