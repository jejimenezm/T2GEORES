# T2GEORES

It is a library to manage input and output files during the development of numerical models for geothermal reservoirs using TOUGH2. The Pypi repository can be found on [T2GEORES](https://pypi.org/project/T2GEORES/).

Currently the library uses a fix scheme of directories to prevent the user to indicate the input/output file location needed on many functions. The first level of the structure is the following:

```
T2GEORES/
/calib
/input
/mesh
/model
/ouput
/report
/scripts
```

The library requires the use of a AMESH copy on the path, others pre/post TOUGH2 processors can be found on [here]('https://tough.lbl.gov/licensing-download/free-software-download/'). 

A detail documentation for the  library can be found on [Github pages](https://jejimenezm.github.io/T2GEORES/index.html)