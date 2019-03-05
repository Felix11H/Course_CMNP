# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 12:33:59 2017
Tested in Python 3.6.5, Anaconda Inc.

@author: Miehl
Adapted by: Florence Kleberg

This simulation contains a LIF neuron receiving excitatory and inhibitory 
spiking inputs, with classical STDP in the excitatory synapses.
The neuron posesses intrinsic plasticity, with which it adapts
its own spiking threshold in ongoing manner to homeostatically
regulate its firing.

"""

from __future__ import division # for Python 2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec

from Euler_Method import Euler 
from Input_synapse import Synapse

from Poisson_Spike_Trains import Poisson_Trains
from Correlated_Spike_Trains import Correlated_Trains
from CorrelatedJitter_Spike_Trains import CorrelatedJitter_Trains

from Plasticity_Rules import NN_STDP

import Parameters_Int_and_Fire

tau_mem       = Parameters_Int_and_Fire.tau_mem
E_leak        = Parameters_Int_and_Fire.E_leak
E_e           = Parameters_Int_and_Fire.E_e
E_i           = Parameters_Int_and_Fire.E_i
V_reset       = Parameters_Int_and_Fire.V_reset
V_thresh      = Parameters_Int_and_Fire.V_thresh
t_0           = Parameters_Int_and_Fire.t_0
t_max         = Parameters_Int_and_Fire.t_max
time_step_sim = Parameters_Int_and_Fire.time_step_sim
numb_exc_syn  = Parameters_Int_and_Fire.numb_exc_syn
numb_inh_syn  = Parameters_Int_and_Fire.numb_inh_syn
tau_e         = Parameters_Int_and_Fire.tau_e
tau_i         = Parameters_Int_and_Fire.tau_i
firing_rate_e = Parameters_Int_and_Fire.firing_rate_e
firing_rate_i = Parameters_Int_and_Fire.firing_rate_i
w_e           = Parameters_Int_and_Fire.w_e
w_i           = Parameters_Int_and_Fire.w_i
delta_t       = Parameters_Int_and_Fire.delta_t
# STDP parameters : 
tau_LTP       = Parameters_Int_and_Fire.tau_LTP
A_LTP         = Parameters_Int_and_Fire.A_LTP
tau_LTD       = Parameters_Int_and_Fire.tau_LTD
A_LTD         = Parameters_Int_and_Fire.A_LTD
w_max         = Parameters_Int_and_Fire.w_max
# correlation in the two groups
c1            = Parameters_Int_and_Fire.c1     
c2            = Parameters_Int_and_Fire.c2
tau_c         = Parameters_Int_and_Fire.tau_c
# IP parameters
etha_IP       = Parameters_Int_and_Fire.etha_IP
R_target      = Parameters_Int_and_Fire.R_target

# define function for excitatory synapse
def excit_cond(g_e_tt,tau_e): # g_e_tt is the changing variable
    func_g_e=-g_e_tt/tau_e
    return func_g_e

# define function for inhibitory synapse
def inhib_cond(g_i_tt,tau_i): # g_e_tt is the changing variable
    func_g_i=-g_i_tt/tau_i
    return func_g_i

# define function to integrate the membrane voltage equation
arg_for_V='total_input_tt,' + 'E_leak,' + 'tau_mem' + 'E_k'
def memb_volt(V_tt,arg_for_V):
    func_V=(E_leak-V_tt+total_input_tt)/tau_mem
    return func_V

# value storage
t_vals = [] # for time
V_vals = [] # for membrane potential V
spike_times = []
FR_vec=[]
V_thresh_vec=[]

# initialize values for voltage, time and conductances (excitatory and inhibitory)
t_vals.append(t_0) 
V_vals.append(V_reset)
V_tt = V_reset
tt = t_0+time_step_sim # initialize tt for the while loop, starts at first time step
g_e_tt_vec=[0]*numb_exc_syn # starting values of all the excitatory conductances (zeros)
g_i_tt_vec=[0]*numb_inh_syn # starting values of all the inhibitory conductances (zeros)
total_exc_input_tt = 0
total_inh_input_tt = 0
w_e_vec_tt=[w_e]*numb_exc_syn # define exc. weights here (all the weights are the same)
w_i_vec_tt=[w_i]*numb_inh_syn 

# buffer for spike times (for STDP)
last_post_spike=0
idx_of_synapse_with_spike=[]

# buffer for weight changes over time (STDP in excitatory synapses)
w_e_storage=np.zeros((int(round((t_max-t_0)/time_step_sim))+1, numb_exc_syn))
w_e_storage[0,:]=w_e_vec_tt
counter_storage=1;

# These counters count the number of excitatory/inhibitory inputs to the neuron
counter_e=0
spike_time_e=[0]*numb_exc_syn
counter_i=0
spike_time_i=[0]*numb_inh_syn
number_spikes = 0 
###########################
# create input spike trains
###########################

# firing rates : 
r1 = firing_rate_e
r2 = firing_rate_e
r3 = firing_rate_i
r4 = firing_rate_i

#### get correlated spike tains for excitatory input
#spikes_e_corr = Correlated_Trains()
#[list_of_all_spike_trains1,list_of_all_spike_trains2] = spikes_e_corr.get_list_of_trains(c1,c2,firing_rate_e)
spikes_e_corr = CorrelatedJitter_Trains()
[list_of_all_spike_trains1,list_of_all_spike_trains2] = spikes_e_corr.get_list_of_trains(c1,c2,firing_rate_e,tau_c)
spike_trains_complete_e = list_of_all_spike_trains1 + list_of_all_spike_trains2

spikes_i = Poisson_Trains()
[list_of_all_spike_trains1,list_of_all_spike_trains2] = spikes_i.get_list_of_trains(r3,r4)
spike_trains_complete_i = list_of_all_spike_trains1 + list_of_all_spike_trains2

###################
# Start of the loop
###################
V_1 = Euler()
synapse_e = Synapse()
synapse_i = Synapse()

exc_STDP = NN_STDP() 

while tt <= t_max:

    # call function for excitatory inputs
    [g_e_tt_vec]=synapse_e.inputs_calc(g_e_tt_vec,time_step_sim,numb_exc_syn,w_e_vec_tt,excit_cond,tau_e,tt,delta_t,spike_trains_complete_e)
    total_exc_input_tt=sum([ww*(E_e-V_tt) for ww in g_e_tt_vec])

    # call function for inhibitory inputs
    [g_i_tt_vec]=synapse_i.inputs_calc(g_i_tt_vec,time_step_sim,numb_inh_syn,w_i_vec_tt,inhib_cond,tau_i,tt,delta_t,spike_trains_complete_i)
    total_inh_input_tt=sum([ww*(E_i-V_tt) for ww in g_i_tt_vec])
    
    # Include STDP in excitatory synapses. (1)
    # Check if there was LTD by comparing all new pre-spikes in this timepoint with the latest post-spike. 
    w_e_vec_tt=exc_STDP.STDP_post_pre(last_post_spike-time_step_sim/10,spike_trains_complete_e,tt,time_step_sim,w_e_vec_tt,tau_LTD,A_LTD,w_max)
    
    # update the postsynaptic neuron.
    total_input_tt=total_exc_input_tt+total_inh_input_tt
    V = V_1.euler_integration(memb_volt, arg_for_V, V_tt,tt,time_step_sim,delta_t)
    
    if V<V_thresh:
        V_tt=V
    else: # if threshold is reached -> spike & reset mem V
        V_tt=V_reset
        # log spike time (for figure)
        V_vals.append(0) 
        t_vals.append(tt-time_step_sim/10) 
        spike_times.append(tt)
        number_spikes=number_spikes+1

        ### include STDP in excitatory synapses. (2)
        w_e_vec_tt = exc_STDP.STDP_pre_post(tt+time_step_sim/10,spike_trains_complete_e,w_e_vec_tt,tau_LTP,A_LTP,w_max)
        
    t_vals.append(tt)
    V_vals.append(V_tt)
    tt=tt+time_step_sim
    
    # Intrinsic Plasticity
    if tt%1000==0:
        R_count=number_spikes/tt*1000
        FR_vec.append(R_count)
    
        V_thresh=V_thresh+etha_IP*(R_count-R_target)
    
    V_thresh_vec.append(V_thresh)
    
    w_e_storage[counter_storage,:]=w_e_vec_tt # store the weights of the excitatory synapses
    counter_storage=counter_storage+1

############################################################
# Plot weight evolution, V_thresh evolution, and firing rate
############################################################

import matplotlib.pyplot as plt
from matplotlib import gridspec

fig1=plt.figure(figsize=(12,5))
gs = gridspec.GridSpec(1, 9)

# weight evolution
ax1 = fig1.add_subplot(gs[0,0:-6])
for ww in range(0,int(numb_exc_syn*0.5)):
    ax1.plot(range(int(round((t_max-t_0)/time_step_sim))+1),w_e_storage[:,ww],color='m',label='Correl.: ' + str(c1))
    ax1.plot(range(int(round((t_max-t_0)/time_step_sim))+1),w_e_storage[:,int(ww+(round(numb_exc_syn*0.5)))],color='g',label='Correl.: '+ str(c2))
ax1.set_xlabel('Time (ms)')
ax1.set_ylabel('Syn. Weight')
#for ww2 in range(int(numb_exc_syn*0.5),numb_exc_syn):

# threshold evolution
ax2 = fig1.add_subplot(gs[0,-6:-3])
ax2.plot(range(int(round((t_max-t_0)/time_step_sim))),V_thresh_vec,lw=2,color='c')
ax2.set_xlabel('Time (ms)')
ax2.set_ylabel('Spiking Threshold (mV)')

# postsynaptic firing rate
ax3=fig1.add_subplot(gs[0,-3::])
x_for_FR = np.arange(1,int(round(t_max/1000))+1)
ax3.plot(x_for_FR,FR_vec,lw=2,color='r')
ax3.set_xlabel('Time (second)')
ax3.set_ylabel('Firing Rate (Hz)')

plt.tight_layout()
plt.show()
fig1.savefig('4_2_IP.png')
