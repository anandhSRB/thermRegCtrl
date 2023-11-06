/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package thermregctrl;

import classes.RecircControl;
import classes.CabHeater;
import java.util.*;

import star.common.*;
import star.base.neo.*;
import star.metrics.*;
import java.io.*;
import star.mapping.*;
import star.segregatedflow.*;
import star.keturb.*;
import star.flow.*;
import java.text.DecimalFormat;
import star.base.report.*;
import star.segregatedenergy.*;
import star.energy.*;
import star.material.*;
import star.post.*;
import star.vis.*;
import star.base.query.*;
import star.meshing.*;
import star.turbulence.*;
import star.viewfactors.*;
import star.radiation.s2s.*;
import star.radiation.common.*;

/**
 *
 * @author anandhr
 */

public class ThermRegCtrl extends StarMacro {
Simulation simulation_0;
String invalidCriteriaCab = "{ \'functionEnabled\': false,"
            + " \'minimumDiscontiguousCellsEnabled\': true, \'minimumDiscontiguousCells\': 1000,"
            + " \'minimumCellVolumeEnabled\': true, \'minimumCellVolume\': 0.0,"
            + " \'minimumVolumeChangeEnabled\': true, \'minimumVolumeChange\': 1.0E-3,"
            + " \'minimumCellQualityEnabled\': true, \'minimumCellQuality\': 1.0E-3,"
            + " \'minimumContiguousFaceAreaEnabled\': true,  \'minimumContiguousFaceArea\': 1.0E-9,"
            + " \'minimumFaceValidityEnabled\': true, \'minimumFaceValidity\': 0.98}";

RecircControl recircControl;
CabHeater cabHeater;
DecimalFormat dfTime = new DecimalFormat("#####0.0");
@Override
@SuppressWarnings("empty-statement")

public void execute() {
simulation_0 = getActiveSimulation();
long startTime = System.nanoTime();

//Set inputs - Case settings - To be setup as parameters in Tools in STAR-CCM+
double T_amb = -10; //degC
double massFlowRate = 0.083; //kg/s
double recirc = 0;    // Ratio [0-1]
double RH_amb = 0.7;    //Ratio [0-1]
double fogThickness = 1e-10; // initial fog thickness (m)
double speed = 90;   // kph
double maxHeaterRate = 1e4;


// feedback recirculation control based on CO2 & humidity
boolean recircControlSwitch = true; 
recircControl = new RecircControl(T_amb, RH_amb);   // Feedback control


//simulation settings
double totalTime = 1800; // Total simulation time
double updateTime = 1;  // coupling time for thermoregulation model
double timeStep = 0.2; // timestep
boolean srh = false;    // srh model (scale resolved hybrid turbulence model)
boolean freezeFlow = false;  // freezeFlow (Pseudo transient approach with steady flow and transient energy solver)

//sim history
boolean simHistory = true;  // setup history
String[] simHistoryFields = {"BoundaryHeatFlux","Temperature"}; // Fields for history


// cabin heating controller
cabHeater = new CabHeater(maxHeaterRate, updateTime,massFlowRate);
double heaterPI =  100.0; // Init heater rate;
if (recircControlSwitch){
    /*
        The initial value must be adaptive for controller stability since the initial value of the controller is calibrated to work accordingly. 
    Setting a different value causes large variation in error resulting in oscillations.
    */
    recirc =(1-RH_amb)*(1+(T_amb+20)/20);
}

double[] caseSettings = {T_amb,massFlowRate,recirc,heaterPI,RH_amb,fogThickness,speed};   
double[] simSettings = {totalTime,updateTime,timeStep};


// Steps
SetInputs(caseSettings,simSettings);
simHistorySetup(simHistory,simHistoryFields);  
RemoveInvalidCells();
RunSimulation(srh,recircControlSwitch,freezeFlow);
SaveSim();
simulation_0.println("=====> Total time to Run = " + dfTime.format((System.nanoTime() - startTime) / 1E9 / 3600) + " hours <=====");
}

    private void RunSimulation(boolean srh, boolean recircControlSwitch, boolean freezeFlow) {        
        /*
        Run simulation function:
        Simulate fixed time @ time step and then update the thermophysical model (in python3) and recircControl (if activated)
        SRH model is activated after 30s if set to true        
        */
        PhysicalTimeStoppingCriterion stopTime = ((PhysicalTimeStoppingCriterion) simulation_0.getSolverStoppingCriterionManager().getSolverStoppingCriterion("Maximum Physical Time"));        
        ScalarGlobalParameter recircParameter = ((ScalarGlobalParameter) simulation_0.get(GlobalParameterManager.class).getObject("recirc"));
        ScalarGlobalParameter heaterPIParameter = ((ScalarGlobalParameter) simulation_0.get(GlobalParameterManager.class).getObject("heaterPI"));
        Units units_3 = ((Units) simulation_0.getUnitsManager().getObject(""));
        double timeStepTransient = (simulation_0.getSolverManager().getSolver(ImplicitUnsteadySolver.class).getTimeStep().evaluate());
        boolean srhSwitch = false;
        
        while(simulation_0.getSolution().getPhysicalTime()<stopTime.getMaximumTime().getSIValue()){            
            String s;
            if (simulation_0.getSolution().getPhysicalTime()>30.0 && ((!srhSwitch) && (srh))){
                /*
                Switch for SRH model - The physics model name is "Physics 1" for cabin air.
                */
                simulation_0.println("Switching to SRH model");
                PhysicsContinuum cabinAir = ((PhysicsContinuum) simulation_0.getContinuumManager().getContinuum("Physics 1")); 
                cabinAir.enable(SrhModel.class);
                srhSwitch = true;
            }            
            
            // Set skin temperatures based on the human model
            try {
                /*
                When the fixedTime has completed, the python model named 'CoSim.py' is executed. Read documentation in the file.
                */
                  simulation_0.println("======Updating human model====");
                  String dir = simulation_0.getSessionDir(); //get the name of the directory
                  String sep = System.getProperty("file.separator"); //get the right separator for your operative system
                  String [] cmd = new String[3];
                  cmd[0] = "python3"; // Build string to be read by the exec() method - "python pathToScript"
                  cmd[1] = "CoSim.py";
                  double timeStep = (simulation_0.getSolverManager().getSolver(ImplicitUnsteadySolver.class).getTimeStep().evaluate());
                  cmd[2] = Double.toString(timeStep);
                  Process p = Runtime.getRuntime().exec(cmd);                 
                  //Read output from Python script
		  BufferedReader stdInput = new BufferedReader(new InputStreamReader(p.getInputStream()));
		  BufferedReader stdError = new BufferedReader(new InputStreamReader(p.getErrorStream()));
			
		  while ((s = stdInput.readLine()) != null) {
				simulation_0.println(s);
			}
			simulation_0.println("python script executed");
                                
            }
            catch (IOException e) {
                  simulation_0.println("error");
            }
        
        // Reload tables 
        // simulation_0.println("Reloading tables");
        // The boundary conditions on the human should be read from the table and interpolated in time lineraly for each segment. 
        FileTable fileTable_0 = ((FileTable) simulation_0.getTableManager().getTable("driver"));
        fileTable_0.extract();
        
        simulation_0.println(" Reloaded tables... new temperatures updated");    
        simulation_0.println("==============================================");
        // Run for x seconds
        
        if (freezeFlow && simulation_0.getSolution().getPhysicalTime()>9.999){
            /*
            Switch for freezing flow: Not recommended while changing recirc in time.
            */
            double time = simulation_0.getSolution().getPhysicalTime();         
            
            double frozenTimeStep = 0.25;
            if (time%10<8.9){
                simulation_0.println("--------------------Frozen Flow------------------------");
                FreezeFlow(frozenTimeStep);
            }
            else{
                simulation_0.println("--------------------Transient Flow------------------------");
                UnfreezeFlow(timeStepTransient);
            }
            
        }
        
        simulation_0.getSimulationIterator().run();
        
          
        // Export all monitors with the string "Driver": export heat flux, radiative heat flux, air temperature 10mm away from the skin, relative humidity 10mm away from the skin, radiant temperature on the skin.
        String dir = simulation_0.getSessionDir(); //get the name of the directory
        String sep = System.getProperty("file.separator"); //get the right separator for your operative system
        Collection printMonitors = simulation_0.getMonitorManager().getObjects();
        Collection reportMonitors = new ArrayList();
        for (Object mon : printMonitors){
            if ((mon.toString().contains("Driver"))){
                reportMonitors.add((Object) mon);
                
            }
            else{
               // printMonitors.remove(mon);
            }
        }
        //Collection print = printMonitors;
        simulation_0.getMonitorManager().export(dir+sep+"monitorData.csv",",",reportMonitors);
        
        // Update heater rate 
        double heaterPI = cabHeater.computeHeaterRate(simulation_0);
        heaterPIParameter.getQuantity().setValue(heaterPI);
        heaterPIParameter.getQuantity().setUnits(units_3);   
        // Update recirc
        if (recircControlSwitch){
        double recirc = recircControl.setRecirc(simulation_0);            
        recircParameter.getQuantity().setValue(recirc);
        recircParameter.getQuantity().setUnits(units_3);
        }
        
        
        }
    }

    private void SetInputs(double[] caseSettings, double[] simSettings) {
        /*
        Set boundary and simulation conditions
        */
        // Sim settings
        simulation_0.println("===============================");
        simulation_0.println("Setting: TotalTime "+simSettings[0]+"s");
        simulation_0.println("Setting: CouplingTime "+simSettings[1]+"s");
        simulation_0.println("Setting: timeStep "+simSettings[2]+"s");
        Units units_0 = ((Units) simulation_0.getUnitsManager().getObject("s"));
        PhysicalTimeStoppingCriterion stopTime = ((PhysicalTimeStoppingCriterion) simulation_0.getSolverStoppingCriterionManager().getSolverStoppingCriterion("Maximum Physical Time"));
        stopTime.setMaximumTime(simSettings[0]);
        stopTime.getMaximumTime().setUnits(units_0);
        
        FixedPhysicalTimeStoppingCriterion Update = ((FixedPhysicalTimeStoppingCriterion) simulation_0.getSolverStoppingCriterionManager().getSolverStoppingCriterion("Fixed Physical Time"));   
        Update.setFixedPhysicalTime(simSettings[1]);
        Update.getFixedPhysicalTime().setUnits(units_0);
        
        ImplicitUnsteadySolver tS = ((ImplicitUnsteadySolver) simulation_0.getSolverManager().getSolver(ImplicitUnsteadySolver.class));
        tS.getTimeStep().setValue(simSettings[2]);
        tS.getTimeStep().setUnits(units_0);
        
        // caseSettings
        simulation_0.println("===============================");
        simulation_0.println("Scenario: T_amb "+caseSettings[0]+" C");
        simulation_0.println("Scenario: massFlowRate "+caseSettings[1]+"kg/s");
        simulation_0.println("Scenario: recirc "+caseSettings[2]+"");
        simulation_0.println("Scenario: Init heater rate "+caseSettings[3]+" W");
        simulation_0.println("Scenario: RH_amb "+caseSettings[4]*100+" %");
        simulation_0.println("Scenario: initialFogThickness "+caseSettings[5]+" m");
        simulation_0.println("Scenario: external HTC "+caseSettings[6]+" kph");
        simulation_0.println("===============================");
        
        Units units_1 = ((Units) simulation_0.getUnitsManager().getObject("K"));
        Units units_2 = ((Units) simulation_0.getUnitsManager().getObject("kg/s"));
        Units units_3 = ((Units) simulation_0.getUnitsManager().getObject(""));
        Units units_4 = ((Units) simulation_0.getUnitsManager().getObject("m"));
        
        ScalarGlobalParameter scalarGlobalParameter_1 = ((ScalarGlobalParameter) simulation_0.get(GlobalParameterManager.class).getObject("T_amb"));
        scalarGlobalParameter_1.getQuantity().setValue(caseSettings[0]+273.15);
        scalarGlobalParameter_1.getQuantity().setUnits(units_1);
        
        ScalarGlobalParameter scalarGlobalParameter_2 = ((ScalarGlobalParameter) simulation_0.get(GlobalParameterManager.class).getObject("massFlowRate"));
        scalarGlobalParameter_2.getQuantity().setValue(caseSettings[1]);
        scalarGlobalParameter_2.getQuantity().setUnits(units_2);
        
        ScalarGlobalParameter scalarGlobalParameter_3 = ((ScalarGlobalParameter) simulation_0.get(GlobalParameterManager.class).getObject("recirc"));
        scalarGlobalParameter_3.getQuantity().setValue(caseSettings[2]);
        scalarGlobalParameter_3.getQuantity().setUnits(units_3);
        
        ScalarGlobalParameter scalarGlobalParameter_4 = ((ScalarGlobalParameter) simulation_0.get(GlobalParameterManager.class).getObject("heaterPI"));
        scalarGlobalParameter_4.getQuantity().setValue(caseSettings[3]);
        scalarGlobalParameter_4.getQuantity().setUnits(units_3);
        
        ScalarGlobalParameter scalarGlobalParameter_5 = ((ScalarGlobalParameter) simulation_0.get(GlobalParameterManager.class).getObject("RH_amb"));
        scalarGlobalParameter_5.getQuantity().setValue(caseSettings[4]);
        scalarGlobalParameter_5.getQuantity().setUnits(units_3);
        
        ScalarGlobalParameter scalarGlobalParameter_6 = ((ScalarGlobalParameter) simulation_0.get(GlobalParameterManager.class).getObject("fogThickness"));
        scalarGlobalParameter_6.getQuantity().setValue(caseSettings[5]);
        scalarGlobalParameter_6.getQuantity().setUnits(units_4);
        
        ScalarGlobalParameter scalarGlobalParameter_7 = ((ScalarGlobalParameter) simulation_0.get(GlobalParameterManager.class).getObject("vehSpeed"));
        scalarGlobalParameter_7.getQuantity().setValue(caseSettings[6]*5/18);
        
    }

    private void RemoveInvalidCells() {
        /*
        Remove cabAir bad cells
        -Should be updated to include all regions-
        */
    MeshManager meshManager_0 = simulation_0.getMeshManager();
    Region cab = simulation_0.getRegionManager().getRegion("cabAir");
    for (int i=1;i<=8;i++){
        meshManager_0.removeInvalidCells(new NeoObjectVector(new Object[] {cab}), NeoProperty.fromString(invalidCriteriaCab));
    }
    

    }
    
    private void simHistorySetup(boolean simHistory,String[] fields) {
        /*
        Setup simulation history for the imposed fields every 10s on all planes and boundaries in cabAir including interfaces b/w opaque and transparent solids and the skin of the human.
        */
        if(simHistory){
            simulation_0.println("============");
            simulation_0.println("Setting up Solution History");
            simulation_0.println("============");
            String saveFile = "sim"; // Location of the sim file
            SolutionHistory solutionHistory_0 = null;
            switch(saveFile){
                case "sim":
                    String dir = simulation_0.getSessionDir(); //get the name of the directory
                    String sep = System.getProperty("file.separator"); //get the right separator for your operative system
                    solutionHistory_0 = simulation_0.get(SolutionHistoryManager.class).createForFile(dir+sep+"simulationHistory.simh", false,true);
                    break;
                case "java":
                    solutionHistory_0 = simulation_0.get(SolutionHistoryManager.class).createForFile(resolvePath("simulationHistory.simh"), false,true);
                    break;
            }
            
            
            solutionHistory_0.setAddReportFieldFunctions(true);
            // Field functions
            
            FieldFunction[] fieldArrays = new FieldFunction[fields.length];
            for (int i=0;i<fields.length;i++){
                fieldArrays[i] = (FieldFunction) simulation_0.getFieldFunctionManager().getFunction(fields[i]);                
            }
            Collection<FieldFunction> fieldSet = Arrays.asList(fieldArrays);
            
            simulation_0.println("----------------------------------------------");
            simulation_0.println("Simulation history saved on derived parts and surfaces");
            simulation_0.println("Fields saved: "+fieldSet);
            simulation_0.println("----------------------------------------------");
            
            Region region_0 = simulation_0.getRegionManager().getRegion("cabAir");
            solutionHistory_0.getInputs().setQuery(new Query(new CompoundPredicate(CompoundOperator.Or, Arrays.<QueryPredicate>asList(new CompoundPredicate(CompoundOperator.And, Arrays.<QueryPredicate>asList(new TypePredicate(TypeOperator.Is, Part.class), new NamePredicate(NameOperator.Contains, "_"))), new CompoundPredicate(CompoundOperator.And, Arrays.<QueryPredicate>asList(new NamePredicate(NameOperator.Contains, "Human"), new RelationshipPredicate(RelationshipOperator.DescendantOf, new IdentityPredicate(IdentityOperator.Equals, Arrays.<ClientServerObject>asList(region_0))))), new NamePredicate(NameOperator.Contains, "Interface to cabAir [In-place 1]"), new NamePredicate(NameOperator.Contains, "Region 1/OpaqueSolids [0]"))), Query.STANDARD_MODIFIERS));
            solutionHistory_0.setFunctions(fieldSet);
            StarUpdate starUpdate_4 = solutionHistory_0.getUpdate();
            starUpdate_4.getUpdateModeOption().setSelected(StarUpdateModeOption.Type.DELTATIME);

            DeltaTimeUpdateFrequency deltaTimeUpdateFrequency_4 =  starUpdate_4.getDeltaTimeUpdateFrequency();
            Units units_0 = ((Units) simulation_0.getUnitsManager().getObject("s"));
            deltaTimeUpdateFrequency_4.setDeltaTime("10.0", units_0);

            // Export region
            //solutionHistory_0.getRegions().setQuery(new Query(new NamePredicate(NameOperator.Contains, ""), Query.STANDARD_MODIFIERS));
            solutionHistory_0.setExportAtAllStencils(true);
            solutionHistory_0.setAutoRescan(false);
        
        } else {
            simulation_0.println("============");
            simulation_0.println("Solution History Disabled");
            simulation_0.println("============");
        }
    }

    private void SaveSim() {
        /*
        Save simulation with '_Finished' appended to the name
        */
        String dir = simulation_0.getSessionDir(); //get the name of the directory
        String sep = System.getProperty("file.separator"); //get the right separator for your operative system
        String filename = simulation_0.getPresentationName();
        simulation_0.saveState(dir + sep + filename + "_Finished.sim");
    }
    
    private void FreezeFlow(double frozenTimeStep) {
        /*
        Freeze flow solver and run only energy solver
        */
        SegregatedFlowSolver segregatedFlowSolver_0 = ((SegregatedFlowSolver) simulation_0.getSolverManager().getSolver(SegregatedFlowSolver.class));
        KeTurbSolver keTurbSolver_0 = ((KeTurbSolver) simulation_0.getSolverManager().getSolver(KeTurbSolver.class));
        KeTurbViscositySolver keTurbViscositySolver_0 = ((KeTurbViscositySolver) simulation_0.getSolverManager().getSolver(KeTurbViscositySolver.class));
        Units units_0 = ((Units) simulation_0.getUnitsManager().getObject("s"));
        
        segregatedFlowSolver_0.setFreezeFlow(true);    
        keTurbSolver_0.setFrozen(true);
        keTurbViscositySolver_0.setFrozen(true);
        
        ImplicitUnsteadySolver tS = ((ImplicitUnsteadySolver) simulation_0.getSolverManager().getSolver(ImplicitUnsteadySolver.class));
        tS.getTimeStep().setValue(frozenTimeStep);
        tS.getTimeStep().setUnits(units_0);
    }

    
    private void UnfreezeFlow(double timeStepTransient) {
        /*
        Unfreeze flow solver; Run completely transient simulations
        */
        SegregatedFlowSolver segregatedFlowSolver_0 = ((SegregatedFlowSolver) simulation_0.getSolverManager().getSolver(SegregatedFlowSolver.class));
        KeTurbSolver keTurbSolver_0 = ((KeTurbSolver) simulation_0.getSolverManager().getSolver(KeTurbSolver.class));
        KeTurbViscositySolver keTurbViscositySolver_0 = ((KeTurbViscositySolver) simulation_0.getSolverManager().getSolver(KeTurbViscositySolver.class));
        Units units_0 = ((Units) simulation_0.getUnitsManager().getObject("s"));
        
        segregatedFlowSolver_0.setFreezeFlow(false);    
        keTurbSolver_0.setFrozen(false);
        keTurbViscositySolver_0.setFrozen(false);
        
        ImplicitUnsteadySolver tS = ((ImplicitUnsteadySolver) simulation_0.getSolverManager().getSolver(ImplicitUnsteadySolver.class));
        tS.getTimeStep().setValue(timeStepTransient);
        tS.getTimeStep().setUnits(units_0);
    }
    
}

