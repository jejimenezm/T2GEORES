from distutils.core import setup

with open("README.md","r",encoding='utf-8') as fh:
    long_description=fh.read()

setup(
    name='T2GEORES',
    version='0.2.0',
    packages=['T2GEORES',],
    license='MIT',
    author='Erick Jiménez',
    author_email="erick@grogtp.is",
    url ="https://github.com/jejimenezm/T2GEORES",
    download_url='https://github.com/jejimenezm/T2GEORES/releases/download/T2GEORES-0.2.0/T2GEORES-0.2.0.tar.gz',
    long_description_content_type='text/markdown',
    long_description=long_description,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    install_requires=[
        'pandas>=1.1.3',
        'numpy>=1.14.5',
        'matplotlib>=3.3.2',
        'iapws>=1.5.2',
		'scipy>=1.5.3',
        'pyshp>=2.2.0',
        'pyvista>=0.33.3',
        'geopandas>=0.10.2'
    ],
)