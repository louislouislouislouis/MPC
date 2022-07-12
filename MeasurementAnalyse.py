from pprint import pprint
import matplotlib.pyplot as plt
import os
from contextlib import ExitStack
import json
import pprint
import numpy as np

def list_full_paths(directory):
    return [os.path.join(directory, file) for file in os.listdir(directory)]

def extract_raw_metrics(filesname,dataInfo,exp_info):
    all_data ={}
    with ExitStack() as stack:
        files = [stack.enter_context(open(fname,"r")) for fname in filesname]
        for i in range(len(files)):
            file = files[i]
            data = json.load(file)
            protocol =  data["global"]["protocol"]
            if ( data["global"]["number_of_part"] in exp_info["number_of_parties"] and (exp_info["circuit_to_test"] == data["global"]["filename"] or data["global"]["filename"] == "baseLine") ):
                if not protocol in all_data:
                    all_data[protocol]={}
                    # Distingue protocol and baseline
                    all_data[protocol]["mpc"]={}
                    all_data[protocol]["baseline"]={}
                    for metric in dataInfo:
                        all_data[protocol]["mpc"][metric]=[]
                        all_data[protocol]["baseline"][metric]=[]   
                if data["global"]["filename"]!="baseLine":
                    for loc in data["local"]:
                        # Change the global data sent by dividing by nulber off participant to get the mean localdata sent
                        data["local"][loc]["globalDataSent"] = data["local"][loc]["globalDataSent"]/data["global"]["number_of_part"]         
                        for metric in dataInfo:
                            all_data[protocol]["mpc"][metric].append(data["local"][loc][metric])            
                else:
                    for loc in data["local"]:
                        # Change the global data sent by dividing by nulber off participant to get the mean localdata sent
                        data["local"][loc]["globalDataSent"] = data["local"][loc]["globalDataSent"]/data["global"]["number_of_part"]         
                        for metric in dataInfo:
                            all_data[protocol]["baseline"][metric].append(data["local"][loc][metric])  
    
    return all_data


def getMean(all_data):
    mean = {}
    for proto in all_data:
        mean[proto]={}
        mean[proto]["mpc"]={}
        mean[proto]["baseline"]={}
        for metric in dataInfo:
            mean[proto]["baseline"][metric]=np.mean(all_data[proto]["baseline"][metric])
            mean[proto]["mpc"][metric]=np.mean(all_data[proto]["mpc"][metric])
    return mean

def analyseData(data,protoInfo):
    #Adding labels
    labels = []
    for proto in data:
        if protoInfo[proto]["analyse"]:
            labels.append(protoInfo[proto]["label"])

    #Graphics Style
    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars

    # Processing Time
    mpc_total_time_means = []
    mpc_transfer_time_means = []
    baseLines_means = []
    for proto in data:
        if protoInfo[proto]["analyse"]:
            mpc_total_time_means.append(data[proto]["mpc"]["totalTime"])
            mpc_transfer_time_means.append(data[proto]["mpc"]["transferTime"])
            baseLines_means.append(data[proto]["baseline"]["totalTime"])

    #GRaphics Plot
    fig, (ax,ax2), = plt.subplots(2, 2)
    
    rects1 = ax[0].bar(x - width/2, mpc_transfer_time_means, width, label='Trnasfer Time')
    rects1 = ax[0].bar(x - width/2, np.subtract(mpc_total_time_means,mpc_transfer_time_means), width, label='Reconstruct Time',bottom=mpc_transfer_time_means)
    rects2 = ax[0].bar(x + width/2, baseLines_means, width, label='Baseline',)

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax[0].set_ylabel('Transfer Time in s')
    ax[0].set_title('Transfer Time grouped by protocol')
    ax[0].set_yscale('log')
    ax[0].set_xticks(x, labels)
    ax[0].legend()
    ax[0].bar_label(rects1, padding=3)
    ax[0].bar_label(rects2, padding=3)


    #Processing Data 
    mpc_global_data_sent = []
    mpc_transfer_data_sent = []
    for proto in data:
        if protoInfo[proto]["analyse"]:
            mpc_global_data_sent.append(data[proto]["mpc"]["globalDataSent"])
            mpc_transfer_data_sent.append(data[proto]["mpc"]["localDataSent"])
    print(mpc_global_data_sent)
    print(mpc_transfer_data_sent)
    
    #GRaphics Plot
    rects1 = ax[1].bar(x , mpc_transfer_data_sent, width, label='Data involved in transfer')
    #rects1 = ax[1].bar(x , np.subtract(mpc_global_data_sent,mpc_transfer_data_sent), width, label='Data involved in reconstruct',bottom=mpc_transfer_data_sent)
    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax[1].set_ylabel('Transfer Data in Mb')
    ax[1].set_title('Transfer Data grouped by protocol')
    ax[1].set_xticks(x, labels)
    ax[1].set_yscale('log')
    ax[1].legend()
    ax[1].bar_label(rects1, padding=3)

    #Processing Reound 
    mpc_round = []
    for proto in data:
        if protoInfo[proto]["analyse"]:
            mpc_round.append(data[proto]["mpc"]["localRound"])
    

    rects1 = ax2[0].bar(x , mpc_round, width, label='Round')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax2[0].set_ylabel('Round number')
    ax2[0].set_title('Round number grouped by protocol')
    ax2[0].set_xticks(x, labels)
    ax2[0].legend()
    ax2[0].set_yscale('log')
    ax2[0].bar_label(rects1, padding=3)

    plt.show()
    
if __name__ == '__main__':
    protoInfo = None
    dataInfo = None
    with open("./MeasurementCommon/proto.json") as file:
        protoInfo = json.load(file)
    with open("./MeasurementCommon/data_metrics.json") as file:
        dataInfo = json.load(file)
    with open("./MeasurementCommon/experiment_setup.json") as file:
        exp_info = json.load(file)
    filesname = list_full_paths("./measures")
    data = extract_raw_metrics(filesname,dataInfo,exp_info)
    mean = getMean(data)
    analyseData(mean,protoInfo)
    
