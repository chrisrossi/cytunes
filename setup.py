from setuptools import setup, find_packages

version = '2.0'

INSTALL_REQUIRES = [
    'mysql-connector==2.1.4',  # Bug in 2.2.3
    'pytaglib',
    'pyyaml',
    'awesome-slugify',
]

setup(name='cytunes',
      version=version,
      description="",
      packages=find_packages(),
      zip_safe=False,
      install_requires=INSTALL_REQUIRES,
      entry_points={
          'console_scripts': [
              'migrate=cytunes.migrate:main',
              ],
          }
      )
