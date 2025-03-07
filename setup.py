from setuptools import find_packages, setup

setup(
    name="geeadd",
    version="1.2.1",
    packages=find_packages(),
    data_files=[("", ["LICENSE"])],
    url="https://github.com/samapriya/gee_asset_manager_addon",
    install_requires=[
        "colorama>=0.4.6",
        "earthengine-api>=1.1.2",
        "jsbeautifier>=1.15.1",
        "logzero>=1.7.0",
        "packaging>=24.2",
        "requests>=2.32.3",
        "setuptools>=65.5.0",
        "tqdm>=4.66.5",
        "beautifulsoup4>=4.9.0",
    ],
    license="Apache 2.0",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    python_requires=">=3.7",
    author="Samapriya Roy",
    author_email="samapriya.roy@gmail.com",
    description="Google Earth Engine Batch Assets Manager with Addons",
    entry_points={
        "console_scripts": [
            "geeadd=geeadd.geeadd:main",
        ],
    },
)
