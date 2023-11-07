#DEFINITIONS OF THE 
import copy
from b2sim.info import *

class MonkeyFarm():
    def __init__(self, initial_state):
        
        ###############
        #BASIC FEATURES
        ###############
        
        #self.upgrades is an array [i,j,k] representing the upgrade state of the farm
        #EXAMPLE: [4,2,0] represents a Banana Research Facility with Valuable Bananas
        
        self.upgrades = list(initial_state.get('Upgrades')) #This must be a list because I need to modify this when the farm is upgraded!
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