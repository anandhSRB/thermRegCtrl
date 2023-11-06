/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package classes;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.text.DecimalFormat;
import java.util.*;
import star.base.neo.DoubleVector;
import star.base.neo.NamedObject;
import star.base.neo.NeoObjectVector;
import star.base.report.FieldMeanMonitor;
import star.base.report.FieldSumMonitor;
import star.base.report.IterationMonitor;
import star.base.report.Monitor;
import star.base.report.PhysicalTimeMonitor;
import star.base.report.ReportMonitor;
import star.base.report.SumReport;
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

public class RecircControl{
    /*
    Initialize all global variables
    */
    double tempAmb, RHAmb;    
    static double kp_CO2, ki_CO2, errorSumCO2;
    static double kp_Vapor,ki_Vapor, kd_Vapor, errorSumVapor;
    static double setPointCO2,VaporSetPoint;
    static double errorCO2,errorVaporBo;
    
    public RecircControl(double t_inf, double RH_inf){
        /*
        Constructor for the class with initial/ambient temperature and relative humidity ratio [0-1]
        */
        tempAmb = t_inf;
        RHAmb = RH_inf*100;        
        
        // Compute specific humidity and vapor mass fraction
        double humidityAmb = computeHumidity(tempAmb, RHAmb);   
        double vaporMassFraction = computeMassFraction(humidityAmb);
        double deltaDewPoint = 1; // degC
        double tMin = -20;
        
        // CO2 control parameters
        kp_CO2 = -0.03;
        ki_CO2 = kp_CO2/100;
        errorSumCO2 = 0.;
        setPointCO2 = 1000; // ppm
        errorCO2 = 0.;
        
        // humidity control parameters
        double saturatedVaporMassFraction = computeMassFraction(computeHumidity(tempAmb-deltaDewPoint,100.0));
        double diffHumid = saturatedVaporMassFraction - vaporMassFraction;
        double steadyREC = computeSteadyStateREC(tempAmb, RHAmb, deltaDewPoint);
        double settingTime = steadyREC*5.7*diffHumid/(1.5e-4*computeHumidity(37,90));
        // vapor mass fraction at the saturated state
        kp_Vapor = - (1-RH_inf)*(1+(t_inf+20)/20)/((saturatedVaporMassFraction-vaporMassFraction));
        ki_Vapor = kp_Vapor/settingTime;
        kd_Vapor = 0;
        errorSumVapor = 0.;
        errorVaporBo = 0.;
        
        
        //VaporSetPoint = vaporMassFraction+(saturatedVaporMassFraction-vaporMassFraction)*0.95;  // 0.95 is the Factor of safety
        double dewPoint = computeDewPoint(humidityAmb);
        double humiditySetPoint = computeHumidity(dewPoint-deltaDewPoint,100);
        
        VaporSetPoint = computeMassFraction(humiditySetPoint);
        
        
        
        
    }
    
    public static double computeSteadyStateREC(double Ta,double RH,double deltaDewPoint){
        double recCO2 = 1-(1.5e-4*4e4)/(0.0803*(setPointCO2-420));

        double humidityAmb = computeHumidity(Ta,RH);
        double humidityInSet = computeHumidity(Ta-1,100);
        double humiditySource = computeHumidity(37,95);

        double recHumid = 1/(1+(1.5e-4*humiditySource/0.0803)/(humidityInSet-humidityAmb));

        return(Math.abs(Math.min(recHumid,recCO2)));
        
    }
    public static double computeDewPoint(double humidity){
        double dewPoint;
        double RH = 100;
        double a = 11.949;
        double b=3978.205;
        double c=-39.801+273.15;
        dewPoint = b/(a-Math.log(humidity/(0.622+humidity)))-c;                
        return dewPoint;
    }
    
    public static double Antoine(double T){      
        /*
        Antoine equation for computing the vapor saturation pressure
        */
        double a = 11.949;
        double b=3978.205;
        double c=-39.801;
        double p = 101325*Math.exp(a-b/(T+273.15+c));
        return p;
    }
    
    public static double ComputeRH(double T, double humidity){        
        /*
        Compute the RH corresponding to the temperature and specific humidity
        */
        double saturationPressure = Antoine(T);
        double RH = humidity*101325/((0.622+humidity)*saturationPressure);
        return RH*100;
    }
    
    public static double computeHumidity(double T, double RH){
        /*
        Compute specific humidity based on temperature and relative humidity
        */
        double saturationPressure = Antoine(T);
        double humidity = 0.622*RH/100*saturationPressure/(101325-RH/100*saturationPressure);
        return humidity;
    }
    
    public static double computeMassFraction(double humidity){
        /*
        vapor mass fraction for a specific humidity
        */
        return humidity/(1+humidity);
    }
    
    public static double updateHumditySetPoint(double minGlassT){
        double deltaDewPoint = 1;
        double vaporMassFractionUpdate;
        
        double humiditySet = computeHumidity(minGlassT-deltaDewPoint, 100);
        vaporMassFractionUpdate = computeMassFraction(humiditySet);        
        
        
        return vaporMassFractionUpdate;
    }
    
    public static double setRecirc(Simulation simulation_0){
        /*
        Returns recirculation to be set in the simulation based on a CO2 or humidity criteria        
        */
        simulation_0.println("================");
        simulation_0.println("kpVapor: "+kp_Vapor);
        
        simulation_0.println("");
        simulation_0.println("================");
        
        
        
        
        double recirc;
        
        //Obtain Volume average of CO2 from report
        VolumeAverageReport CO2concRep = ((VolumeAverageReport) simulation_0.getReportManager().getReport("CO2Conc"));
        double co2Conc = CO2concRep.getValue();
        
        //Obtain vapor mass fraction at the inlet from report
        AreaAverageReport VaporBoRep = ((AreaAverageReport) simulation_0.getReportManager().getReport("vaporMassFractionAtInlet")); // gives specific humidity
        double VaporBo = VaporBoRep.getValue();        
        VaporBo = computeMassFraction(VaporBo);
        
        //Obtain total fraction of dry area on the windows
        SumReport fractionOfDryAreaRep = ((SumReport) simulation_0.getReportManager().getReport("dryAreaFraction"));
        double dryFractionArea = fractionOfDryAreaRep.getValue();       
        
        MinReport minGlassTempRep = ((MinReport) simulation_0.getReportManager().getReport("minGlassTemp"));
        double minGlassTemp = minGlassTempRep.getValue()-273.15;                       
        
        //The update interval for the controller. The integral controller is multiplied with this time to make the scaling of the intergral controller consistent with all coupling times/timesteps
        FixedPhysicalTimeStoppingCriterion dt_ = ((FixedPhysicalTimeStoppingCriterion) simulation_0.getSolverStoppingCriterionManager().getSolverStoppingCriterion("Fixed Physical Time"));
        double dt = dt_.getFixedPhysicalTime().getSIValue();
        
        VaporSetPoint = updateHumditySetPoint(minGlassTemp);
        
        if ((dryFractionArea<1.9)){
            /*
            If the dry area is less than 99%, recirc is set to 0.0 to defog
            */
            recirc = 0.0;
            simulation_0.println("===========================================");
            simulation_0.println("Fogged state, setting recirculation to 0.0");
            simulation_0.println("===========================================");
        }
        
        else{
            /*
            The controller executes otherwise. 
            Two recirculation ratios are computed: One based on CO2 and one based on humidity. The values are corrected to limits.
            The humidity set point is based on the minimum glass temperature on the interface. A delta of 1 degC is taken to account for safety.
            The minimum of the two is chosen.            
            The intergral term for the larger recirc is corrected to prevent overshoot in subsequent steps.
            */
            simulation_0.println("===============Recirc control===========");
            simulation_0.println("Minimum Glass Temperature: "+minGlassTemp);
            simulation_0.println("VaporSetPoint: "+VaporSetPoint);
            
            errorCO2 = co2Conc - setPointCO2;

            // CO2
            errorSumCO2 += errorCO2*dt;
            double recircCO2 = kp_CO2*errorCO2+ki_CO2*errorSumCO2;
            if (recircCO2<0.001){
                recircCO2 = 0.001;
                errorSumCO2 -= errorCO2*dt;
            }
            else if (recircCO2>0.95){
                recircCO2 = 0.95;
                errorSumCO2 -= errorCO2*dt;
            }
            
            // humidity
            
            
            
            double errorVaporDt = (VaporBo-VaporSetPoint-errorVaporBo)/dt;
            errorVaporBo = VaporBo - VaporSetPoint;
            errorSumVapor += errorVaporBo*dt;
            
            double recircVapor = kp_Vapor*errorVaporBo +ki_Vapor*errorSumVapor+kd_Vapor*errorVaporDt;
            if (recircVapor<0.001){
                simulation_0.println("Setting vapor recirc from "+recircVapor+" to 0.0 ...");
                recircVapor = 0.001;
                errorSumVapor -= errorVaporBo*dt;
            }
            else if (recircVapor>0.95){
                simulation_0.println("Setting vapor recirc from "+recircVapor+" to 0.95 ...");
                recircVapor = 0.95;
                errorSumVapor -= errorVaporBo*dt;
            }
            
            // choose the minimum of the two
            recirc = Math.min(recircCO2,recircVapor);
            
            // Anti-windup for the inactive controller
            if (recirc == recircCO2){
                errorSumVapor = (recirc-errorVaporBo*kp_Vapor-errorVaporDt*kd_Vapor)/ki_Vapor;
            }
            else {
                errorSumCO2 = (recirc-errorCO2*kp_CO2)/ki_CO2;
            }
            
            simulation_0.println("Recirc: "+recirc);
            simulation_0.println("errorSumCO2:"+errorSumCO2);
            simulation_0.println("errorSumVapor :"+errorSumVapor);            
            simulation_0.println("errorCo2 : "+errorCO2);
            simulation_0.println("errorHumid : "+errorVaporBo);
            simulation_0.println("========================================");
        }
        
        return recirc;
        
    }
}
