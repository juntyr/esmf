// $Id: ESMC_Macros.h,v 1.3 2003/06/27 21:05:28 nscollins Exp $
//
// Earth System Modeling Framework
// Copyright 2002-2003, University Corporation for Atmospheric Research,
// Massachusetts Institute of Technology, Geophysical Fluid Dynamics
// Laboratory, University of Michigan, National Centers for Environmental
// Prediction, Los Alamos National Laboratory, Argonne National Laboratory,
// NASA Goddard Space Flight Center.
// Licensed under the GPL.

// Public prototypes and constants for the ESMF C++ interface

#ifndef ESMC_H
#define ESMC_H

//BOP
// -------------------------------------------------------------------------
// 
//  !DESCRIPTION:
// 
//  Utility macros and constants usable ESMF-wide from the C++ interface.
// 
//  (all lines below between the !BOP and !EOP markers will be included in
//   the automated document processing.)
// 
// -------------------------------------------------------------------------
//EOP

#define ESMF_SUCCESS  0
#define ESMF_FAILURE -1

#define ESMF_MAXSTR 128
#define ESMF_MAXDIM 7
#define ESMF_MAXDECOMPDIM 3
#define ESMF_MAXGRIDDIM 2

#define ESMF_SRCLINE __FILE__, __LINE__


#define ESMF_MAJOR_VERSION 1
#define ESMF_MINOR_VERSION 0
#define ESMF_REVISION      1
#define ESMF_PATCHLEVEL    0

#define ESMF_VERSION_STRING "1.0.1"

#endif

