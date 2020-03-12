 =========================================================================
 i T O U G H 2 _ 1  R U N  date: jue mar 12 11:59:06 CST 2020
 =========================================================================

Command submitted: /home/erick/bin/itough2 fit2 t2 1

STOP iTOUGH2 stopped in iTOUGH2Wrapper


     Error  >> Subroutine <<  Message
      5290  >>> OBSERVAT <<<  ERROR                --> Incomplete TOUGH2 simulation  

 ---     1 error(s) and  0 warning(s) detected

 Machine dependent real constants used in iTOUGH2
 ------------------------------------------------

 XZERO                      :         0.1000000000E-49
 EPS                        :         0.1000000000E-09
 XINF                       :         0.1000000000E+51

 HAVE READ UNKNOWN BLOCK LABEL "----*" --- IGNORE THIS, AND CONTINUE READING INPUT DATA
 HAVE READ UNKNOWN BLOCK LABEL "     " --- IGNORE THIS, AND CONTINUE READING INPUT DATA
 HAVE READ UNKNOWN BLOCK LABEL "     " --- IGNORE THIS, AND CONTINUE READING INPUT DATA
 HAVE READ UNKNOWN BLOCK LABEL "     " --- IGNORE THIS, AND CONTINUE READING INPUT DATA
 HAVE READ UNKNOWN BLOCK LABEL "     " --- IGNORE THIS, AND CONTINUE READING INPUT DATA
 HAVE READ UNKNOWN BLOCK LABEL "     " --- IGNORE THIS, AND CONTINUE READING INPUT DATA

 PRIMARY VARIABLE NO. 2 HOLDS SATURATION (RIGHT?)

                        ************************************************************************************
                        *                       EVALUATE FLOATING POINT ARITHMETIC                         *
                        ************************************************************************************
                        *                                                                                  *
                        * FLOATING POINT PROCESSOR HAS APPROXIMATELY 15 SIGNIFICANT DIGITS                 *
                        *                                                                                  *
                        * DEFAULT VALUE OF INCREMENT FACTOR FOR NUMERICAL DERIVATIVES IS DFAC = 0.1051E-07 *
                        * DEFAULT VALUE FOR DFAC WILL BE USED                                              *
                        *                                                                                  *
                        ************************************************************************************


 ==================================================================================================================================
      ARRAY DIMENSIONS (SEE FILE maxsize.inc)
 ----------------------------------------------------------------------------------------------------------------------------------
      MAXEL     =   20000      Maximum number of elements
      MAXCON    =   50000      Maximum number of connections
      MAXK      =       2      Maximum number of components
      MAXEQ     =       3      Maximum number of equations
      MAXPH     =       2      Maximum number of phases
      MAXB      =       6      Maximum number of phase-dependent secondary variables
      MAXSS     =    1000      Maximum number of sinks/sources
      MAVTAB    =      10      Maximum average number of table entries per sink/source
      MAXROC    =      20      Maximum number of rock types
      MAXTSP    =       5      Maximum number of specified time steps, divided by eight
      MAXLAY    =      10      Maximum number of reservoir layers for wells on deliverability
      MXRPCP    =       7      Maximum number of parameters for relative permeability and capillary pressure functions
      MXPCTB    =      10      Maximum number of points in table for ECM capillary pressure
      MXTBC     =       5      Maximum number of elements with time vs. boundary condition
      MXTBCT    =    1000      Maximum number of time vs. pressure data
      MAXTIM    =     400      Maximum number of calibration times
      MAXN      =      50      Maximum number of parameters to be estimated
      MAXO      =     200      Maximum number of datasets
      MAXM      =    1400      Maximum number of calibration points
      MAXPD     =    1000      Maximum number of paired data
      MAXR      =     100      Maximum number of elements or indices of each parameter or observation
      MAXBRK    =      20      Maximum number of points in time at which SAVE file is written for restart
      MAXEBRK   =      20      Maximum number of elements with new initial conditions after restart
      MAXCOEFF  =       5      Maximum number of coefficients for data modeling functions
      MAXMCS    =     100      Maximum number of Monte Carlo simulations
      MAXCURVE  =    2000      Maximum number of curves to be plotted
      MAXXGR    =       3      Dimension of third index of array XGUESSR
      MTYPE     =      25      Number of observation types
      MPFMT     =       6      Number of plot file formats 
 ----------------------------------------------------------------------------------------------------------------------------------


 ----------------------------------------------------------------------------------------------------------------------------------
      PROGRAM  VERSION   DATE                  COMMENT
 ----------------------------------------------------------------------------------------------------------------------------------
      iTOUGH2            Current version       iTOUGH2 V6.4 (JANUARY, 2009)                                                                                                                                                                                                                                    
 ----------------------------------------------------------------------------------------------------------------------------------
      iTOUGH   1.0       1 AUGUST    1992      ITOUGH User's Guide, Version 1.0, Report NIB 92-99
      iTOUGH2  2.2       1 FEBRUARY  1994      iTOUGH2 User's Guide, Version 2.2, Report LBL-34581
      iTOUGH2  3.0      12 JULY      1996      YMP Software qualification, Report LBNL-39489
      iTOUGH2  3.1       1 APRIL     1997      iTOUGH2 Command Reference, Version 3.1, Report LBNL-40041
      iTOUGH2  3.2      30 JUNE      1998      YMP Software Qualification, Report LBNL-42002
      iTOUGH2  3.3       1 OCTOBER   1998      Parallelization using PVM, Report LBNL-42261
      iTOUGH2  4.0      19 JANUARY   1999      Released by Energy Science and Technology Software Center
      iTOUGH2  5.0      31 JULY      2002      Qualified for use within Yucca Mountain Project
 ----------------------------------------------------------------------------------------------------------------------------------

      WHATCOM  1.0      10 AUGUST    1993      Q: WHAT COMPUTER IS USED? A: LINUX
      CALLSIG  1.0       5 DECEMBER  1995      #112: SIGNAL HANDLER
      CPUSEC   1.0      10 AUGUST    1993      RETURNS CPU-TIME (VERSION LINUX)
      OPENFILE 4.0      19 JANUARY   1999      OPENS MOST OF THE FILES
      LENOS    1.0       1 MARCH     1992      RETURNS LENGTH OF LINE
      PREC     1.0       1 AUGUST    1992      CALCULATE MACHINE DEPENDENT CONSTANTS
      ITHEADER 3.2      27 MAY       1998      PRINTS iTOUGH2 HEADER
      DAYTIM   1.0      10 AUGUST    1993      RETURNS DATE AND TIME (VERSION SUN)
      THEADER  6.0      29 JUNE      2007      PRINTS TOUGH2 HEADER
      SOLVTYPE 1.0       1 OCTOBER   1999      INITIALIZE PARAMETERS FOR THE SOLVER PACKAGE
      INPUT    6.4       5 MARCH     2009      READ ALL DATA PROVIDED THROUGH FILE *INPUT*
      INDATA   6.2      10 OCTOBER   2008      PROVIDE PRINTOUT OF MOST DATA PROVIDED THROUGH FILE *INPUT*
      CHECKMAX 6.0       4 FEBRUARY  2008      CHECK KEY DIMENSIONS
      FLOPP    1.1       4 NOVEMBER  2009      CALCULATE NUMBER OF SIGNIFICANT DIGITS FOR FLOATING POINT ARITHMETIC
      RFILE    5.1cd    18 DECEMBER  2007      INITIALIZE DATA FROM FILES *MESH* OR *MINC*, *GENER*, AND *INCON*
      ITINPUT  1.0       1 AUGUST    1992      READS COMMANDS OF COMMAND LEVEL 1
      READCOMM 2.5      14 JUNE      1996      READS A COMMAND
      FINDKEY  4.2      22 FEBRUARY  2000      READS A KEYWORD
      LTU      1.0       1 AUGUST    1992      CONVERTS LOWER TO UPPER CASE
      INOBSERV 6.4       3 MAY       2009      READS TYPE OF OBSERVATION
      INTIMES  6.4      17 MARCH     2009      READS TIMES AT WHICH OBSERVATIONS ARE AVAILABLE
      NEXTWORD 6.0      19 JUNE      2007      EXTRACTS NEXT WORD ON A LINE
      INCOMPUT 1.0       1 AUGUST    1992      READS VARIOUS COMPUTATIONAL PARAMETERS
      INPRINT  6.4      28 FEBRUARY  2009      READS OUTPUT OPTIONS
      INOPTION 6.4      13 MARCH     2008      READS PROGRAM OPTIONS
      READREAL 5.1      25 FEBRUARY  2005      READS A REAL AFTER A COLON
      GETINDEX 3.3      17 JULY      1998      GETS INDEX OF ELEMENTS, CONNECTIONS, AND SOURCES
      INIGUESS 6.4      17 AUGUST    2009      ASSIGN DEFAULT INITIAL PARAMETER GUESS
      IXLBXUB  2.1      21 SEPTEMBER 1993      INITIALIZES ARRAY XLB AND XUB
      ADDNOISE 6.0      14 JUNE      2007      ADDS NOISE TO SYNTHETIC DATA
      SETWSCAL 6.4       3 MARCH     2009      INITIALIZES ARRAY WSCALE
      OBSMEAN  1.0       1 AUGUST    1992      CALCULATES MEAN OF OBSERVATIONS
      SETXSCAL 1.0       1 AUGUST    1992      INITIALIZES ARRAY XSCALE
      IN_OUT   6.4      20 JANUARY   2009      PRINTS A SUMMARY OF INPUT DATA
      TIMEWIND 6.2       3 NOVEMBER  2008      SETS TIME WINDOW
      PRSTATUS 3.1      20 FEBRUARY  1997      PRINTS STATUS MESSAGES
      ERRORMSG 5.1      19 SEPTEMBER 2005      PRINTS ERROR MESSAGES
      FCNLEV   5.0      12 JULY      2002      RETURNS WEIGHTED RESIDUAL VECTOR
      UPDATE   6.4      17 AUGUST    2009      UPDATES PARAMETERS
      PRIORINF 2.1      21 SEPTEMBER 1993      PRIOR INFORMATION
      OBSERVAT 6.4      23 MARCH     2009      COMPARES MEASURED AND CALCULATED QUANTITIES
      GETMESH  3.2      20 JUNE      1998      READS FILE MESH, MINC, GENER, AND INCON
      GETINCON 6.2       8 OKTOBER   2008      READS FILE INCON
      INITTOUG 5.0      12 JULY      2002      INITIALIZES TOUGH2 RUN (REPLACES CYCIT)
      EOS      1.0      15 AUGUST    1990      *EOS1* ... THERMOPHYSICAL PROPERTIES MODULE FOR WATER
      SAT      4.2 MOS  16 JULY      1999      STEAM TABLE EQUATION: SATURATION PRESSURE AS FUNCTION OF TEMPERATURE
      VISW     1.0      22 JANUARY   1990      VISCOSITY OF LIQUID WATER AS FUNCTION OF TEMPERATURE AND PRESSURE
      COWAT    4.2 MOS  16 JULY      1999      LIQUID WATER DENSITY AND INT. ENERGY AS FUNCTION OF TEMPERATURE AND PRESSURE
      SUPST    4.2 MOS  16 JULY      1999      VAPOR DENSITY AND INTERNAL ENERGY AS FUNCTION OF TEMPERATURE AND PRESSURE
      PCAP     5.2cd    18 DECEMBER  2007      CAPILLARY PRESSURE FUNCTIONS
      BALLA    3.3      17 JULY      1998      PERFORM SUMMARY BALANCES FOR VOLUME, MASS, AND ENERGY
      CALLTOUG 6.4      15 FEBRUARY  2009      CALLS TOUGH2 FOR ONE TIME STEP
      TSTEP    6.4      22 JANUARY   2009      ADJUST TIME STEPS TO COINCIDE WITH USER-DEFINED TARGET TIMES
      MULTI    6.4       9 OCTOBER   2009      ASSEMBLE ALL ACCUMULATION AND FLOW TERMS

      QUV2     2.0       2 APRIL     2002      ASSEMBLE ALL SOURCE AND SINK TERMS
                                               "RIGOROUS" STEP RATE CAPABILITY FOR MOP(12) = 2,
                                               AND CAPABILITY FOR FLOWING WELLBORE PRESSURE CORRECTIONS
      LINEQ    2.1      30 JANUARY   2007      INTERFACE FOR LINEAR EQUATION SOLVERS

      ELINDX   5.0      12 JULY      2002      NEIGHBOR ELEMENT INDEXING
      REASSN   4.4      17 JANUARY   2001      ESTABLISH THE SPARSITY PATTERN FOR LUBAND
      MTRXIN   4.4      17 JANUARY   2001      ROUTINE FOR Z-PREPROCESSING 
      CONVER   6.4      20 FEBRUARY  2009      UPDATE PRIMARY VARIABLES AFTER CONVERGENCE IS ACHIEVED
      FGTAB    1.00     28 MAY       1998      TABULATE ELEMENT, CONNECTION, AND GENERATION DATA VS. TIME FOR PLOTTING
      OUT      5.0      12 JULY      2002      PRINT RESULTS FOR ELEMENTS, CONNECTIONS, AND SINKS/SOURCES
      WRIFI    6.2       8 OCTOBER   2008      AT THE COMPLETION OF A TOUGH2 RUN, WRITE PRIMARY VARIABLES ON FILE *SAVE*
      TERMINAT 6.4       3 MARCH     2009      PERFORM ERROR ANALYSIS AND TERMINATE iTOUGH2
      PLOTFILE 4.0      19 JANUARY   1999      WRITES PLOTFILE IN PLOPO-FORMAT
      QNORMAL  2.5      13 JANUARY   1996      RETURNS QUANTILE OF NORMAL DISTRIBUTION
      MOMENT   3.3      28 OCTOBER   1998      MOMENTS OF DISTRIBUTION
      PLOTIF   1.0      15 FEBRUARY  1993      PLOT INTERFACE
      REFORMAT 5.1       8 JUNE      2005      REFORMATS PLOT FILES
      QUOTES   1.0      15 FEBRUARY  1993      RETURNS TEXT BETWEEN QUOTES
      WRITEPAR 6.0       8 APRIL     2008      WRITE BEST FIT PARAMETER SET AND BLOCK ROCKS

 ==================================================================
      S T A T U S   O F   i T O U G H 2   S I M U L A T I O N
 ==================================================================

 Date                        : 12-Mar-20  11:59
 iTOUGH2 file                : fit2
 TOUGH2 file                 : t2
 Working directory           : /home/erick/Reservorios/T2RES/model/t2
 Temporary directory         : /home/erick/it2_30558
 UNIX command line arguments : fit2 t2 1
 Comment                     : Input files read.                                                              

 Iterations completed        :              0    Iterations to go      1
 TOUGH2 runs completed       :              0    Unsuccessful steps    0
 TOUGH2 runs to go (approx.) :              1    Log(Levenberg)        0
 CPU time used [sec]         :           0.64    for last step      0.64
