from distutils.core import setup

with open("README.md","r",encoding='utf-8') as fh:
    long_description=fh.read()

setup(
    name='T2GEORES',
    version='0.1.5',
    packages=['T2GEORES',],
    license='MIT',
    author='Erick Jiménez',
    author_email="erick@grogtp.is",
    url ="https://github.com/jejimenezm/T2GEORES",
    download_url='https://github.com/jejimenezm/T2GEORES/releases/download/T2GEORES-0.1.2/T2GEORES-0.1.2.tar.gz',
    long_description=long_description,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'pandas>=1.1.3',
        'numpy>=1.14.5',
        'matplotlib>=3.3.2',
        'iapws>=1.5.2',
		'scipy>=1.5.3'
    ],
)