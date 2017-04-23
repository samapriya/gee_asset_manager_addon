from setuptools import setup
from setuptools import find_packages
def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='geeadd',
    version='0.1.2',
    packages=find_packages(),
    package_data={'geeadd': ['logconfig.json']},
    url='https://github.com/samapriya/gee_asset_manager_addon',
    license='Apache 2.0',
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: GIS',
    ),
    author='Samapriya Roy',
    author_email='samapriya.roy@gmail.com',
    description='Google Earth Engine Batch Assets Manager with Addons',
    entry_points={
        'console_scripts': [
            'geeadd=geeadd.geeadd:main',
        ],
    },
)
