from setuptools import setup, find_packages

version = '2.0'

INSTALL_REQUIRES = [
    'mysql-connector',
    'pytaglib',
    'pyyaml',
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
