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

# Change log

Recent changes are listed.

## [0.1.7]
### 2021-01-16
- Include OUTPU section

### 2021-01-20
- Include GENER D capability

### 2021-01-28
- Include MOMOP section

### 2021-02-15
- Define ROCK section on dictionary basis

### 2021-03-04
- Export mesh and rock distribution to ParaView

### 2021-03-10
- Export results to ParaView

### 2021-06-06
- Fix GENER block update during production state

## [0.1.8]

### 2021-10-17
- Severals updates on mesh creation (lloyd relaxation) and incon creation

[0.1.7]: https://github.com/jejimenezm/T2GEORES/releases/tag/T2GEORES-0.1.8