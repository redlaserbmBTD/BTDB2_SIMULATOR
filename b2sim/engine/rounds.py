#IMPORT NECESSARY LIBRARIES
import csv
from math import floor, ceil
import os
from bisect import bisect_right

nat_send = [0.5,18,17,18,23,21,17,17,15,14,5,8,11,12.5,5.5,9,27,33,20,30,1,10,24,6,54,30,21,18,17,40,1,48.294,9.53,22.75,8.44166,41.142,21.698,82.385,58.92083,90,2,35.68,25,21,14.55,11.9,35,15,32.12,30,0.1]
nat_stall = [5.5,9,10.5,11.5,12.5,13.5,14.5,15.5,13,17.5,16,16,18,13.5,16.5,23.5,11,13,12,14,28.5,16,13,16,15,27,28,22,23,18,38.5,15,15,15,15,15,15,15,15,15,48.5,15,15,15,15,15,15,15,15,15,58.5]
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
        self.nat_send_lens = nat_send

        max_antistall_time = 5.5
        if mode == 'Stall Factor':
            max_stall_times = nat_stall
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
        ind = bisect_right(self.round_starts, time)
        
        if get_frac_part:
            frac_part = (time - self.round_starts[ind-1])/(self.round_starts[ind] - self.round_starts[ind-1])
            ind += frac_part
            
        return ind - 1
    
    def getTimeFromRound(self, round_val):
        frac_part = round_val - floor(round_val)
        time = (1-frac_part)*self.round_starts[int(min(floor(round_val),50))] + frac_part*self.round_starts[int(min(ceil(round_val),50))]
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
  