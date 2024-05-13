# thermRegCtrl
Running JOS-3 thermoregulation model [1] with STAR-CCM+ with control for heating and recirculation. 
For more details on the implementation, refer to [2].

# Scripts organization
## Co-simulation in STAR-CCM+
The scripts were written for STAR-CCM+ v2210. The Java files can be compiled in Netbeans along with the STAR-CCM+ libraries. The compiled *.JAR file in the dist/ folder can access the classes.
The file src/thermregctrl/ThermRegCtrl.java can be used to run the simulation. The scripts make function calls to files in src/classes/ intermittently for recirculation and cab heater control. 

## JOS3 in Python3
The file pythonFiles/CoSim.py is called from src/thermregctrl/ThermRegCtrl.java. After installing jos3, replace the source file ('jos3.py') in the site-packages/jos3/ folder, with the 'jos3.py' available in the pythonFiles/ directory.
This accounts for the modifications necessary to perform the co-simulation.

# Running the simulation
## Simulation setup
The simulation (.sim) must be set up with a number of Tools/parameters that account for the boundary conditions as given in src/thermregctrl/ThermRegCtrl.java.
A number of monitors must be defined to export the air temperature, radiant temperature, heat flux, radiant heat flux, and relative humidity for each segment as shown in monitorData.csv.
To run src/classes/* for recirculation or heater control, appropriate boundary conditions must be defined to recompute the inlet conditions. 

## Run
Include src/thermregctrl/ThermRegCtrl.java, pythonFiles/CoSim.py, dist/thermRegCtrl.jar and the .sim file in a folder.
Use 
> starccm+ -Ver 2210 -np 16 -batch ThermRegCtrl.java -classpath thermRegCtrl.jar *.sim

## Berkeley comfort model
The UCB-Zhang comfort model has been included in pythonFiles/BerkeleyModel.py
Use the script pythonFiles/postComfort.py that uses the BerkeleyModel.py and the data from '*.csv' to compute sensations and comfort metrics.

# References
1. Takahashi, Y., Nomoto, A., Yoda, S., Hisayama, R., Ogata, M., Ozeki, Y. and Tanabe, S.I., 2021. Thermoregulation model JOS-3 with new open source code. Energy and Buildings, 231, p.110575.
2. Ramesh Babu, A., Sebben, S., Chronéer, Z., & Etemad, S., 2024. An adaptive cabin air recirculation strategy for an electric truck using a coupled CFD-thermoregulation approach. International Journal of Heat and Mass Transfer, 221, 125056.

# Citation
```
@article{RAMESHBABU2024125056,
title = {An adaptive cabin air recirculation strategy for an electric truck using a coupled CFD-thermoregulation approach},
journal = {International Journal of Heat and Mass Transfer},
volume = {221},
pages = {125056},
year = {2024},
issn = {0017-9310},
doi = {https://doi.org/10.1016/j.ijheatmasstransfer.2023.125056},
author = {Anandh {Ramesh Babu} and Simone Sebben and Zenitha Chronéer and Sassan Etemad},
}
´´´
