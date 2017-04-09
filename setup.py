from setuptools import setup, find_packages

version = '2.0'

INSTALL_REQUIRES = [
    'ansible',
    'awesome-slugify',
    'droplets',
    'Jinja2',
    'markdown',
    'pytaglib',
    'pyyaml',

    # https://github.com/sanpingz/mysql-connector/issues/3
    'mysql-connector==2.1.4',  # FU
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
            'migrate=cytunes.migrate:main',
            'publish=cytunes.publish:main',
        ],
    }
)
