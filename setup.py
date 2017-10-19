from setuptools import setup
from setuptools import find_packages

setup(
    name='geeadd',
    version='0.2.0',
    packages=['geeadd'],
    package_data={'geeadd': ['logconfig.json']},
    url='https://github.com/samapriya/gee_asset_manager_addon',
    install_requires=['earthengine_api >= 0.1.87','requests >= 2.10.0','retrying >= 1.3.3','clipboard>=0.0.4','beautifulsoup4 >= 4.5.1',
                      'requests_toolbelt >= 0.7.0','pytest >= 3.0.0','future >= 0.16.0','google-cloud-storage >= 1.1.1'],
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
