import logger
import numpy as np
from sklearn.cluster import MeanShift, estimate_bandwidth 

def cluster_doa_1d(log_filename, quantile = 0.5, first_doa = True, 
    n_samples = None, n_jobs = None, cluster_all = True):
    '''
    cluster direction of arrival as 1d array.
    values vary from 0 - 359 (degrees) and will cluster on sound sources
    ie speakers. 
    For lower number of speakers use higher quantile and vice versa
    log_filename        the filename of the log file with doa in first or fourth
                        column
    quantile            using 0.5 means that the median of all pairwise 
                        distances used. Use lower value if there are more 
                        speakers
    first_doa           use the first doa column, log files can contain 
                        multiple doa columns, for now assumes 1 or 2
    n_samples            influences the estimate_bandwith computation speed
                        with none all samples are used
                        for long files you might restrict the number of 
                        samples used to speed up estimation
    n_jobs              use multiple cpus to do bandwidth estimation
    cluster_all         whether to assign orphans to nearest cluster
    '''
    log = logger.load_log(log_filename)
    index = 0 if first_doa and len(log[0]) != 6 else 3
    doa = [l[index] for l in log]
    X = np.array(list(zip(doa,np.zeros(len(doa)))), dtype=int)
    bandwidth=estimate_bandwidth(X,quantile=quantile, n_samples = n_samples)
    ms = MeanShift(bandwidth=bandwidth, bin_seeding=True, n_jobs = n_jobs,
        cluster_all = cluster_all)
    ms.fit(X)
    cluster_centers = ms.cluster_centers_[:,0]
    labels = ms.labels_
    return np.array(doa), labels, cluster_centers, ms

def cluster_doa_2d(log_filename):
    log = logger.load_log(log_filename)
    index = 0 if first_doa and len(log[0]) != 6 else 3
    doa = [l[index] for l in log]
    t = [l[index+2] for l in log]
    X = np.array([doa, t])
    return X
    

    
