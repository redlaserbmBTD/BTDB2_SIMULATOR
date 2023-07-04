#IMPORT NECESSARY LIBRARIES
import numpy as np
import pandas as pd

import os

nat_dirname = os.path.dirname(__file__)
nat_filename = os.path.join(nat_dirname, "templates/nat_send_lengths.csv")

#DEFINITION OF THE ROUNDS CLASS
class Rounds():
    def __init__(self, stall_factor_info):
        
        #Logging system
        self.logs = []

        #Determine natural send lengths, max stall times, and max anti-stall times
        df = pd.read_csv(nat_filename)
        self.nat_send_lens = list(df['Nat Send Len'])

        max_antistall_time = 5.5
        max_stall_times = [8.5 + i for i in range(51)]
        max_stall_times[0] = max_antistall_time

        #Backwards compatability with the old system:
        if type(stall_factor_info) == float:
            stall_factor_info = [(0,stall_factor_info)]

        #If the users fails to specify stall factor info for round 0...
        if stall_factor_info[0][0] > 0:
            stall_factor_info[0] = (0,stall_factor_info[0][1])

        #Compute the round times given the stall factor info
        val = 0
        self.round_starts = [0]

        ind_of_interest = 0
        stall_factor = stall_factor_info[ind_of_interest][1]
        for i in range(len(self.nat_send_lens)):

            #If we have reached a round where the stall factor changes, change the stall factor
            if len(stall_factor_info) >= ind_of_interest + 2 and i >= stall_factor_info[ind_of_interest+1][0]:
                ind_of_interest += 1
                stall_factor = stall_factor_info[ind_of_interest][1]
                #print("Changed stall factor to %s"%(stall_factor))

            #Determine the round length based on the current stall factor.
            round_len = self.nat_send_lens[i] + (1-stall_factor)*max_antistall_time + stall_factor*max_stall_times[i]
            val += round_len
            self.round_starts.append(val)            
            
    def getRoundFromTime(self, time, get_frac_part = False):
        ind = 0
        while self.round_starts[ind] <= time and ind < 50:
            ind += 1
        
        if get_frac_part:
            frac_part = (time - self.round_starts[ind-1])/(self.round_starts[ind] - self.round_starts[ind-1])
            ind += frac_part
            
        return ind - 1
    
    def getTimeFromRound(self, round_val):
        frac_part = round_val - np.floor(round_val)
        time = (1-frac_part)*self.round_starts[int(min(np.floor(round_val),50))] + frac_part*self.round_starts[int(min(np.ceil(round_val),50))]
        #self.logs.append("Mapped round %s to time %s"%(round_val,time))
        return time
    
    def changeStallFactor(self,stall_factor, current_time):
        self.logs.append("MESSAGE FROM Rounds.changeStallFactor():")
        self.logs.append("Changing the stall factor from %s to %s"%(self.stall_factor,stall_factor))
        self.logs.append("The old round start times were %s"%(self.round_starts))
        
        game_round = self.rounds.getRoundFromTime(current_time)
        
        if current_time < self.round_starts[game_round] + self.nat_send_lens[game_round]:
            #Yes, the current round should have its stall time modified
            start_ind = game_round
        else:
            #No, the current round should not have its stall time modified
            start_ind = game_round+1
            val = self.round_starts[start_ind]
        
        for i in range(start_ind, len(self.nat_send_lens)-1):
            #print("Trying index %s"%(str(i)))
            val += self.nat_send_lens[i] + (1-stall_factor)*4 + stall_factor*max_stall_times[i]
            self.round_starts[i+1] = val
        
        self.logs.append("The new round start times are %s"%(self.round_starts))
  