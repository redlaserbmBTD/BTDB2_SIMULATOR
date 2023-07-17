#IMPORT NECESSARY LIBRARIES
import numpy as np
import pandas as pd

import os

nat_dirname = os.path.dirname(__file__)
nat_filename = os.path.join(nat_dirname, "templates/nat_send_lengths.csv")

#DEFINITION OF THE ROUNDS CLASS

# There are different ways to set round times in the Rounds class:
# 1. Stall Factor - Sets rounds using designated "stall factors" for each round
# 2. Theoretical Stall Factor - Just like 
# 3. Stall Times
# 4. Manual

class Rounds():
    def __init__(self, info, mode = 'Stall Factor'):

        if mode == 'Manual':
            #For manually setting round times
            self.round_starts = info
            return None

        #Determine natural send lengths, max stall times, and max anti-stall times
        df = pd.read_csv(nat_filename)
        self.nat_send_lens = list(df['Nat Send Len'])

        max_antistall_time = 5.5
        if mode == 'Stall Factor':
            max_stall_times = list(df['Nat Stall Len'])
        else:
            #If using the Theoretical Stall Factor or Stall Times modes, use the round timer to determine maximum stall times
            max_stall_times = [8.5 + i for i in range(51)]
            max_stall_times[0] = max_antistall_time
        
        #Backwards compatability with the old system:
        if type(info) == float:
            info = [(0,info)]

        #If the user fails to specify stall factor info for round 0...
        if info[0][0] > 0:
            info[0] = (0,info[0][1])

        #Compute the round times given the stall factor info
        val = 0
        self.round_starts = [0]

        ind_of_interest = 0
        stall_info = info[ind_of_interest][1]
        for i in range(len(self.nat_send_lens)):

            #If we have reached a round where the stall info changes, change the stall info
            if len(info) >= ind_of_interest + 2 and i >= info[ind_of_interest+1][0]:
                ind_of_interest += 1
                stall_info = info[ind_of_interest][1]
            
            if mode == 'Stall Times':
                #Interpret the stall info as meaning, "the given round is stalled for this many seconds"
                round_len = self.nat_send_lens[i] + max(max_antistall_time,min(max_stall_times[i],stall_info))
            elif mode == 'Stall Factor' or mode == 'Theoretical Stall Factor':
                #Interpret the stall info as meaning, "the given round has this stall factor"
                round_len = self.nat_send_lens[i] + (1-stall_info)*max_antistall_time + stall_info*max_stall_times[i]
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
    
    def getStallTimes(self):
        #given self.round_starts, determine how long each round is stalled for in seconds
        stall_times = [0]
        for i in range(1,len(self.round_starts) - 1):
            stall_times.append((self.round_starts[i+1] - self.round_starts[i]) - self.nat_send_lens[i])
        return stall_times

    def changeStallFactor(self,stall_factor, current_time):
        #self.logs.append("MESSAGE FROM Rounds.changeStallFactor():")
        #self.logs.append("Changing the stall factor from %s to %s"%(self.stall_factor,stall_factor))
        #self.logs.append("The old round start times were %s"%(self.round_starts))
        
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
  