#DEFINITIONS OF THE 
import copy
from math import floor, ceil
from b2sim.engine.info import *

class MonkeyFarm():
    def __init__(self, initial_state):
        
        ###############
        #BASIC FEATURES
        ###############
        
        #self.upgrades is an array [i,j,k] representing the upgrade state of the farm
        #EXAMPLE: [4,2,0] represents a Banana Research Facility with Valuable Bananas
        
        self.upgrades = initial_state.get('Upgrades')
        self.sell_value = farm_sellback_values[tuple(self.upgrades)]
        
        self.purchase_time = initial_state.get('Purchase Time')
        self.init_purchase_time = self.purchase_time #This isn't great code, *but*, I do this so that the sim can accurately track eco impact.
        
        self.payout_amount = farm_payout_values[tuple(self.upgrades)][0]
        self.payout_frequency = farm_payout_values[tuple(self.upgrades)][1]
        
        ##############
        #BANK FEATURES
        ##############
        
        self.bank = False

        #If the farm is a bank, mark is as such
        if self.upgrades[1] >= 3:
            self.bank = True
        
        self.account_value = 0
        self.max_account_value = farm_bank_capacity[self.upgrades[1]]
        
        #Regarding the IMF Loan/Monkeyopolis active ability
        self.min_use_time = None
        if self.upgrades[1] >= 4:
            self.min_use_time = self.purchase_time + farm_globals['Monkeynomics Initial Cooldown']

        ###################
        #OVERCLOCK FEATURES
        ###################

        self.overclock_expiration_time = initial_state.get('Overclock Expiration Time')

        ##################
        # REVENUE TRACKING
        ##################

        # Rather than remove a farm from the simulator when sold, we will just mark its sell time and tell the simulator not to consider payments from this farm anymore
        self.sell_time = None

        self.revenue = 0
        self.expenses = 0

        # Tracks hypothetical revenue while processing the buy queue.
        # In general this is necessary because of the impact of Loans on revenue generation.
        self.h_revenue = 0

    def payout(self, time, mws_bonus = False, brf_buff = False, bank_interest = False):
        #This method should be used over calling self.payout_amount directly because it automatically accounts for overclock & MWS buffs

        if bank_interest:
            payout_amount = farm_globals['Start of Round Bank Payment']
        else:
            payout_amount = self.payout_amount
        
        # First, apply the MWS bonus if relevant:
        # Note that the code which ensures the MWS bonus is paid out at only the correct times is handled by the GameState class, not the MonkeyFarm class!
        if mws_bonus and self.upgrades[2] >= 5:
            payout_amount += farm_globals['Monkey Wall Street Bonus']
        
        # Next, if the farm is being buffed by overclock, apply the overclock buff to the payout:
        # NOTE: The start of round bank interest payment is NOT eligible to be overclock-buffed.
        if self.overclock_expiration_time is not None and time < self.overclock_expiration_time and not bank_interest:
            payout_amount *= engi_globals['Overclock Payout Modifier']

        # Finally, if the farm is being buffed by Banana Central, apply that buff to this farm's payment
        if brf_buff and self.upgrades[0] == 4:
            payout_amount *= farm_globals['Banana Central Multiplier']

        # Finally, return the payout!
        return payout_amount
    
    def computePayoutSchedule(self, start_time, target_time, rounds, BC_exists = False):
        '''
        Determines all payments the farm will give between the start_time and target_time (left-open interval)
        assuming round lengths equal to rounds.
        '''
        payout_times = []
        # print("calling computePayoutSchedule with start and target times %s and %s"%(start_time, target_time))
        if self.sell_time is not None:
            return payout_times

        #If this farm is a monkeynomics, determine the payout times of the active ability
        if self.upgrades[1] == 5:
            while self.min_use_time <= start_time:
                self.min_use_time += farm_globals['Monkeynomics Payout']

            farm_time = self.min_use_time

            while farm_time <= target_time:
                if farm_time > start_time:
                    payout_entry = {
                        'Time': farm_time,
                        'Payout Type': 'Direct',
                        'Payout': farm_globals['Monkeynomics Payout'],
                        'Source': 'Farm',
                    }
                    payout_times.append(payout_entry)
                farm_time += farm_globals['Monkeynomics Usage Cooldown']

        farm_purchase_round = rounds.getRoundFromTime(self.purchase_time)
        current_round = rounds.getRoundFromTime(start_time)
        inc = 0
        flag = False
        while flag == False:
            #If computing farm payments on the same round as we are currently on, precompute the indices the for loop should go through.
            #NOTE: This is not necessary at the end because the for loop terminates when a "future" payment is reached.
            if inc == 0:
                if current_round > farm_purchase_round:
                    #When the farm was purchased on a previous round
                    round_time = start_time - rounds.round_starts[current_round]
                    loop_start = int(floor(self.payout_frequency*round_time/rounds.nat_send_lens[current_round]) + 1)
                    loop_end = self.payout_frequency
                else: #self.current_round == farm_purhcase_round
                    #When the farm was purchased on the same round as we are currently on
                    loop_start = int(floor(self.payout_frequency*(start_time - self.purchase_time)/rounds.nat_send_lens[current_round]-1)+1)
                    loop_end = int(ceil(self.payout_frequency*(1 - (self.purchase_time - rounds.round_starts[current_round])/rounds.nat_send_lens[current_round])-1)-1)
            else:
                loop_start = 0
                loop_end = self.payout_frequency
            
            #self.logs.append("Precomputed the loop indices to be (%s,%s)"%(loop_start,loop_end))
            #self.logs.append("Now computing payments at round %s"%(self.current_round + self.inc))
            
            for i in range(loop_start, loop_end):
                #Precompute the value i that this for loop should start at (as opposed to always starting at 0) to avoid redundant computations
                #Farm payout rules are different for the round the farm is bought on versus subsequent rounds
                if current_round + inc == farm_purchase_round:
                    farm_time = self.purchase_time + (i+1)*rounds.nat_send_lens[current_round + inc]/self.payout_frequency
                else:
                    # print("Current round + inc: %s"%(current_round+inc))
                    farm_time = rounds.round_starts[current_round + inc] + i*rounds.nat_send_lens[current_round + inc]/self.payout_frequency
                    # print("Set time to %s"%(farm_time))
                
                #Check if the payment time occurs within our update window. If it does, add it to the payout times list
                if farm_time <= target_time and farm_time > start_time:
                    
                    #Farm payouts will either immediately be added to the player's cash or added to the monkey bank's account value
                    #This depends of course on whether the farm is a bank or not.
                    
                    #WARNING: If the farm we are dealing with is a bank, we must direct the payment into the bank rather than the player.
                    #WARNING: If the farm we are dealing with is a MWS, we must check whether we are awarding the MWS bonus payment!
                    #WARNING: If the farm we are dealing with is a BRF, we must check whether the BRF buff is being applied or not!
                    
                    if self.upgrades[1] >= 3:
                        if i == 0 and current_round + inc > farm_purchase_round:
                            #At the start of every round, every bank gets a $400 payment and then is awarded 20% interest.
                            payout_entry = {
                                'Time': farm_time,
                                'Payout Type': 'Bank Interest',
                                'Source': 'Farm'
                            }
                            payout_times.append(payout_entry)
                        payout_entry = {
                            'Time': farm_time,
                            'Payout Type': 'Bank Payment',
                            'Payout': self.payout(farm_time),
                            'Source': 'Farm'
                        }
                    elif i == 0 and self.upgrades[2] == 5 and current_round + inc > farm_purchase_round:
                        payout_entry = {
                            'Time': farm_time,
                            'Payout Type': 'Direct',
                            'Payout': self.payout(farm_time, mws_bonus = True),
                            'Source': 'Farm',
                        }
                    elif self.upgrades[0] == 4 and BC_exists == True:
                        payout_entry = {
                            'Time': farm_time,
                            'Payout Type': 'Direct',
                            'Payout': self.payout(farm_time, brf_buff = True),
                            'Source': 'Farm'
                        }
                    else:
                        payout_entry = {
                            'Time': farm_time,
                            'Payout Type': 'Direct',
                            'Payout': self.payout(farm_time),
                            'Source': 'Farm',
                        }
                    payout_times.append(payout_entry)
                elif farm_time > target_time:
                    #self.logs.append("The payout time of %s is too late! Excluding payout time!"%(farm_time))
                    flag = True
                    break
            inc += 1
        return payout_times
    
    def upgrade(self, time, info, mode = 'Upgrades'):
        # There are two modes for upgrading:
        # 'Upgrades': info is a tuple saying the new upgrades for the farm
        # 'Path': info is an integer 0,1, or 2 specifying the path to upgrade
        
        # In order to perform the initilization checks when a farm is upgraded to x3x or higher, 
        # I need to have both the new and old farm upgrade information on hand at any given point. 
        upgrades = copy.deepcopy(self.upgrades)

        if mode == 'Upgrades':
            #Expense tracking
            self.expenses = farm_total_cost_values[info]
            #Update the upgrade info
            for i in range(3):
                upgrades[i] = info[i]

        elif mode == 'Path':
            #Expense tracking
            self.expenses += farm_upgrades_costs[info][self.upgrades[info]]
            #Update the upgrade info
            upgrades[info] += 1

        #Update the payout information of the farm
        self.payout_amount = farm_payout_values[tuple(upgrades)][0]
        self.payout_frequency = farm_payout_values[tuple(upgrades)][1]
        
        #So that we can accurately track payments for the farm
        self.purchase_time = time
        
        #Update the sellback value of the farm
        self.sell_value = farm_sellback_values[tuple(upgrades)]
        
        #If the resulting farm is a Monkey Bank, indicate as such and set its max account value appropriately
        if upgrades[1] >= 3 and self.upgrades[1] < 3:
            self.bank = True
            self.max_account_value = farm_bank_capacity[self.upgrades[1]]
            # self.logs.append("The new farm is a bank! The bank's max capacity is %s"%(farm.max_account_value))
            
        #If the resulting farm is an IMF Loan or Monkeyopolis, determine the earliest time the loan can be used
        if upgrades[1] >= 4 and self.upgrades[1] < 4:
            self.min_use_time = time + farm_globals['Monkeynomics Initial Cooldown']

        self.upgrades = upgrades

    def overclock(self, time):
        #What tier of farm do we have right now?
        tier = max(self.upgrades[0],self.upgrades[1], self.upgrades[2])
        uptime = 105 - 15*tier
        self.overclock_expiration_time = time + uptime

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        if self.sell_time and other.sell_time:
            #Two farms that are sold are considered equal
            return True
        
        # Two active farms are considered the same if their upgrades are the same
        return self.upgrades == other.upgrades
    
    def __repr__(self):
        if self.sell_time:
            end_str = "INACTIVE"
        else:
            end_str = "ACTIVE"

        return "(%s,%s,%s) Farm %s"%(self.upgrades[0], self.upgrades[1], self.upgrades[2],end_str)