from setuptools import setup
from setuptools import find_packages

setup(
    name='geeadd',
    version='0.5.3',
    packages=['geeadd'],
    data_files=[("",["LICENSE"])],
    url='https://github.com/samapriya/gee_asset_manager_addon',
    install_requires=['earthengine-api>=0.1.222','requests>=2.22.0','logzero>=1.5.0',
                      'beautifulsoup4>=4.9.0'],
    license='Apache 2.0',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
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







