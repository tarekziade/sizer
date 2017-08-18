from setuptools import setup, find_packages

install_requires = []
description = ''

for file_ in ('README', 'CHANGELOG'):
    with open('%s.rst' % file_) as f:
        description += f.read() + '\n\n'


classifiers = ["Programming Language :: Python",
               "License :: OSI Approved :: Apache Software License",
               "Development Status :: 5 - Production/Stable",
               "Programming Language :: Python :: 3 :: Only",
               "Programming Language :: Python :: 3.5",
               "Programming Language :: Python :: 3.6"]


setup(name='molotov',
      version="0.13",
      url='https://github.com/tarekziade/sizer',
      packages=find_packages(),
      long_description=description.strip(),
      description=("AWS Sizing tool"),
      author="Tarek Ziade",
      author_email="tarek@ziade.org",
      include_package_data=True,
      zip_safe=False,
      classifiers=classifiers,
      install_requires=install_requires)
