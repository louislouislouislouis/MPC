
from datetime import datetime
from fileinput import filename
import subprocess
from contextlib import ExitStack
import os
import pprint
from datetime import datetime
import json

#Create good file
def create_circuit_file(circuit_name,number_of_parties):
    with open(str("./Programs/Source/")+circuit_name+str("_template.mpc"), 'r') as filesource:
        with open(str("./Programs/Source/")+circuit_name+str(".mpc"), 'w+') as fildest:
            txt=filesource.read()
            txt=txt.replace("$$$[P_NUMBER]$$$",str(number_of_parties))
            fildest.write(txt)

    

def compile(circuit_name,ring=False):
    if ring:
        subprocess.run(['./compile.py',circuit_name, "-R", "64"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    else:
        subprocess.run(['./compile.py',circuit_name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   


def create_outputs(number_of_parties):
    filenamesoutput = []
    filenameserror = []
    for i in range(number_of_parties):
        os.makedirs(os.path.dirname('./output/temp'+str(i)+'/out'), exist_ok=True)
        filenamesoutput.append('./output/temp'+str(i)+'/out')
        filenameserror.append('./output/temp'+str(i)+'/err')
    return filenamesoutput,filenameserror


def exec_and_wait_process(number_of_parties,programname,filenamesoutput,filenameserror,protocol):
    subprocesss= []
    with ExitStack() as stack1:
        filesout = [stack1.enter_context(open(fname,"w+")) for fname in filenamesoutput]
        with ExitStack() as stack:
            fileserr = [stack.enter_context(open(fname,"w+")) for fname in filenameserror]
            for i in range(number_of_parties):
                if i == 0:
                    subprocesss.append(subprocess.Popen([protocol["url"], str(i), programname, "-pn" ,"11247", "-h" ,"localhost" ,"-N", str(number_of_parties)],stdout=filesout[i],stderr=fileserr[i]))
                else:
                    subprocesss.append(subprocess.Popen([protocol["url"], str(i), programname, "-pn" ,"11247", "-h" ,"localhost" ,"-N", str(number_of_parties), "-I"],stdout=filesout[i],stderr=fileserr[i]) )
    for i in subprocesss:
        i.wait()


def magnify_metric(filenameserror,programme_name,protocol):
    with ExitStack() as stack:
        filesout = [stack.enter_context(open(fname,"r")) for fname in filenameserror]
        meta = {"global":
                    {
                        "filename":programme_name, 
                        "number_of_part":len(filenameserror),
                        "protocol":protocol["name"]
                    },
                "local":{

                }
                }
        for i in range(len(filenameserror)):
            meta["local"][i]={}
            file = filesout[i]
            lines = file.readlines()
            # Strips the newline character
            for line in lines:
                if "Time ="  in line:
                    meta["local"][i]["totalTime"]= float(line.split()[2])
                elif "Time1 ="  in line:
                    meta["local"][i]["transferTime"]= float(line.split()[2])
                    meta["local"][i]["transferData"]= float(line.split()[4][1:])
                elif "Time2 ="  in line:
                    meta["local"][i]["reconstructTime"]= float(line.split()[2])
                    meta["local"][i]["reconstructData"]= float(line.split()[4][1:])
                elif "Global data sent"  in line:
                    meta["local"][i]["globalDataSent"]= float(line.split()[4])
                elif "Data sent ="  in line:
                    meta["local"][i]["localDataSent"]= float(line.split()[3])
                    meta["local"][i]["localRound"]= float(line.split()[6][1:])  
        return meta

def export_metrics(metrics,programme_name):
    name_output= './measures/'+str(programme_name)+ "_" +str(datetime.now().strftime('%Y-%m-%d_%H:%M:%S:%f')+".json")
    os.makedirs(os.path.dirname(name_output), exist_ok=True)
    with open(name_output, "w+") as outfile:
        json.dump(metrics, outfile,indent = 2)

def generate_metrics(number_of_parties, programme_name,protocol,ring=False):
    create_circuit_file(programme_name,number_of_parties)
    compile(programme_name,ring)
    filenamesoutput,filenameserror = create_outputs(number_of_parties)
    exec_and_wait_process(number_of_parties,programme_name,filenamesoutput,filenameserror,protocol)
    metrics = magnify_metric(filenameserror,programme_name,protocol)
    export_metrics(metrics,programme_name)
    
if __name__ == '__main__':
    with open("./MeasurementCommon/experiment_setup.json") as file:
        experienceInfo = json.load(file)
    with open("./MeasurementCommon/proto.json") as file:
        protoInfo = json.load(file)
    print (experienceInfo)
    for number_of_part in experienceInfo["number_of_parties"]:
        for i in range(experienceInfo["number_of_transfer"]):
            for proto in protoInfo:
                if protoInfo[proto]["experiment"]:
                    print("Currently generate "+proto+" metrics for "+ str(number_of_part) +" partcicipant")
                    generate_metrics(number_of_part,"baseLine",{"name":proto,"url":protoInfo[proto]["program"]},ring=protoInfo[proto]["ring"])
                    generate_metrics(number_of_part,experienceInfo["circuit_to_test"],{"name":proto,"url": protoInfo[proto]["program"]},ring=protoInfo[proto]["ring"])
                    print("Done with "+proto)
    