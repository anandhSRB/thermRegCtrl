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
/**
 *
 * @author anandhr
 */
public class CabHeater {
    // initialize global variables
    double couplingTime;
    double errorTemp, errorTempSum;
    double kp, ki, kd;
    double maxHeaterRate;
    String cabSwitch;
    double massFlowRate; 
    
    public CabHeater(double maxHeater, double time, double massFlow){                        
        kp = -2.5;
        ki = -5;
        kd = 0;
        couplingTime = time;
        maxHeaterRate = maxHeater;
        cabSwitch = "inlet";
        massFlowRate = massFlow;
    }
    
    public double computeHeaterRate(Simulation simulation_0){
        
        double heaterRate;                
        
        ExpressionReport tempBo_ = ((ExpressionReport) simulation_0.getReportManager().getReport("tempBo"));
        double tempBo = tempBo_.getValue();
        
        MaxReport setPointAtInlet_ = ((MaxReport) simulation_0.getReportManager().getReport("setPointAtInlet"));
        double setPointAtInlet = setPointAtInlet_.getValue();
        
        VolumeAverageReport meanCabTemp_ = ((VolumeAverageReport) simulation_0.getReportManager().getReport("meanCabTemp"));
        double meanCabTemp = meanCabTemp_.getValue();
        
        double diffCabTemp = meanCabTemp-295.15;    //Set Point in cabin = 22degC
                       
        errorTemp = diffCabTemp;                    
        errorTempSum += errorTemp*couplingTime;
        
        heaterRate = kp*errorTemp + ki*errorTempSum;
        double newInletTemp = tempBo + heaterRate/(massFlowRate*1005);
        
        if (newInletTemp>setPointAtInlet){
            newInletTemp = setPointAtInlet;
            heaterRate = massFlowRate*1005*(newInletTemp-tempBo);
            errorTempSum = (heaterRate-kp*errorTemp)/ki;
        }
        
        
        return heaterRate;
    }
        
    
}
