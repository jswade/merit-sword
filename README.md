# MERIT-SWORD
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.13156892.svg)](https://doi.org/10.5281/zenodo.13156892)

[![License (3-Clause BSD)](https://img.shields.io/badge/license-BSD%203--Clause-yellow.svg)](https://github.com/jswade/merit-sword/blob/main/LICENSE)

MERIT-SWORD is a collection of Python and bash shell scripts that reconciles 
critical differences between the SWOT River Database (SWORD), the hydrography  
dataset used to aggregate observations from the Surface Water and Ocean 
Topography (SWOT) Mission, and MERIT-Basins (MB) an elevation-derived vector 
hydrography dataset commonly used by global river routing models.

The SWORD and MERIT-Basins river networks differ considerably in their 
representation of the location and extent of global river reaches, complicating 
potential synergistic data transfer between SWOT observations and existing 
hydrologic models.

MERIT-SWORD aims to:

1.  Identify a subset of river reaches in MERIT-Basins that directly correspond 
to related reaches in SWORD (ms_riv_network files).
2.  Generate bidirectional, one-to-many links (i.e. translations) between river 
reaches in SWORD and MERIT-Basins (ms_translate files).
3.  Provide a reach-specific evaluation of the quality of translations 
(ms_diagnostic files).
