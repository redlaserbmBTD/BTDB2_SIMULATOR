# %% [markdown]
# # Preliminaries

# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import b2sim.farm_init

# %% [markdown]
# ## TODO:
# 
# Features to add in the future, (listed in no particular order):
# 1. When initializing banks, the code implicitly assumes the bank has made 0 dollars worth of deposits prior to the initial time state. Add functionality which allows for bank account amounts (assuming no withdrawals) to be automatically computed.
# 2. More robust data visualization
# 3. Add support for boat farms/heli farms/druid farms.
# 4. Implement fail-safes to prevent the user from eco'ing disabled eco sends.
# 5. Add support for a proper eco queue which accounts for "queue overloading" and "unloading"
# 
# Ideas for data visualization:
# 1. Show explicitly on the graphs when a change was made in the buy queue or the eco queue.
# 2. Bar graph showing how much money each farm has made
# 3. Selling power over time

# %% [markdown]
# ## Eco Send Info

# %%
#The formatting of the tuples is (eco_cost, eco_gain)

# %% [markdown]
# ## Monkey Farm Info
# 
# To build the MonkeyFarm class, we need the following global info for farms:
# 1. Upgrade costs for farms
# 2. Resell values for farms
# 3. Payout info for farms
# 
# Unforunately, the recording of data necessary for farms is quite involved!

# %%
farm_upgrades_costs = b2sim.farm_init.farm_upgrades_costs
farm_bank_capacity = b2sim.farm_init.farm_bank_capacity
farm_payout_values = b2sim.farm_init.farm_payout_values
farm_sell_values = b2sim.farm_init.farm_sellback_values

eco_send_info = b2sim.farm_init.eco_send_info

# %% [markdown]
# # Boat Farm Info
# 
# Thankfully this information is not *as* intensive to collect!

# %%
boat_upgrades_costs = [5400, 19000]
boat_payout_values = [300, 1000, 3000]
boat_sell_values = [1960, 6560, 21760]

# %% [markdown]
# # Game State Class

# %% [markdown]
# The game state class is an instance of battles 2 in action! 

# %%
def impact(cash, loan, amount):
    #If the amount is positive (like a payment), half of the payment should be directed to the outstanding loan
    #If the amount is negative (like a purhcase), then we can treat it "normally"
    if amount > 0:
        if amount > 2*loan:
            cash = cash + amount - loan
            loan = 0
        else:
            cash = cash + amount/2
            loan = loan - amount/2
    else: 
        cash = cash + amount
    return cash, loan

def writeLog(lines, filename = 'log', path = 'logs/'):
    with open(path + filename + '.txt', 'w') as f:
        for line in lines:
            f.write(line)
            f.write('\n')

# %%
class GameState():
    def __init__(self, initial_state):
        
        ############################
        #INITIALIZING THE GAME STATE
        ############################
        
        #To ensure the code runs properly, we'll create a log file to track cash and eco as they evolve over time
        self.logs = []
        
        #Initial cash and eco and loan values
        self.cash = initial_state.get('Cash')
        self.eco = initial_state.get('Eco')
        self.loan = initial_state.get('Loan') #For IMF Loans
        
        #Eco send info
        self.send_name = initial_state.get('Eco Send')
        if self.send_name is None:
            self.send_name = 'Zero'
        
        try:
            self.eco_cost = eco_send_info[self.send_name]['Price']
            self.eco_gain = eco_send_info[self.send_name]['Eco']
            self.eco_time = eco_send_info[self.send_name]['Send Duration']
        except:
            self.send_name = 'Zero'
            self.eco_cost = 0
            self.eco_gain = 0
        
        #~~~~~~~~~~~~~~~~~
        #ROUND LENGTH INFO
        #~~~~~~~~~~~~~~~~~
        
        #Initialize round length info
        self.rounds = initial_state.get('Rounds')
        
        # If the user specifies a starting round instead of a starting time, convert it to a starting time
        # self.current_time is a nonnegative real number telling us how much game time has elapsed
        # self.current_round is an integer telling us what round we're currently on
        # NOTE: In the initial state, the player can specify a decimal value for rounds. A 'Game Round' of 19.5 means "halfway through Round 19" for instance.
        
        if initial_state.get('Game Round') is not None:
            starting_round = initial_state.get('Game Round')
            self.current_time = self.rounds.getTimeFromRound(starting_round)
            self.current_round = int(np.floor(starting_round))
        else:
            self.current_time = initial_state.get('Game Time')
            self.current_round = self.rounds.getRoundFromTime(self.current_time)
        
        #~~~~~~~
        #LOGGING
        #~~~~~~~

        #As the Game State evolves, I'll use these arrays to track how cash and eco have changed over time
        self.time_states = [self.current_time]
        self.cash_states = [self.cash] 
        self.eco_states = [self.eco]

        #These lists will hold tuples (time, message)
        self.buy_messages = []
        self.eco_messages = []
        
        #~~~~~~~~~~~~~~~
        #FARMS & ALT-ECO
        #~~~~~~~~~~~~~~~
        
        #Process the initial info given about farms/alt-eco:
        
        #Info for whether T5 Farms are up or not
        self.T5_exists = [False, False, False]
        
        #First, farms!
        self.farms = {}
        farm_info = initial_state.get('Farms')
        self.key = 0
        if farm_info is not None:
            for key in farm_info.keys():
                if key >= self.key:
                    self.key = key+1

                farm_dict = farm_info[key]
                self.farms[key] = MonkeyFarm(farm_dict)
                
                #If the farm is a T5 farm, modify our T5 flags appropriately
                #Do not allow the user to initialize with multiple T5's
                for i in range(3):
                    if self.farms[key].upgrades[i] == 5 and self.T5_exists[i] == False:
                        self.T5_exists[i] = True
                    elif self.farms[key].upgrades[i] == 5 and self.T5_exists[i] == True:
                        self.farms[key].upgrades[i] = 4

        #Next, boat farms!
        self.boat_farms = initial_state.get('Boat Farms')
        self.Tempire_exists = False
        self.boat_key = 0
        if self.boat_farms is not None:
            for key in boat_farms.keys():
                if key >= self.key:
                    self.key = key+1

                boat_farm = self.boat_farms[key]
                #If the boat farm is a Tempire, mark it as such appropriately.
                #Do not allow the user to initialize with multiple Tempires!
                if boat_farm['Upgrade'] == 5 and self.Tempire_exists[i] == False:
                    self.Tempire_exists = True
                elif boat_farm['Upgrade'] == 5 and self.Tempire_exists[i] == True:
                    boat_farm['Upgrade'] = 4

        #Next, druid farms!
        self.druid_farms = initial_state.get('Druid Farms')
        if self.druid_farms is not None:
            self.sotf = self.druid_farms['Spirit of the Forest Index']
            self.druid_key = len(self.druid_farms) - 2
        else:
            self.sotf = None
            self.druid_key = 0
        
        if self.sotf is not None:
            self.sotf_min_use_time = self.druid_farms[self.sotf] + 15
        else:
            self.sotf_min_use_time = None

        #Next, supply drops!
        self.supply_drops = initial_state.get('Supply Drops')
        if self.supply_drops is not None:
            self.elite_sniper = self.supply_drops['Elite Sniper Index']
            self.sniper_key = len(self.supply_drops) - 2
        else:
            self.elite_sniper = None
            self.sniper_key = 0
        
        #~~~~~~~~~~~~~~~~
        #THE QUEUE SYSTEM
        #~~~~~~~~~~~~~~~~
        
        #Eco queue info
        self.eco_queue = initial_state.get('Eco Queue')
        
        #Upgrade queue
        self.buy_queue = initial_state.get('Buy Queue')
        self.buy_cost = None
        self.buffer = 0
        self.min_buy_time = None

        #Attack queue - This is the list of bloons in the center of the screen that pops up whenever you send eco
        self.attack_queue = []
        self.attack_queue_unlock_time = self.current_time
        self.eco_delay = 1.0/30.0

        #For repeated supply drop buys
        self.supply_drop_max_buy_time = -1
        self.supply_drop_buffer = 0

        #For repeated druid farm buys
        self.druid_farm_max_buy_time = -1
        self.druid_farm_buffer = 0

        #~~~~~~~~~~
        #FAIL-SAFES
        #~~~~~~~~~~
        
        if self.farms is None:
            self.farms = {}
        if self.buy_queue is None:
            self.buy_queue = []
        if self.eco_queue is None:
            self.eco_queue = []
        if self.loan is None:
            self.loan = 0
        if self.boat_farms is None:
            self.boat_farms = {}
            
        self.logs.append("MESSAGE FROM GameState.__init__(): ")
        self.logs.append("Initialized Game State!")
        self.logs.append("The current game round is %s"%(self.current_round))
        self.logs.append("The current game time is %s seconds"%(self.current_time))
        self.logs.append("The game round start times are given by %s \n"%(self.rounds.round_starts))
        
    def viewCashEcoHistory(self, dim = (15,18)):
        self.logs.append("MESSAGE FROM GameState.viewCashEcoHistory():")
        self.logs.append("Graphing history of cash and eco!")

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #Graph the cash and eco values over time
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        fig, ax = plt.subplots(2)
        fig.set_size_inches(dim[0],dim[1])
        ax[0].plot(self.time_states, self.cash_states, label = "Cash")
        ax[1].plot(self.time_states, self.eco_states, label = "Eco")
        
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #Mark where the rounds start
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        cash_min = min(self.cash_states)
        eco_min = min(self.eco_states)
        
        cash_max = max(self.cash_states)
        eco_max = max(self.eco_states)

        round_to_graph = self.rounds.getRoundFromTime(self.time_states[0]) + 1
        while self.rounds.round_starts[round_to_graph] <= self.time_states[-1]:
            ax[0].plot([self.rounds.round_starts[round_to_graph], self.rounds.round_starts[round_to_graph]],[cash_min-1, cash_max+1], label = "R" + str(round_to_graph) + " start", linestyle='dotted', color = 'k')
            ax[1].plot([self.rounds.round_starts[round_to_graph], self.rounds.round_starts[round_to_graph]],[eco_min-1, eco_max+1], label = "R" + str(round_to_graph) + " start", linestyle='dotted', color = 'k')
            round_to_graph += 1

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #Mark where purchases in the buy queue and eco queue occurred
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        for message in self.buy_messages:
            if message[2] == 'Eco':
                line_color = 'b'
            elif message[2] == 'Buy':
                line_color = 'r'

            if len(message[1]) > 30:
                thing_to_say = message[1][0:22] + '...'
            else:
                thing_to_say = message[1]
            
            ax[0].plot([message[0],message[0]],[cash_min-1, cash_max+1], label = thing_to_say, linestyle = 'dashed', color = line_color)
            ax[1].plot([message[0],message[0]],[eco_min-1, eco_max+1], label = thing_to_say, linestyle = 'dashed', color = line_color)

        #~~~~~~~~~~~~~~~~
        #Label the graphs
        #~~~~~~~~~~~~~~~~

        ax[0].set_title("Cash vs Time")
        ax[1].set_title("Eco vs Time")
        
        ax[0].set_ylabel("Cash")
        ax[1].set_ylabel("Eco")
        
        ax[1].set_xlabel("Time (seconds)")
        
        ax[0].legend(bbox_to_anchor = (1.02, 1))
        ax[1].legend(bbox_to_anchor = (1.02, 1))
        
        fig.tight_layout()
        self.logs.append("Successfully generated graph! \n")
    
    def changeStallFactor(self,stall_factor):
        #This is just a helper function
        self.rounds.changeStallFactor(stall_factor,self.current_time)

    def ecoQueueCorrection(self):
        #Check whether the next item in the eco queue is valid.
        future_flag = False
        while len(self.eco_queue) > 0 and future_flag == False:
            break_flag = False
            while len(self.eco_queue) > 0 and break_flag == False:
                #print("length of queue: %s"%(len(self.eco_queue)))
                #Is the eco send too late?
                if self.eco_queue[0][0] >= self.rounds.getTimeFromRound(eco_send_info[self.eco_queue[0][1]]['End Round']+1):
                    #Yes, the send is too late.
                    self.logs.append("Warning! Time %s is too late to call %s. Removing from eco queue"%(self.eco_queue[0][0],self.eco_queue[0][1]))
                    self.eco_queue.pop(0)
                    
                else:
                    #No, the send is not too late
                    
                    #Is the eco send too early?
                    candidate_time = self.rounds.getTimeFromRound(eco_send_info[self.eco_queue[0][1]]['Start Round'])
                    if self.eco_queue[0][0] < candidate_time:
                        #Yes, the send is too early
                        self.logs.append("Warning! Time %s is too early to call %s. Adjusting the queue time to %s"%(self.eco_queue[0][0],self.eco_queue[0][1], candidate_time))
                        self.eco_queue[0] = (candidate_time, self.eco_queue[0][1])
                        #Is the adjusted time still valid?
                        if len(self.eco_queue) < 2 or self.eco_queue[0][0] < self.eco_queue[1][0]:
                            #Yes, it's still valid
                            break_flag = True
                        else:
                            #No, it's not valid
                            self.logs.append("Warning! Time %s is too late to call %s because the next item in the eco queue is slated to come earlier. Removing from eco queue"%(self.eco_queue[0][0],self.eco_queue[0][1]))
                            self.eco_queue.pop(0)
                    else:
                        #No, the send is not too early
                        break_flag = True
            
            if len(self.eco_queue) > 0 and self.eco_queue[0][0] <= self.current_time:
                self.changeEcoSend(self.eco_queue[0][1])
                self.eco_queue.pop(0)
            else:
                future_flag = True
        
    def changeEcoSend(self,send_name):
        #TODO: Implement safeguards to prevent the player from changing to an eco send that is unavailable
        self.eco_cost = eco_send_info[send_name]['Price']
        self.eco_gain = eco_send_info[send_name]['Eco']
        self.eco_time = eco_send_info[send_name]['Send Duration']

        self.send_name = send_name
        self.logs.append("Modified the eco send to %s"%(send_name))

    def showWarnings(self,warnings):
        for index in warnings:
            print(self.logs[index])
        
    def fastForward(self, target_time = None, target_round = None, interval = 0.1):
        self.logs.append("MESSAGE FROM GameState.fastForward: ")

        #Collect a list of indices corresponding to log messages the player should know about.
        #Useful for when the user inputs incorrect data or gets unexpected results.
        self.warnings = []
        self.valid_action_flag = True #To prevent the code from repeatedly trying to perform a transaction that obviously can't happen
        
        # If a target round is given, compute the target_time from that
        if target_round is not None:
            target_time = self.rounds.getTimeFromRound(target_round)
            
        #A fail-safe to prevent the code from trying to go backwards in time
        if target_time < self.current_time:
            target_time = self.current_time
        
        while self.current_time < target_time:
            intermediate_time = min(max(np.floor(self.current_time/interval + 1)*interval,self.current_time + interval/2),target_time)
            self.logs.append("Advancing game to time %s"%(np.round(intermediate_time,3)))
            self.advanceGameState(target_time = intermediate_time)
            self.logs.append("----------")

        #FOR SPOONOIL: Show warning messages for fail-safes triggered during simulation
        self.showWarnings(self.warnings)
        
        self.logs.append("Advanced game state to round " + str(self.current_round))
        self.logs.append("The current time is " + str(self.current_time))
        self.logs.append("The next round starts at time " + str(self.rounds.round_starts[self.current_round+1]))
        self.logs.append("Our new cash and eco is given by (%s,%s) \n"%(np.round(self.cash,2),np.round(self.eco,2)))

    def advanceGameState(self, target_time = None, target_round = None):
        #self.logs.append("MESSAGE FROM GameState.advanceGameState: ")
        # Advance the game to the time target_time, 
        # computing the new money and eco amounts at target_time
        
        # FAIL-SAFE
        self.ecoQueueCorrection()
        
        # FAIL-SAFE: Terminate advanceGameState early if an eco change is scheduled before the target_time.
        if len(self.eco_queue) > 0 and self.eco_queue[0][0] < target_time:
            #Yes, an eco change will occur
            target_time = self.eco_queue[0][0]

        # FAIL-SAFE: Check whether the current eco send is valid. If it is not, change the eco send to zero.
        if eco_send_info[self.send_name]['End Round'] < self.current_round:
            self.logs.append("Warning! The eco send %s is no longer available! Switching to the zero send."%(self.send_name))
            self.warnings.append(len(self.logs) - 1)
            self.changeEcoSend('Zero')
            self.buy_messages.append((self.current_time, 'Change eco to %s'%(self.send_name), 'Eco'))

        # FAIL-SAFE: Prevent advanceGameState from using an eco send after it becomes unavailable by terminating early in this case.
        if eco_send_info[self.send_name]['End Round'] + 1 <= self.rounds.getRoundFromTime(target_time):
            target_time = self.rounds.getTimeFromRound(eco_send_info[self.send_name]['End Round'] + 1)
            self.logs.append("Warning! The current eco send will not be available after the conclusion of round %s. Adjusting the target time."%(eco_send_info[self.send_name]['End Round']))

        # FAIL-SAFE: Only try to update if we are trying to go into the future. Do NOT try to go back in time!
        if target_time <= self.current_time:
            self.logs.append("Warning! The target time is in the past! Terminating advanceGameState()")
            self.warnings.append(len(self.logs) - 1)
            return None
        
        ############################################
        #PART 1: COMPUTATION OF PAYOUT TIMES & INFOS
        ############################################
        
        #Entries in payout_times take the format of a dictionary with paramters 'Time' and 'Payment' (if possible).
        
        payout_times = self.computePayoutSchedule(target_time)

        ##############################
        #PART 2: COMPUTATION OF WEALTH
        ##############################
        
        #Now that payouts are sorted, award them in the order they are meant to be awarded in.
        #This is essential for the correct computation of wealth gained over the given time period.
        
        time = self.current_time
        for i in range(len(payout_times)):
            payout = payout_times[i]
            
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            #First, compute the impact of eco in between payouts
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

            while self.attack_queue_unlock_time < payout['Time'] and self.send_name != 'Zero':

                # First, check if we can remove any items from the attack queue
                for attack_end in self.attack_queue:
                    if self.attack_queue_unlock_time >= attack_end:
                        self.attack_queue.remove(attack_end)
                
                # Next, try to add an attack to the attack_queue.
                # Can we send an attack?
                if self.cash >= self.eco_cost and len(self.attack_queue) < 6:
                    # Yes, the queue is empty and we have enough cash
                    if len(self.attack_queue) == 0:
                        self.attack_queue.append(time + self.eco_time)
                    else:
                        self.attack_queue.append(self.attack_queue[-1] + self.eco_time)
                    self.cash -= self.eco_cost
                    self.eco += self.eco_gain
                    self.attack_queue_unlock_time += self.eco_delay

                elif len(self.attack_queue) == 6:
                    # No, the queue is full!
                    self.attack_queue_unlock_time = max(self.attack_queue[0], self.attack_queue_unlock_time)

                elif self.cash < self.eco_cost:
                    # No, we don't have money!
                    self.attack_queue_unlock_time = max(payout['Time'], self.attack_queue_unlock_time)
            
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
            #Next, award the payout at the given time
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            
            # WARNING! If an IMF Loan is active, half of the payment must go towards the loan.
            
            if payout['Payout Type'] == 'Direct':
                #This case is easy! Just award the payment and move on
                self.cash, self.loan = impact(self.cash,self.loan, payout['Payout'])
                self.logs.append("Awarded direct payment %s at time %s"%(np.round(payout['Payout'],2),np.round(payout['Time'],2)))
            elif payout['Payout Type'] == 'Bank Payment':
                #Identify the bank that we're paying and deposit money into that bank's account
                #NOTE: Bank deposits are not impacted by IMF Loans. It is only when we withdraw the money that the loan is repaid
                key = payout['Index']
                farm = self.farms[key]
                farm.account_value += payout['Payout']
                self.logs.append("Awarded bank payment %s at time %s to farm at index %s"%(np.round(payout['Payout'],2),np.round(payout['Time'],2), key))
                if farm.account_value > farm.max_account_value:
                    #At this point, the player should withdraw from the bank. T
                    farm.account_value = 0
                    self.cash, self.loan = impact(self.cash,self.loan,farm.max_account_value)
                    self.logs.append("The bank at index %s reached max capacity! Withdrawing money"%(key))
                self.logs.append("The bank's new account value is %s"%(farm.account_value))
            elif payout['Payout Type'] == 'Bank Interest':
                #Identify the bank that we're paying and deposit $400, then give 20% interest
                key = payout['Index']
                farm = self.farms[key]
                farm.account_value += 400
                farm.account_value *= 1.2
                self.logs.append("Awarded bank interest at time %s to the farm at index %s"%(np.round(payout['Time'],2), key))
                if farm.account_value > farm.max_account_value:
                    farm.account_value = 0
                    self.cash, self.loan = impact(self.cash,self.loan,farm.max_account_value)
                    self.logs.append("The bank at index %s reached max capacity! Withdrawing money"%(key))
                self.logs.append("The bank's new account value is %s"%(farm.account_value))
            elif payout['Payout Type'] == 'Eco':
                self.cash, self.loan = impact(self.cash,self.loan, self.eco)
                self.logs.append("Awarded eco payment %s at time %s"%(np.round(self.eco,2),np.round(payout['Time'],2)))
            
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            #Now, check whether we can perform the next buy in the buy queue
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            
            # The simulation should attempt to process the buy queue after every purchase, *except* if multiple payouts occur at the same time
            # If multiple payouts occur at the same time, only access the buy queue after the *last* of those payments occurs.

            made_purchase = False
            try_to_buy = False

            if i == len(payout_times)-1:
                try_to_buy = True
            elif payout_times[i]['Time'] < payout_times[i+1]['Time']:
                try_to_buy = True
            
            if try_to_buy == True:
                made_purchase = self.processBuyQueue(payout)
            
            #~~~~~~~~~~~~~~~~~~~~
            # Automated Purchases
            #~~~~~~~~~~~~~~~~~~~~

            # There are actions in actions.py which let the player trigger the action of repeatedly buying supply drops or druid farms.
            # These while loops process *those* transactions independently of the buy queue.
            # WARNING: Unusual results will occur if you attempt to implement automated purchases of multiple alt eco's at the same time.
            # WARNING: Because automated purchases are processed after checking the buy queue, unexpected results may occur if items in the buy queue do not have a min_buy_time designated.

            if payout['Time'] <= self.supply_drop_max_buy_time and try_to_buy == True:
                while self.cash >= 9650 + self.supply_drop_buffer:
                    made_purchase = True
                    self.cash -= 9650
                    self.supply_drops[self.sniper_key] = payout['Time']
                    self.sniper_key += 1
                    self.logs.append("Purchased a supply drop! (Automated purchase)")

            if payout['Time'] <= self.druid_farm_max_buy_time and try_to_buy == True:
                while self.cash >= 4675 + self.druid_farm_buffer:
                    made_purchase = True
                    self.cash -= 4675
                    self.druid_farm[self.druid_key] = payout['Time']
                    self.druid_key += 1
                    self.logs.append("Purchased a druid farm!")
            
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            #Record the cash & eco history and advance the game time
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            
            #print("New cash and eco is (%s,%s)"%(np.round(self.cash,2), np.round(self.eco,2)))
            self.time_states.append(payout['Time'])
            self.cash_states.append(self.cash)
            self.eco_states.append(self.eco)
            self.logs.append("Recorded cash and eco values (%s,%s) at time %s"%(np.round(self.cash,2),np.round(self.eco,2),np.round(payout['Time'],2)))
            
            time = payout['Time']

            #If a purchase occured in the buy queue, exit the processing of payments early
            if made_purchase == True:
                target_time = time
                break

            #end of for loop
        
        # After going through the for loop, we have accounted for all payments that could occur in the time period of interest
        # and also performed any purchases in our buy queue along the way. 
            
        ####################################
        #PART 3: UPDATE GAME TIME PARAMETERS
        ####################################
        
        #Determine the round we are in now
        self.current_time = target_time
        while self.rounds.round_starts[self.current_round] <= self.current_time:
            self.current_round += 1
        self.current_round -= 1
        
        #Update the eco send, if necessary
        if len(self.eco_queue) > 0 and target_time >= self.eco_queue[0][0]:
            self.changeEcoSend(self.eco_queue[0][1])
            self.buy_messages.append((self.current_time, 'Change eco to %s'%(self.send_name), 'Eco'))
            self.eco_queue.pop(0)
        
        #self.logs.append("Advanced game state to round " + str(self.current_round))
        #self.logs.append("The current time is " + str(self.current_time))
        #self.logs.append("The next round starts at time " + str(self.rounds.round_starts[self.current_round+1]))
        #self.logs.append("Our new cash and eco is given by (%s,%s) \n"%(np.round(self.cash,2),np.round(self.eco,2)))
           
    def computePayoutSchedule(self, target_time):
        # Helper method for advanceGameState
        # Given a target time target_time, return an order list of all payouts to occur from the game state's current time until the designated target time.
        # Each entry in the returned array is a dictionary detailing the time the payment is to occur and either the payment to give or instructions to compute that payment (necessary for eco for banks)

        payout_times = []
        
        #First, let's identify payouts from eco
        eco_time = 6*(np.floor(self.current_time/6)+1)
        while eco_time <= target_time:
            payout_entry = {
                'Time': eco_time,
                'Payout Type': 'Eco'
            }
            payout_times.append(payout_entry)
            eco_time += 6

        #Next, let's do druid farms!
        if self.druid_farms is not None:
            for key in self.druid_farms.keys():
                druid_farm = self.druid_farms[key]
                if key != self.sotf:
                    #Determine the earliest druid farm activation that could occur within the interval of interest (self.current_time,target_time]
                    use_index = max(1,np.floor(1 + (self.current_time - druid_farm - 15)/40)+1)
                    druid_farm_time = druid_farm + 15 + 40*(use_index-1)
                    while druid_farm_time <= target_time:
                        payout_entry = {
                            'Time': druid_farm_time,
                            'Payout Type': 'Direct',
                            'Payout': 1000
                        }
                        payout_times.append(payout_entry)
                        druid_farm_time += 40
                elif key == self.sotf:
                    #Spirit of the Forest has a start of round payment of 3000 dollars and an "optional" active that is used 
                    #At the start of each round, append a payout entry with the SOTF payout
                    self.inc = 1
                    while self.rounds.getTimeFromRound(self.current_round + self.inc) <= target_time:
                        payout_entry = {
                            'Time': self.rounds.getTimeFromRound(self.current_round + self.inc),
                            'Payout Type': 'Direct',
                            'Payout': 3000
                        }
                        payout_times.append(payout_entry)
                        self.inc += 1


        #Next, let's do supply drops
        if self.supply_drops is not None:
            for key in self.supply_drops.keys():
                supply_drop = self.supply_drops[key]
                if key == self.elite_sniper:
                    payout_amount = 5000
                else:
                    payout_amount = 2000

                #Determine the earliest supply drop activation that could occur within the interval of interest (self.current_time,target_time]
                drop_index = max(1,np.floor(1 + (self.current_time - supply_drop - 15)/40)+1)
                supply_drop_time = supply_drop + 15 + 40*(drop_index-1)
                while supply_drop_time <= target_time:
                    
                    payout_entry = {
                        'Time': supply_drop_time,
                        'Payout Type': 'Direct',
                        'Payout': payout_amount
                    }
                    payout_times.append(payout_entry)
                    supply_drop_time += 40
                    
        #Next, let's do farms!
        if len(self.farms) > 0:
            for key in self.farms.keys():
                farm = self.farms[key]
                #If the farm is a monkeyopolis, determine the payout times of the active ability
                if farm.upgrades[1] == 5:
                    farm_time = farm.min_use_time
                    while farm_time <= target_time:
                        if farm_time > self.current_time:
                            payout_entry = {
                                'Time': farm_time,
                                'Payout Type': 'Direct',
                                'Payout': 20000
                            }
                            payout_times.append(payout_entry)
                        farm_time += 60
                    farm.min_use_time = farm_time
                
                farm_purchase_round = self.rounds.getRoundFromTime(farm.purchase_time)
                self.inc = 0
                self.flag = False
                while self.flag == False:
                    #If computing farm payments on the same round as we are currently on, precompute the indices the for loop should go through.
                    #NOTE: This is not necessary at the end because the for loop terminates when a "future" payment is reached.
                    if self.inc == 0:
                        if self.current_round > farm_purchase_round:
                            #When the farm was purchased on a previous round
                            round_time = self.current_time - self.rounds.round_starts[self.current_round]
                            loop_start = int(np.floor(farm.payout_frequency*round_time/self.rounds.nat_send_lens[self.current_round]) + 1)
                            loop_end = farm.payout_frequency
                        else: #self.current_round == farm_purhcase_round
                            #When the farm was purchased on the same round as we are currently on
                            loop_start = int(np.floor(farm.payout_frequency*(self.current_time - farm.purchase_time)/self.rounds.nat_send_lens[self.current_round]-1)+1)
                            loop_end = int(np.ceil(farm.payout_frequency*(1 - (farm.purchase_time - self.rounds.round_starts[self.current_round])/self.rounds.nat_send_lens[self.current_round])-1)-1)
                    else:
                        loop_start = 0
                        loop_end = farm.payout_frequency
                    
                    #self.logs.append("Precomputed the loop indices to be (%s,%s)"%(loop_start,loop_end))
                    #self.logs.append("Now computing payments at round %s"%(self.current_round + self.inc))
                    
                    for i in range(loop_start, loop_end):
                        #Precompute the value i that this for loop should start at (as opposed to always starting at 0) to avoid redundant computations
                        #Farm payout rules are different for the round the farm is bought on versus subsequent rounds
                        if self.current_round + self.inc == farm_purchase_round:
                            farm_time = farm.purchase_time + (i+1)*self.rounds.nat_send_lens[self.current_round + self.inc]/farm.payout_frequency
                        else:
                            farm_time = self.rounds.round_starts[self.current_round + self.inc] + i*self.rounds.nat_send_lens[self.current_round + self.inc]/farm.payout_frequency
                        
                        #Check if the payment time occurs within our update window. If it does, add it to the payout times list
                        if farm_time <= target_time and farm_time > self.current_time:
                            
                            #Farm payouts will either immediately be added to the player's cash or added to the monkey bank's account value
                            #This depends of course on whether the farm is a bank or not.
                            
                            #WARNING: If the farm we are dealing with a bank, we must direct the payment into the bank rather than the player.
                            #WARNING: If the farm we are dealing with is a MWS, we must check whether we are awarding the MWS bonus payment!
                            #WARNING: If the farm we are dealing with is a BRF, we must whether the BRF buff is being applied or not!
                            
                            if farm.upgrades[1] >= 3:
                                if i == 0 and self.current_round + self.inc > farm_purchase_round:
                                    #At the start of every round, every bank gets a $400 payment and then is awarded 20% interest.
                                    payout_entry = {
                                        'Time': farm_time,
                                        'Payout Type': 'Bank Interest',
                                        'Index': key,
                                    }
                                    payout_times.append(payout_entry)
                                payout_entry = {
                                    'Time': farm_time,
                                    'Payout Type': 'Bank Payment',
                                    'Index': key,
                                    'Payout': farm.payout_amount
                                }
                            elif i == 0 and farm.upgrades[2] == 5 and self.current_round + self.inc > farm_purchase_round:
                                payout_entry = {
                                    'Time': farm_time,
                                    'Payout Type': 'Direct',
                                    'Payout': farm.payout_amount + 10000
                                }
                            elif farm.upgrades[0] == 4 and self.T5_exists[0] == True:
                                payout_entry = {
                                    'Time': farm_time,
                                    'Payout Type': 'Direct',
                                    'Payout': farm.payout_amount*1.25
                                }
                            else:
                                payout_entry = {
                                    'Time': farm_time,
                                    'Payout Type': 'Direct',
                                    'Payout': farm.payout_amount
                                }
                            payout_times.append(payout_entry)
                        elif farm_time > target_time:
                            #self.logs.append("The payout time of %s is too late! Excluding payout time!"%(farm_time))
                            self.flag = True
                            break
                    self.inc += 1
        
        #Now, let's do boat farms!
        if len(self.boat_farms) > 0:

            #If the player has Trade Empire, determine the buff to be applied to other boat farm payments
            if self.Tempire_exists == True:
                arg = min(len(self.boat_farms) - 1,20)
            else:
                arg = 0
            multiplier = 1 + 0.05*arg

            #Determine the amount of the money the boats will give each round
            boat_payout = 0
            for key in self.boat_farms.keys():
                boat_farm = self.boat_farms[key]
                boat_payout += multiplier*boat_payout_values[boat_farm['Upgrade'] - 3]

            #At the start of each round, append a payout entry with the boat payout
            self.inc = 1
            while self.rounds.getTimeFromRound(self.current_round + self.inc) <= target_time:
                payout_entry = {
                    'Time': self.rounds.getTimeFromRound(self.current_round + self.inc),
                    'Payout Type': 'Direct',
                    'Payout': boat_payout
                }
                payout_times.append(payout_entry)
                self.inc += 1

        #This special payout prevents the code from waiting possibly several seconds to carry out purchases in the buy queue that can obviously be afforded
        payout_entry = {
            'Time': target_time,
            'Payout Type': 'Direct',
            'Payout': 0
        }
        payout_times.append(payout_entry)

        #Now that we determined all the payouts, sort the payout times by the order they occur in
        payout_times = sorted(payout_times, key=lambda x: x['Time']) 
        #self.logs.append("Sorted the payouts in order of increasing time!")

        return payout_times

    def processBuyQueue(self, payout):
        # Helper function for advanceGameState
        
        made_purchase = False
        buy_message_list = []
        
        # DEVELOPER'S NOTE: It is possible for the queue to be empty but for there to still be purchases to be performed (via automated purchases)
        while len(self.buy_queue) > 0 and self.valid_action_flag == True:
            
            # To begin, pull out the first item in the buy queue and determine the hypothetical cash and loan amounts 
            # if this transaction was performed, as well as the minimum buy time for the transaction.
            
            h_cash = self.cash
            h_loan = self.loan
            self.buffer = 0
            
            # Let's start by determining the minimum buy time.
            # NOTE: Only one object in purchase info should have minimum buy time info
            # If there are multiple values, the code will pick the latest value

            purchase_info = self.buy_queue[0]
            
            if self.min_buy_time is None:
                self.min_buy_time = 0
                # DEVELOPER NOTE: self.min_buy_time is initialized as None and set to None following the completion of a purhcase in the buy queue
                # This if condition prevents the redundant computation.
                for dict_obj in purchase_info:
                    min_buy_time = dict_obj.get('Minimum Buy Time')
                    if min_buy_time is not None:
                        if min_buy_time > self.min_buy_time:
                            self.min_buy_time = min_buy_time

                    #If the dict_obj is an IMF Loan activation, force self.min_buy_time to be at least the min_use_time of the loan
                    if dict_obj['Type'] == 'Activate IMF':
                        ind = dict_obj['Index']
                        farm = self.farms[ind]
                        if farm.min_use_time is not None and farm.min_use_time > self.min_buy_time:
                            self.min_buy_time = farm.min_use_time
                        elif farm.min_use_time is None:
                            #If the farm doesn't have a min_use_time designated, it can't be an IMF farm!
                            self.logs.append("Warning! Buy queue entry includes attempt to take out a loan from a farm that is not an IMF Loan! Aborting buy queue!")
                            self.warnings.append(len(self.logs)-1)
                            self.valid_action_flag = False
                            break
                    
                    #If the dict_obj is a SOTF use, force self.min_buy_time to be at least be the self.sotf_min_use_time
                    if dict_obj['Type'] == 'Use Spirit of the Forest':
                        if self.sotf_min_use_time is not None and self.sotf_min_use_time > self.min_buy_time:
                            self.min_buy_time = self.sotf_min_use_time
                        elif self.sotf_min_use_time is None:
                            #Do not attempt to use SOTF if we don't have SOTF
                            self.logs.append("Warning! Buy queue entry includes attempt to use Spirit of the Forest when it is not in play! Aborting buy queue!")
                            self.warnings.append(len(self.logs)-1)
                            self.valid_action_flag = False
                            break
                    
                self.logs.append("Determined the minimum buy time of the next purchase to be %s"%(self.min_buy_time))
                        
            # If we have not yet reached the minimum buy time, break the while loop. 
            # We will check this condition again later:
            if payout['Time'] < self.min_buy_time:
                break
            
            #Next, let's compute the cash and loan values we would have if the transaction was performed
            #We will also take the opportunity here to form the message that gets sent to the graph for viewCashEcoHistory
            
            for dict_obj in purchase_info:

                # DEFENSE RELATED MATTERS
                if dict_obj['Type'] == 'Buy Defense':
                    h_cash, h_loan = impact(h_cash, h_loan, -1*dict_obj['Cost'])
                    
                # FARM RELATED MATTERS
                elif dict_obj['Type'] == 'Buy Farm':
                    h_cash, h_loan = impact(h_cash, h_loan, -1000)
                elif dict_obj['Type'] == 'Upgrade Farm':
                    ind = dict_obj['Index']
                    path = dict_obj['Path']
                    farm = self.farms[ind]
                    #The following code prevents from the player from having multiple T5's in play
                    if farm.upgrades[path]+1 == 5 and self.T5_exists[path] == True:
                        self.logs.append("WARNING! Tried to purchase a T5 farm when one of the same kind already existed! Aborting buy queue!")
                        self.warnings.append(len(self.logs)-1)
                        self.valid_action_flag = False
                        break
                    h_cash, h_loan = impact(h_cash, h_loan, -1*farm_upgrades_costs[path][farm.upgrades[path]])
                elif dict_obj['Type'] == 'Sell Farm':
                    ind = dict_obj['Index']
                    farm = self.farms[ind]
                    h_cash, h_loan = impact(h_cash, h_loan, farm_sell_values[tuple(farm.upgrades)])
                elif dict_obj['Type'] == 'Withdraw Bank':
                    #WARNING: The farm in question must actually be a bank for us to perform a withdrawal!
                    #If it isn't, break the loop prematurely
                    ind = dict_obj['Index']
                    farm = self.farms[ind]
                    if farm.upgrades[1] < 3:
                        self.logs.append("WARNING! Tried to Withdraw from a farm that is not a bank! Aborting buy queue!")
                        self.warnings.append(len(self.logs)-1)
                        self.valid_action_flag = False
                        break
                    
                    h_cash, h_loan = impact(h_cash, h_loan, farm.account_value)

                elif dict_obj['Type'] == 'Activate IMF':
                    #WARNING: The farm in question must actually be an IMF Loan for us to use this ability!
                    #If it isn't, set a flag to False and break the loop.
                    #DEVELOPER'S NOTE: A farm that has a min_use_time is not necessarily an IMF loan, it could also be an Monkeyopolis
                    if farm.upgrades[1] != 4:
                        self.logs.append("WARNING! Tried to take out a loan from a farm that is not an IMF! Aborting buy queue!")
                        self.warnings.append(len(self.logs)-1)
                        self.valid_action_flag = False
                        break
                        
                    ind = dict_obj['Index']
                    farm = self.farms[ind]
                    
                    #When, a loan is activated, treat it like a payment, then add the debt
                    h_cash, h_loan = impact(h_cash, h_loan, 20000)
                    h_loan += 20000
                
                # BOAT FARM RELATED MATTERS
                elif dict_obj['Type'] == 'Buy Boat Farm':
                    h_cash, h_loan = impact(h_cash, h_loan, -2800)
                elif dict_obj['Type'] == 'Upgrade Boat Farm':
                    ind = dict_obj['Index']
                    boat_farm = self.boat_farms[ind]
                    #The following code prevents from the player from having multiple Trade Empires in play
                    if boat_farm['Upgrade']+1 == 5 and self.Tempire_exists == True:
                        self.logs.append("WARNING! Tried to purchase a Trade Empire when one already exists! Aborting buy queue!")
                        self.warnings.append(len(self.logs)-1)
                        self.valid_action_flag = False
                        break
                    upgrade_cost = boat_upgrades_costs[boat_farm['Upgrade']-3]
                    h_cash, h_loan = impact(h_cash, h_loan, -1*upgrade_cost)
                elif dict_obj['Type'] == 'Sell Boat Farm':
                    ind = dict_obj['Index']
                    boat_farm = self.boat_farms[ind]
                    h_cash, h_loan = impact(h_cash, h_loan, boat_sell_values[boat_farm['Upgrade']-3])

                # DRUID FARM RELATED MATTERS
                elif dict_obj['Type'] == 'Buy Druid Farm':
                    h_cash, h_loan = impact(h_cash, h_loan, -4675)
                elif dict_obj['Type'] == 'Sell Druid Farm':
                    if dict_obj['Index'] == self.sotf:
                        h_cash, h_loan = impact(h_cash, h_loan, 27772.5)
                    else:
                        h_cash, h_loan = impact(h_cash, h_loan, 3272.5)
                elif dict_obj['Type'] == 'Buy Spirit of the Forest':
                    #WARNING: There can only be one sotf at a time!
                    if self.sotf is not None:
                        self.logs.append("WARNING! Tried to purchase a Spirit of the Forest when one already exists! Aborting buy queue!")
                        self.warnings.append(len(self.logs)-1)
                        self.valid_action_flag = False
                        break
                    h_cash, h_loan = impact(h_cash, h_loan, -35000)
                elif dict_obj['Type'] == 'Use Spirit of the Forest':
                    #Whether or not SOTF is off cooldown is governed by the min_buy_time check
                    h_cash, h_loan = impact(h_cash, h_loan, 750)
                
                # SUPPLY DROP RELATED MATTERS
                elif dict_obj['Type'] == 'Buy Supply Drop':
                    h_cash, h_loan = impact(h_cash, h_loan, -9650)
                elif dict_obj['Type'] == 'Sell Supply Drop':
                    if dict_obj['Index'] == self.elite_sniper:
                        h_cash, h_loan = impact(h_cash, h_loan, 16555)
                    else:
                        h_cash, h_loan = impact(h_cash, h_loan, 6755)
                elif dict_obj['Type'] == 'Buy Elite Sniper':
                    #WARNING: There can only be one e-sniper at a time!
                    if self.elite_sniper is not None:
                        self.logs.append("WARNING! Tried to purchase an Elite Sniper when one already exists! Aborting buy queue!")
                        self.warnings.append(len(self.logs)-1)
                        self.valid_action_flag = False
                        break
                    h_cash, h_loan = impact(h_cash, h_loan, -14000)
                    
                #If at any point while performing these operations our cash becomes negative, then prevent the transaction from occurring:
                if h_cash < 0:
                    self.logs.append("WARNING! Reached negative cash while attempting the transaction!")
                    break

                #Read the buffer associated with the buy if any
                #NOTE: Only one object in purchase_info should have buffer info
                #If there are multiple buffers, the code rectifies the matter by
                #adding them all together
                if dict_obj.get('Buffer') is not None:
                    self.buffer += dict_obj.get('Buffer')
            
            #If the purchase sequence triggered a warning in the logs, do NOT perform it and break the while loop
            if self.valid_action_flag == False:
                break
            
            # Now, check if we are eligible to do the buy. 
            # Note at this point we have already checked whether we have reached the minimum time for the buy and also
            # we have already checked whether the buy item is valid. We now just need to check whether we have enough money!
            
            #self.logs.append("We have %s cash, but the next buy costs %s and has a buffer of %s and needs to be made on or after time %s!"%(np.round(self.cash,2), np.round(self.cash - h_cash,2),np.round(self.buffer,2), self.min_buy_time))
            if h_cash >= self.buffer:
                #If we do, perform the buy!
                made_purchase = True
                self.logs.append("We have %s cash! We can do the next buy, which costs %s and has a buffer of %s and a minimum buy time of %s!"%(np.round(self.cash,2), np.round(self.cash - h_cash,2),np.round(self.buffer,2),np.round(self.min_buy_time,2)))

                #Make the adjustments to the cash and loan amounts
                self.cash = h_cash
                self.loan = h_loan
                
                for dict_obj in purchase_info:

                    buy_message_list.append(dict_obj['Message'])
                    
                    #FARM RELATED MATTERS
                    if dict_obj['Type'] == 'Buy Farm':
                        self.logs.append("Purchasing farm!")
                        farm_info = {
                            'Purchase Time': self.current_time,
                            'Upgrades': [0,0,0]
                        }
                        farm = MonkeyFarm(farm_info)
                        
                        self.farms[self.key] = farm
                        self.key+= 1
                        
                    elif dict_obj['Type'] == 'Upgrade Farm':
                        ind = dict_obj['Index']
                        path = dict_obj['Path']
                        
                        self.logs.append("Upgrading path %s of the farm at index %s"%(path, ind))
                        farm = self.farms[ind]
                        farm.upgrades[path] += 1
                        
                        #Update the payout information of the farm
                        farm.payout_amount = farm_payout_values[tuple(farm.upgrades)][0]
                        farm.payout_frequency = farm_payout_values[tuple(farm.upgrades)][1]
                        
                        #So that we can accurately track payments for the farm
                        farm.purchase_time = payout['Time']
                        
                        #Update the sellback value of the farm
                        farm.sell_value = farm_sell_values[tuple(farm.upgrades)]
                        
                        self.logs.append("The new farm has upgrades (%s,%s,%s)"%(farm.upgrades[0],farm.upgrades[1],farm.upgrades[2]))
                        
                        #If the resulting farm is a Monkey Bank, indicate as such and set its max account value appropriately
                        if farm.upgrades[1] >= 3 and path == 1:
                            farm.bank = True
                            farm.max_account_value = farm_bank_capacity[farm.upgrades[1]]
                            self.logs.append("The new farm is a bank! The bank's max capacity is %s"%(farm.max_account_value))
                            
                        #If the resulting farm is an IMF Loan or Monkeyopolis, determine the earliest time the loan can be used
                        if farm.upgrades[1] > 3 and path == 1:
                            farm.min_use_time = payout['Time'] + 20 #initial cooldown of 20 seconds
                        
                        #If the resulting farm is a Banana Central, activate the BRF buff, giving them 25% more payment amount
                        if farm.upgrades[0] == 5 and path == 0:
                            self.logs.append("The new farm is a Banana Central!")
                            self.T5_exists[0] = True
                            
                        #If the resutling farm is a Monkeyopolis, mark the x5x_exists flag as true to prevent the user from trying to have multiple of them
                        if farm.upgrades[1] == 5:
                            self.T5_exists[1] = True
                        
                        #If the resulting farm is a MWS, mark the MWS_exists flag as true to prevent the user from trying to have multiple of them.
                        if farm.upgrades[2] == 5:
                            self.T5_exists[2] = True
                        
                    elif dict_obj['Type'] == 'Sell Farm':
                        ind = dict_obj['Index']
                        self.logs.append("Selling the farm at index %s"%(ind))
                        #If the farm being sold is a Banana Central, we must turn off the BRF buff
                        if farm.upgrades[0] == 5:
                            self.logs.append("The farm we're selling is a Banana Central! Removing the BRF buff.")
                            self.T5_exists[0] = False
                        self.farms.pop(ind)
                        
                    elif dict_obj['Type'] == 'Withdraw Bank':
                        self.logs.append("Withdrawing money from the bank at index %s"%(ind))
                        ind = dict_obj['Index']
                        farm = self.farms[ind]
                        farm.account_value = 0
                    elif dict_obj['Type'] == 'Activate IMF':
                        ind = dict_obj['Index']
                        farm = self.farms[ind]
                        self.logs.append("Taking out a loan from the IMF at index %s"%(ind))
                        farm.min_use_time = payout['Time'] + 90
                        
                    # BOAT FARM RELATED MATTERS
                    elif dict_obj['Type'] == 'Buy Boat Farm':
                        self.logs.append("Purchasing boat farm!")
                        boat_farm = {
                            'Purchase Time': self.current_time,
                            'Upgrade': 3
                        }
                        self.boat_farms[self.boat_key] = boat_farm
                        self.boat_key += 1
                    elif dict_obj['Type'] == 'Upgrade Boat Farm':
                        ind = dict_obj['Index']
                        
                        self.logs.append("Upgrading the boat farm at index %s"%(ind))
                        boat_farm = self.boat_farms[ind]
                        boat_farm['Upgrade'] += 1
                        
                        #Update the payout information of the boat farm
                        boat_farm['Payout'] = boat_payout_values[boat_farm['Upgrade'] - 3]
                        
                        #So that we can accurately track payments for the boat farm
                        boat['Purchase Time'] = payout['Time']
                        
                        #Update the sellback value of the boat farm
                        boat['Sell Value'] = boat_sell_values[boat_farm['Upgrade'] - 3]

                        #If the new boat farm is a Trade Empire, indicate as such
                        if boat_farm['Upgrade'] == 5:
                            self.logs.append("The new boat farm is a Trade Empire!")
                            self.Tempire_exists = True

                    elif dict_obj['Type'] == 'Sell Boat Farm':
                        ind = dict_obj['Index']
                        self.logs.append("Selling the boat farm at index %s"%(ind))
                        #If the farm being sold is a Trade Empire, indicate as such
                        if boat_farm['Upgrade'] == 5:
                            self.logs.append("The boat farm we're selling is a Trade Empire! Removing the Tempire buff.")
                            self.Tempire_exists = False
                        self.boat_farms.pop(ind)

                    # DRUID FARMS
                    elif dict_obj['Type'] == 'Buy Druid Farm':
                        self.druid_farms[self.druid_key] = payout['Time']
                        self.druid_key += 1
                        self.logs.append("Purchased a druid farm!")
                    elif dict_obj['Type'] == 'Sell Druid Farm':
                        ind = dict_obj['Index']
                        self.logs.append("Selling the druid farm at index %s"%(ind))
                        #If the druid we're selling is actually SOTF...
                        if self.sotf is not None and ind == self.sotf:
                            self.logs.append("The druid farm being sold is a Spirit of the Forest!")
                            self.sotf = None
                            self.sotf_min_use_time = None
                    elif dict_obj['Type'] == 'Buy Spirit of the Forest':
                        ind = dict_obj['Index']
                        self.sotf = ind
                        self.logs.append("Upgrading the druid farm at index %s into a Spirit of the Forest!"%(ind))
                        #Determine the minimum time that the SOTF active could be used
                        i = np.floor((20 + payout['Time'] - self.druid_farms[ind])/40) + 1
                        self.sotf_min_use_time = payout['Time'] + 20 + 40*(i-1)
                    elif dict_obj['Type'] == 'Use Spirit of the Forest':
                        self.logs.append("Using the Spirit of the Forest active (index %s)"%(self.sotf))
                        self.sotf_min_use_time = payout['Time'] + 40
                    elif dict_obj['Type'] == 'Repeatedly Buy Druid Farms':
                        self.druid_farm_max_buy_time = dict_obj['Maximum Buy Time']
                        self.druid_farm_buffer = dict_obj['Buffer']
                        self.logs.append("Triggered automated druid farm purchases until time %s"%(self.supply_drop_max_buy_time))

                    # SUPPLY DROP RELATED MATTERS
                    elif dict_obj['Type'] == 'Buy Supply Drop':
                        self.supply_drops[self.sniper_key] = payout['Time']
                        self.sniper_key += 1
                        self.logs.append("Purchased a supply drop!")
                    elif dict_obj['Type'] == 'Sell Supply Drop':
                        ind = dict_obj['Index']
                        self.logs.append("Selling the supply drop at index %s"%(ind))
                        #If the supply drop we're selling is actually an E-sniper, then...
                        if self.elite_sniper is not None:
                            if ind == self.elite_sniper:
                                self.logs.append("The supply drop being sold is an elite sniper!")
                                self.elite_sniper = None
                        
                        self.supply_drops.pop(ind)
                    elif dict_obj['Type'] == 'Buy Elite Sniper':
                        ind = dict_obj['Index']
                        self.elite_sniper = ind
                        self.logs.append("Upgrading the supply drop at index %s into an elite sniper!"%(ind))
                    elif dict_obj['Type'] == 'Repeatedly Buy Supply Drops':
                        self.supply_drop_max_buy_time = dict_obj['Maximum Buy Time']
                        self.supply_drop_buffer = dict_obj['Buffer']
                        self.logs.append("Triggered automated supply drop purchases until time %s"%(self.supply_drop_max_buy_time))
                        
                #Now, we have finished the for loop through purchase_info and thus correctly performed the buys
                #Remove the buy from the queue and set self.buy_cost to None so the code knows next time to re-compute
                #the buy cost for the next item in the buy queue
                self.min_buy_time = None
                self.buffer = 0
                self.buy_queue.pop(0)
                self.logs.append("Completed the buy operation! The buy queue now has %s items remaining in it"%(len(self.buy_queue)))
            else:
                #If we can't afford the buy, break the while loop
                #self.logs.append("We can't afford the buy! Terminating the buy queue while loop")
                break
        
        #...so that players can see where in the graphs their purchases are occuring
        if len(buy_message_list) > 0:
            buy_message = ', '.join(buy_message_list)
            self.buy_messages.append((payout['Time'], buy_message, 'Buy'))
        
        return made_purchase
            
# %% [markdown]
# Now it's time to define the MonkeyFarm class!

# %%
class MonkeyFarm():
    def __init__(self, initial_state):
        
        ###############
        #BASIC FEATURES
        ###############
        
        #self.upgrades is an array [i,j,k] representing the upgrade state of the farm
        #EXAMPLE: [4,2,0] represents a Banana Research Facility with Valuable Bananas
        
        self.upgrades = initial_state.get('Upgrades')
        self.sell_value = farm_sell_values[tuple(self.upgrades)]
        
        self.purchase_time = initial_state.get('Purchase Time')
        
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
            self.min_use_time = self.purchase_time + 20



# %% [markdown]
# The goal of a simulator like this is to compare different strategies and see which one is better. To this end, we define a function capable of simulating multiple game states at once and comparing them.

# %%
def compareStrategies(initial_state, eco_queues, buy_queues, target_time = None, target_round = 30, display_farms = True):
    
    # Log file in case we need to check outputs
    logs = []
    
    # Given an common initial state and N different tuples of (eco_queue, buy_queue), 
    # Build N different instances of GameState, advance them to the target_time (or target round if specified)
    # Finally, graph their cash and eco histories
    
    # To begin, let's form the GameState objects we will use in our analysis!
    game_states = []
    farm_incomes = []
    N = len(eco_queues)
    for i in range(N):
        init = initial_state
        init['Eco Queue'] = eco_queues[i]
        init['Buy Queue'] = buy_queues[i]
        #print(init['Supply Drops'])
        game_states.append(GameState(init))
    
    #########################
    # GRAPH CASH & ECO STATES
    #########################
    
    #Now intialize the graphs, one for cash and one for eco
    fig, ax = plt.subplots(2)
    fig.set_size_inches(8,12)
    
    #For each GameState object, advance the time, and then graph the cash and eco history
    i = 0
    cash_min = None
    if target_round is not None:
        #Use the target round instead of the target time if specified
        target_time = game_states[0].rounds.getTimeFromRound(target_round)

    for game_state in game_states:
        logs.append("Simulating Game State %s"%(i))
        game_state.fastForward(target_time = target_time)
        
        ax[0].plot(game_state.time_states, game_state.cash_states, label = "Cash of Game State %s"%(i))
        ax[1].plot(game_state.time_states, game_state.eco_states, label = "Eco of Game State %s"%(i))
        
        farm_income = 0
        for key in game_state.farms.keys():
            #WARNING: This is not a great measure to go by if the player has farms
            farm = game_state.farms[key]
            if game_state.T5_exists[0] == True and farm.upgrades[0] == 4:
                #If the farm is a BRF being buffed by Banana Central
                farm_income += 1.25*farm.payout_amount*farm.payout_frequency
            elif farm.upgrades[2] == 5:
                #If the farm is a Monkey Wall Street
                farm_income += 10000 + farm.payout_amount*farm.payout_frequency
            elif farm.upgrades[1] >= 3:
                #This is an *estimate* based on the impact of one round of bank payments
                farm_income = farm_income + 1.2*(farm.payout_amount*farm.payout_frequency + 400)
            else:
                farm_income += farm.payout_amount*farm.payout_frequency
        farm_incomes.append(farm_income)
            
        
        if cash_min is None:
            cash_min = min(game_state.cash_states)
            eco_min = min(game_state.eco_states)
            
            cash_max = max(game_state.cash_states)
            eco_max = max(game_state.eco_states)
            
        else:
            candidate_cash_min = min(game_state.cash_states)
            candidate_eco_min = min(game_state.eco_states)
            
            if candidate_cash_min < cash_min:
                cash_min = candidate_cash_min
            if candidate_eco_min < eco_min:
                eco_min = candidate_eco_min
            
            candidate_cash_max = max(game_state.cash_states)
            candidate_eco_max = max(game_state.eco_states)
            
            if candidate_cash_max > cash_max:
                cash_max = candidate_cash_max
            if candidate_eco_max > eco_max:
                eco_max = candidate_eco_max
        
        i += 1

    ####################
    # GRAPH ROUND STARTS
    ####################
    
    # Also, graph when the rounds start
    # DEVELOPER'S NOTE: We are dealing with multiple game states where the stall factor in each game state may change
    # For now, I will just take the round starts from game state 0, but I'll have to adjust this later on down the road.
    
    round_to_graph = initial_state['Rounds'].getRoundFromTime(game_states[0].time_states[0]) + 1
    while initial_state['Rounds'].round_starts[round_to_graph] <= game_states[0].time_states[-1]:
        logs.append("Graphing round %s, which starts at time %s"%(str(round_to_graph),str(initial_state['Rounds'].round_starts[round_to_graph])))
        ax[0].plot([initial_state['Rounds'].round_starts[round_to_graph], initial_state['Rounds'].round_starts[round_to_graph]],[cash_min, cash_max], label = "R" + str(round_to_graph) + " start")
        ax[1].plot([initial_state['Rounds'].round_starts[round_to_graph], initial_state['Rounds'].round_starts[round_to_graph]],[eco_min, eco_max], label = "R" + str(round_to_graph) + " start")
        round_to_graph += 1

    #################
    # DISPLAY VISUALS
    #################
    
    ax[0].set_title("Cash vs Time")
    ax[1].set_title("Eco vs Time")

    ax[0].set_ylabel("Cash")
    ax[1].set_ylabel("Eco")

    ax[1].set_xlabel("Time (seconds)")

    ax[0].legend(loc='upper left')
    ax[1].legend(loc='upper left')
    
    d = {'Game State': [i for i in range(N)], 'Farm Income': [farm_incomes[i] for i in range(N)]}
    df = pd.DataFrame(data=d)
    
    fig.tight_layout()
    display(df)
    logs.append("Successfully generated graph! \n")


