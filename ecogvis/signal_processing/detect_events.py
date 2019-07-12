import numpy as np
import scipy.signal as sgn
from ecogvis.signal_processing.resample import *

def detect_events(speaker_data, mic_data, interval=None, dfact=30, stimtime=0.4,
                  resptime=0.4, threshold=0.05):
    """
    Automatically detects events in audio signals.

    Parameters
    ----------
    speaker_data : 'pynwb.base.TimeSeries' object
        Object containing speaker data.
    mic_data : 'pynwb.base.TimeSeries' object
        Object containing microphone data.
    interval : list of floats
        Interval to be used [Start_bin, End_bin]. If 'None', the whole signal is used.
    dfact : float
        Downsampling factor. Default 30.
    stimtime: float
        Min time for stimulus (default = .4, decent for CVs)
    resptime : float
        Min time for response (default = stimtime)
    threshold : float
        Sets threshold level.
    """

    # Downsampling Speaker -----------------------------------------------------
    if interval is None:
        X = speaker_data.data[:]
    else:
        X = speaker_data.data[interval[0]:interval[1]]
    fs = speaker_data.rate    #sampling rate
    ds = fs/dfact
    #Pad zeros to make signal lenght a power of 2, improves performance
    nBins = X.shape[0]
    extraBins = 2**(np.ceil(np.log2(nBins)).astype('int')) - nBins
    extraZeros = np.zeros(extraBins)
    X = np.append(X, extraZeros)
    speakerDS = resample(X, ds, fs)
    #Remove excess bins (because of zero padding on previous step)
    excessBins = int(np.ceil(extraBins*ds/fs))
    speakerDS = speakerDS[0:-excessBins]

    #kernel size must be an odd number
    speaker_filt = sgn.medfilt(volume=np.diff(np.append(speakerDS,speakerDS[-1]))**2,
                               kernel_size=int((stimtime*dfact//2)*2+1))
    speaker_thresh = np.std(speaker_filt)*threshold
    #Find threshold crossing times
    stimBinsDS = threshcross(speaker_filt, speaker_thresh, 'up')
    #Remove detections too close in time (< 100 miliseconds)
    rem_ind = np.where(np.diff(stimBinsDS/ds)<.1)[0] + 1
    stimBinsDS = np.delete(stimBinsDS, rem_ind)
    #Transform bins to time
    stimtimesDS = stimBinsDS/ds

    # Downsampling Mic ---------------------------------------------------------
    # X = mic_data.data[:]
    # #Pad zeros to make signal lenght a power of 2, improves performance
    # nBins = mic_data.data.shape[0]
    # extraBins = 2**(np.ceil(np.log2(nBins)).astype('int')) - nBins
    # extraZeros = np.zeros(extraBins)
    # X = np.append(X, extraZeros)
    # micDS = resample(X, ds, fs)
    # #Remove excess bins (because of zero padding on previous step)
    # excessBins = int(np.ceil(extraBins*ds/fs))
    # micDS = micDS[:, 0:-excessBins]

    #REST OF MATLAB CODE -------------------------------------------------------
    #micDS([speakerfilt; speakerfilt(end)] > speakerthresh) = 0; #get rid of mic response to speaker
    #micfilt = medfilt1(diff([micDS;micDS(end)]).^2,round(resptime*fsDS));
    #micthresh = 2e-4; #std(micfilt)/70 + mean(micfilt);
    #resptimes = threshcross(micfilt,micthresh,'up')/fsDS;
    # MATLAB CODE --------------------------------------------------------------

    return speakerDS, stimtimesDS


def threshcross(data, threshold=0, direction='up'):
    """
    Outputs the indices where the signal crossed the threshold.

    Parameters
    ----------
    data : array of floats
        Numpy array of floats, containing signal.
    threshold : float
        Value of threshold.
    direction : str
        Defines the direction of cross detected: 'up', 'down', or 'both'.

    Returns
    -------
    out : array
        Array with indices where data crossed threshold.
    """

    # Find crosses
    over = (data >= threshold).astype('int')
    cross = np.append(False,np.diff(over))

    if direction == 'up':
        out = np.where(cross==1)[0]
    elif direction == 'down':
        out = np.where(cross==-1)[0]
    elif direction == 'both':
        out = np.where(cross!=0)[0]

    return out
