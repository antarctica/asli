# Method

The methods used in this package are fairly straightforward but have developed slightly over time. See the [versions](#versions) section below.

## Computing the index

In brief:

+ Mean Sea Level Pressure fields from ERA5 are clipped to the region of interest.
+ The land is masked away using a land-sea binary mask calculated from the land-sea fraction of each pixel and a threshold of 50%, i.e. pixels with >=50% land are classed as land in the mask.
+ Pressure values are inverted and a peak finding function ([`skimage.feature.peak_local_max`](https://scikit-image.org/docs/stable/api/skimage.feature.html#skimage.feature.peak_local_max)) used to find the minima.
+ We also compute the area-average sea level pressure over the sector and the relative central pressure.


## Automating the ASLI

This package is used to automatically update the dataset published at the Polar Data Centre, run by the British Antarctic Survey.

This is done using [`asli-pipeline`](https://github.com/antarctica/asli-pipeline) which also performs quality assurance checks prior to publising.


## Versions

If you look at the header of the data file produced, the calculation version is `3.20240813`, this is distinct from the software version or the data version, and changes to it indicate a difference in the method by which the ASLI is calculated.

This page describes the version `3.20240813` method currently in use, but previous methods have been used to calculate the position and pressure of the Amundsen Sea Low in [Hosking *et al.* (2013)][hosking2013] and [Hosking *et al.* (2016)][hosking2016]

### Version 3
Version 3 is derived using ERA5 data with an updated algorithm written in python.

The version number 3.20240813 is used for the current packaged implementation of the version 3 python-based method, but differs only in that it is structured as a package. The code for version 3 is at <https://github.com/scotthosking/amundsen-sea-low-index>


<br>

---

Previous versions of the analysis have been used in the past to derive the ASL index.

The following is taken from the ASL legacy page on the BAS website: <https://legacy.bas.ac.uk/data/absl/index2.html>

### Version 2
In version 2 the ASL latitude and longitude are identified using a minima finding algorithm within the ASL sector (here defined as 170°—298° E, 80°—60° S). This methodology is more robust at identifying the ASL compared to version 1 (see Hosking et al., 2016).

+ The monthly ASL indices can be downloaded from here [ASL Monthly Version 2](https://legacy.bas.ac.uk/data/absl/ASL-index-Version2-Monthly-ERA-Interim_Hosking2016.txt)
+ The seasonal and annual ASL indices can downloaded from here [ASL Seasonal Version 2](https://legacy.bas.ac.uk/data/absl/ASL-index-Version2-Seasonal-ERA-Interim_Hosking2016.txt)

When using the version 2 dataset in a paper, the following is the correct citation to use:

> Hosking, J. S., Orr, A., Bracegirdle, T. J., Turner, J. (2016). Future circulation changes off West Antarctica: Sensitivity of the Amundsen Sea Low to projected anthropogenic forcing.. Geophysical Research Letters, 43, [doi:10.1002/2015GL067143](http://dx.doi.org/10.1002/2015GL067143)

### Version 1
In the original ASL indices (now known as version 1) the ASL latitude and longitude are identified at the geographical location of minimum pressure in the ASL sector (here defined as 170°—290° E, 75°—60° S; note that this is different to the region used in version 2).

+ The monthly ASL indices can be can downloaded from here [ASL Monthly Version 1](https://legacy.bas.ac.uk/data/absl/ASL-index-Monthly-ERA-Interim_Hosking2013.txt)
+ The seasonal and annual ASL indices can be can downloaded from here [ASL Seasonal Version 1](https://legacy.bas.ac.uk/data/absl/ASL-index-Seasonal-ERA-Interim_Hosking2013.txt)

When using the version 1 dataset in a paper, the following is the correct citation to use:

> Hosking, J. S., Orr, A., Marshall, G. J., Turner, J., and Phillips, T. (2013). The influence of the Amundsen-Bellingshausen Seas Low on the climate of West Antarctica and its representation in coupled climate model simulations. Journal of Climate, 26(17):6633-6648. [doi:10.1175/JCLI-D-12-00813.1](http://dx.doi.org/10.1175/JCLI-D-12-00813.1)

[hosking2013]: http://dx.doi.org/10.1175/JCLI-D-12-00813.1
[hosking2016]: http://dx.doi.org/10.1002/2015GL067143
