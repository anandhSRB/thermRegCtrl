# thermRegCtrl
Running JOS-3 thermoregulation model with STAR-CCM+ with control for heating and recirculation. 

# Scripts organization
## Co-simulation in STAR-CCM+
The scripts were written for STAR-CCM+ v2210. The Java files can be compiled in Netbeans along with the STAR-CCM+ libraries. The compiled *.JAR file in the dist/ folder can be used to accessed the classes.
The file src/thermregctrl/ThermRegCtrl.java can be used to run the simulation. The scripts makes function calls to files in src/classes/ intermittently for recirculation and cab heater control. 

## JOS3 in Python3
The file pythonFiles/CoSim.py is called from src/thermregctrl/ThermRegCtrl.java. After installing jos3, replace the source file ('jos3.py') in the site-packages/jos3/ folder with the jos3.py available in the pythonFiles/ directory.
This accounts for the modifications necessary to perform the co-simulation.

# Running the simulation
## Simulation setup
The simulation (.sim) must be set up with a number of Tools/parameters that account for the boundary conditions as given in src/thermregctrl/ThermRegCtrl.java
A number of monitors must be defined to export the air temperature, radiant temperature, heat flux, radiant heat flux, and relative humidity for each segment as shown in monitorData.csv
To run src/classes/* for recirculation or heater control, appropriate boundary conditions must be defined to recompute the inlet conditions. 

## Run
Include src/thermregctrl/ThermRegCtrl.java, pythonFiles/CoSim.py, dist/thermRegCtrl.jar and the .sim file in a folder.
Use 
> starccm+ -Ver 2210 -np 16 -batch ThermRegCtrl.java -classpath thermRegCtrl.jar *.sim


