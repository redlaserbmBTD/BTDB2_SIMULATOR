# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from b2sim.info import *
from b2sim.actions import *
import copy

# %%


# %%
def impact(cash, loan, amount):
    #If the amount is positive (like a payment), half of the payment should be directed to the outstanding loan
    #If the amount is negative (like a purchase), then we can treat it "normally"
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
        
        #Initial cash and eco and loan values
        self.cash = initial_state.get('Cash')
        self.eco = initial_state.get('Eco')
        self.loan = initial_state.get('Loan') #For IMF Loans
        
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

        self.logs = [] #To ensure the code runs properly, we'll create a log file which the code writes to track what it's doing
        self.warnings = [] #These are indices corresponding to log messages where fail-safes or other unexpecated events are triggered.

        #As the Game State evolves, I'll use these arrays to track how cash and eco have changed over time
        self.time_states = [self.current_time]
        self.cash_states = [self.cash] 
        self.eco_states = [self.eco]

        #I'll use this list to track the amount of money each farm makes over the course of the simulation
        self.farm_revenues = []
        self.farm_expenses = []

        #These lists will hold tuples (time, message)
        #These tuples are utilized by the viewCashAndEcoHistory method to display detailed into to the player about what actions were taken at what during simulation
        self.event_messages = []
        
        #~~~~~~~~~~~~~~~
        #FARMS & ALT-ECO
        #~~~~~~~~~~~~~~~
        
        #Process the initial info given about farms/alt-eco:
        
        #Info for whether T5 Farms are up or not
        self.T5_exists = [False, False, False]
        
        #First, farms!

        # We assume in the initial state dictionary that there is an entry "Farms" consisting of a list of dictionaries.
        # Note that the structure of self.farms however is not a list, but a dictionary with keys being nonnegative integers
        # The rationale for doing this is to drastically simplify code related to performing compound transactions.

        self.farms = []
        farm_info = initial_state.get('Farms')
        if farm_info is not None:
            for farm_info_entry in farm_info:
                self.farms.append(MonkeyFarm(farm_info_entry))
                
                #If the farm is a T5 farm, modify our T5 flags appropriately
                #Do not allow the user to initialize with multiple T5's
                for i in range(3):
                    if self.farms[-1].upgrades[i] == 5 and self.T5_exists[i] == False:
                        self.T5_exists[i] = True
                    elif self.farms[-1].upgrades[i] == 5 and self.T5_exists[i] == True:
                        self.logs.append("Warning! The initial state contained multiple T5 farms. Modifying the initial state to prevent this.")
                        self.warnings.append(len(self.logs)-1)
                        self.farms[-1].upgrades[i] = 4

        #Next, boat farms!
        boat_info = initial_state.get('Boat Farms')
        self.Tempire_exists = False
        self.boat_farms = {}
        self.boat_key = 0
        if boat_info is not None:
            for boat_entry in boat_info:
                #If the boat farm is a Tempire, mark it as such appropriately.
                #Do not allow the user to initialize with multiple Tempires!
                if boat_entry['Upgrade'] == 5 and self.Tempire_exists[i] == False:
                    self.Tempire_exists = True
                elif boat_entry['Upgrade'] == 5 and self.Tempire_exists[i] == True:
                    boat_entry['Upgrade'] = 4
                self.boat_farms[self.boat_key] = boat_entry

                self.boat_key += 1
                

        #Next, druid farms!
        self.druid_farms = initial_state.get('Druid Farms')
        if self.druid_farms is not None:
            self.sotf = self.druid_farms['Spirit of the Forest Index']
            self.druid_key = len(self.druid_farms) - 2
        else:
            self.sotf = None
            self.druid_key = 0

        #Next, supply drops!
        self.supply_drops = initial_state.get('Supply Drops')
        if self.supply_drops is not None:
            self.elite_sniper = self.supply_drops['Elite Sniper Index']
            self.sniper_key = len(self.supply_drops) - 2
        else:
            self.elite_sniper = None
            self.sniper_key = 0

        #Next, heli farms!
        self.heli_farms = initial_state.get('Heli Farms')
        if self.heli_farms is not None:
            self.special_poperations = self.heli_farms['Special Poperations Index']
            self.heli_key = len(self.heli_farms) - 2
        else:
            self.special_poperations = None
            self.heli_key = 0

        #~~~~~~~~~~~~
        #HERO SUPPORT
        #~~~~~~~~~~~~

        self.jericho_steal_time = float('inf') #Represents the time when Jericho's steal is to be activated.
        self.jericho_steal_amount = 25 #Represents the amount of money Jericho steals

        #~~~~~~~~~~~~~~~~
        #THE QUEUE SYSTEM
        #~~~~~~~~~~~~~~~~
        
        #Eco queue info
        
        # Items in the eco_queue look like (time, properties), where properties is a dictionary like so:
        # {
        #     'Send Name': send_name,
        #     'Max Send Amount': max_send_amount,
        #     'Fortified': fortified,
        #     'Camoflauge': camo,
        #     'Regrow': regrow,
        #     'Max Eco Amount': max_eco_amount
        # }

        # Max send amount is useful if we need to simulate sending a precise number of sets of bloons
        # Max eco amount is useful for eco strategies which may demand strategy decisions like "stop eco at 3000 eco"

        self.eco_queue = initial_state.get('Eco Queue')
        if self.eco_queue is None:
            self.eco_queue = [ecoSend(time = 0, send_name = 'Zero')]
        self.number_of_sends = 0

        eco_send = initial_state.get('Eco Send')
        if eco_send is not None:
            eco_send['Time'] = 0
            self.eco_queue.insert(0,eco_send)
        
        #Upgrade queue
        self.buy_queue = initial_state.get('Buy Queue')
        self.buy_cost = None
        self.buffer = 0
        self.min_buy_time = None

        #Attack queue - This is the list of bloons in the center of the screen that pops up whenever you send eco
        self.attack_queue = []
        self.attack_queue_unlock_time = self.current_time
        self.eco_delay = game_globals['Eco Delay']
        self.max_queue_length = game_globals['Max Queue Length']
        self.attack_queue_threshold = game_globals['Max Queue Length']

        #For repeated supply drop buys
        self.supply_drop_max_buy_time = -1
        self.supply_drop_buffer = 0

        #For repeated druid farm buys
        self.druid_farm_max_buy_time = -1
        self.druid_farm_buffer = 0

        #For repeated heli farm buys
        self.heli_farm_max_buy_time = -1
        self.heli_farm_buffer = 0

        #~~~~~~~~~~
        #FAIL-SAFES
        #~~~~~~~~~~
        
        if self.farms is None:
            self.farms = []
        if self.buy_queue is None:
            self.buy_queue = []
        if self.loan is None:
            self.loan = 0
        if self.boat_farms is None:
            self.boat_farms = {}
        if self.druid_farms is None:
            self.druid_farms = {}
        if self.heli_farms is None:
            self.heli_farms = {}
        if self.supply_drops is None:
            self.supply_drops = {}
        self.simulation_start_time = 0
            
        self.logs.append("MESSAGE FROM GameState.__init__(): ")
        self.logs.append("Initialized Game State!")
        self.logs.append("The current game round is %s"%(self.current_round))
        self.logs.append("The current game time is %s seconds"%(self.current_time))
        self.logs.append("The game round start times are given by %s \n"%(self.rounds.round_starts))
        
    def viewCashEcoHistory(self, dim = (15,18), display_farms = True, font_size = 12):
        self.logs.append("MESSAGE FROM GameState.viewCashEcoHistory():")
        self.logs.append("Graphing history of cash and eco!")

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #Create a table that shows when each significant event in simulation occurs
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        event_df = pd.DataFrame(self.event_messages)
        event_df = event_df.round(1)
        display(event_df)

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #Graph the cash and eco values over time
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        #Graphing cash
        fig, ax1 = plt.subplots()
        fig.set_size_inches(dim[0],dim[1])

        color = 'tab:blue'
        ax1.set_xlabel('Time (seconds)')
        ax1.set_ylabel('Cash', color = color)
        ax1.plot(self.time_states, self.cash_states, label = "Cash", color = color)
        ax1.tick_params(axis ='y', labelcolor = color)

        #Graphing eco
        color = 'tab:orange'
        ax2 = ax1.twinx()
        ax2.set_ylabel('Eco', color = color)
        ax2.plot(self.time_states, self.eco_states, label = "Eco", color = color)
        ax2.tick_params(axis ='y', labelcolor = color)

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #Mark on the graph messages in self.event_messages
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        cash_min = min(self.cash_states)
        eco_min = min(self.eco_states)
        
        cash_max = max(self.cash_states)
        eco_max = max(self.eco_states)

        for message in self.event_messages:

            # Set different line properties for each message type
            if message['Type'] == 'Eco':
                line_style = ':'
                line_color = 'b'
            elif message['Type'] == 'Buy':
                line_style = ':'
                line_color = 'r'
            elif message['Type'] == 'Round':
                line_style = ':'
                line_color = 'k'

            # If the given message is too long, truncate it.
            if len(message['Message']) > 30:
                thing_to_say = message['Message'][0:22] + '...'
            else:
                thing_to_say = message['Message']

            #On both the cash and eco history graphs
            ax1.plot([message['Time'],message['Time']],[cash_min-1, cash_max+1], label = thing_to_say, linestyle = line_style, color = line_color)

        #~~~~~~~~~~~~~~~~
        #Label the graphs
        #~~~~~~~~~~~~~~~~

        ax1.set_title("Cash & Eco vs Time")
        ax1.legend(bbox_to_anchor = (1.1, 1), fontsize = font_size)
        fig.tight_layout()

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #Create a table that displays the revenue/expenses of each farm
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        #Create a list of revenues and expenses for every farm
        self.farm_revenues = []
        self.farm_expenses = []
        self.farm_profits = []
        self.farm_eis = []
        self.farm_starts = []
        self.farm_ends = []

        for farm in self.farms:
            self.farm_revenues.append(farm.revenue)
            self.farm_expenses.append(farm.expenses)
            self.farm_profits.append(farm.revenue - farm.expenses)

            #Also, measure the equivalent eco impact of the farm
            start_time = max(farm.init_purchase_time, self.simulation_start_time)
            if farm.sell_time == None:
                end_time = self.current_time
            else:
                end_time = farm.sell_time

            self.farm_starts.append(start_time)
            self.farm_ends.append(end_time)

            self.farm_eis.append(6*farm.revenue/(end_time - start_time))

        # dictionary of lists 
        if display_farms and len(self.farms) > 0:
            farm_table = {
                'Farm Index': [int(i) for i in range(len(self.farms))], 
                'Revenue': self.farm_revenues, 
                'Expenses': self.farm_expenses, 
                'Profit': self.farm_profits, 
                'Eco Impact': self.farm_eis, 
                'Start Time': self.farm_starts, 
                'End Time': self.farm_ends
            } 
            df = pd.DataFrame(farm_table)
            df = df.set_index('Farm Index')
            df = df.round(0)
            display(df)

        
        self.logs.append("Successfully generated graph! \n")
    
    def changeStallFactor(self,stall_factor):
        #NOTE: This method currently does not see use at all. It may be removed in a future update.
        self.rounds.changeStallFactor(stall_factor,self.current_time)

    def checkProperties(self):
        # Helper method for ecoQueueCorrection.

        #Do not apply modifiers to eco sends if the modifiers are not available
        if self.eco_queue[0]['Time'] < self.rounds.getTimeFromRound(game_globals['Fortified Round']):
            self.eco_queue[0]['Fortified'] = False
        if self.eco_queue[0]['Time'] < self.rounds.getTimeFromRound(game_globals['Camoflauge Round']):
            self.eco_queue[0]['Camoflauge'] = False
        if self.eco_queue[0]['Time'] < self.rounds.getTimeFromRound(game_globals['Regrow Round']):
            self.eco_queue[0]['Regrow'] = False
        
        #Do not apply modifiers to eco sends if they are ineligible to receive such modifiers
        if not eco_send_info[self.eco_queue[0]['Send Name']]['Fortified']:
            self.eco_queue[0]['Fortified'] = False
        if not eco_send_info[self.eco_queue[0]['Send Name']]['Camoflauge']:
            self.eco_queue[0]['Camoflauge'] = False
        if not eco_send_info[self.eco_queue[0]['Send Name']]['Regrow']:
            self.eco_queue[0]['Regrow'] = False

    def ecoQueueCorrection(self):
        # This method automatically adjusts the game state's given eco queue so that it contains valid sends.

        # Essentially, the code works like this:
        # Look at the first send in the queue and decide if the time currently indicated is too early or late, or if we have exceeded the maximum permissible amount of eco for this send (self.max_eco_amount).
        # # If it's too late (we are beyond the last round which we would use the send), remove the send from the queue
        # # If it's too early, adjust the time to earliest available time we can use the send
        # If the process above results in the first send in the queue being slated to be used after the second, *remove* the first send.
        # The process above repeats until either the queue is empty or the first send in the queue is valid.
        # Once it is determined that the first send in the queue is valid, check for and remove any properties from the eco which cannot be applied to said send.

        # When the process above is complete, we must check whether we should change to first send in the queue right now or not.
        # # If the answer is no, we can exit the process.
        # # If the answer is yes, switch to said send, and then (if there are still items in the eco queue) check whether the next item in the send is valid (This entails repeating the *entire* process above!)

        future_flag = False
        while len(self.eco_queue) > 0 and future_flag == False:
            break_flag = False
            while len(self.eco_queue) > 0 and break_flag == False:
                #print("length of queue: %s"%(len(self.eco_queue)))

                #Are we under the eco threshold to use the eco send?
                if self.eco_queue[0]['Max Eco Amount'] is not None and self.eco >= self.eco_queue[0]['Max Eco Amount']:
                    #No, do not use the eco send.
                    self.eco_queue.pop(0)
                else:
                    #Yes, we are under the threshold. Now check if the given time for the send is a valid time..
                    if self.eco_queue[0]['Time'] is None:
                        #Bypass the time check if no time is given.
                        break_flag = True
                    else:
                        #Is the eco send too late?
                        if self.eco_queue[0]['Time'] >= self.rounds.getTimeFromRound(eco_send_info[self.eco_queue[0]['Send Name']]['End Round']+1):
                            #Yes, the send is too late. Remove it from the queue.
                            self.logs.append("Warning! Time %s is too late to call %s. Removing from eco queue"%(self.eco_queue[0]['Time'],self.eco_queue[0]['Send Name']))
                            self.eco_queue.pop(0)
                            
                        else:
                            #No, the send is not too late
                            
                            #Is the eco send too early?
                            #self.logs.append("The candidate round is %s"%(eco_send_info[self.eco_queue[0]['Send Name']]['Start Round']))
                            candidate_time = self.rounds.getTimeFromRound(eco_send_info[self.eco_queue[0]['Send Name']]['Start Round'])
                            if self.eco_queue[0]['Time'] < candidate_time:
                                #Yes, the send is too early
                                self.logs.append("Warning! Time %s is too early to call %s. Adjusting the queue time to %s"%(self.eco_queue[0]['Time'],self.eco_queue[0]['Send Name'], candidate_time))
                                self.eco_queue[0]['Time'] = candidate_time
                                #Is the adjusted time still valid?
                                if len(self.eco_queue) < 2 or self.eco_queue[0]['Time'] < self.eco_queue[1]['Time']:
                                    #Yes, it's still valid
                                    self.checkProperties()
                                    break_flag = True
                                else:
                                    #No, it's not valid
                                    self.logs.append("Warning! Time %s is too late to call %s because the next item in the eco queue is slated to come earlier. Removing from eco queue"%(self.eco_queue[0]['Time'],self.eco_queue[0]['Send Name']))
                                    self.eco_queue.pop(0)
                            else:
                                #No, the send is not too early
                                self.checkProperties()
                                break_flag = True
            
            if len(self.eco_queue) > 0 and (self.eco_queue[0]['Time'] is not None and self.eco_queue[0]['Time'] <= self.current_time):
                self.changeEcoSend()
            else:
                future_flag = True
        
    def changeEcoSend(self):
        # Attempt to change to the first send available in the eco queue
        # This method is triggered either when reaching the specified time for the next send in the eco queue OR when a break condition (such as max_eco_amount) is satisfied for the current send
        # Note that if this method is called as a consequence of a break condition being satisfied, it is possible that the safeguard for switching to a send before it becomes available could be triggered.

        send_info = self.eco_queue[0]
        self.eco_queue.pop(0)

        # The send info dictionary looks like this:
        # {
        #     'Time': time,
        #     'Send Name': send_name,
        #     'Max Send Amount': max_send_amount,
        #     'Fortified': fortified,
        #     'Camoflauge': camo,
        #     'Regrow': regrow,
        #     'Max Eco Amount': max_eco_amount
        # }
        
        # Check if the given send name corresponds to a valid send. If not, default to the zero send.
        eco_send_keys = list(eco_send_info.keys())
        if eco_send_keys.count(send_info['Send Name']) == 0:
            self.logs.append("Warning! The name %s does not correspond with an eco send! Switching to the zero send."%(send_info['Send Name']))
            send_info['Send Name'] = 'Zero'
            self.warnings.append(len(self.logs) - 1)

        self.current_round = self.rounds.getRoundFromTime(self.current_time)

        # FAIL SAFE: Switch to the zero send instead if the send is not yet available, and reinsert the send we tried to switch to back into the eco queue.
        if self.current_round < eco_send_info[send_info['Send Name']]['Start Round']:
            self.logs.append("Warning! The eco send %s is not available yet! Switching to the zero send for now, we will attempt to use this send later."%(send_info['Send Name']))
            self.warnings.append(len(self.logs) - 1)
            send_info['Time'] = self.rounds.getTimeFromRound(eco_send_info[send_info['Send Name']]['Start Round'])
            self.logs.append("We are about to insert the following send into the eco queue: ")
            self.logs.append(str(send_info))
            self.eco_queue.insert(0,copy.deepcopy(send_info))
            send_info['Send Name'] = 'Zero'
            self.logs.append("The next item in the eco queue now looks like this: ")
            self.logs.append(str(self.eco_queue[0]))
        
        # FAIL SAFE: Switch to the zero send if the send is no longer available.
        # The only scenario this should trigger is if the initially specified eco send is no good.
        if self.current_round > eco_send_info[send_info['Send Name']]['End Round']:
            self.logs.append("Warning! The eco send %s is no longer available! Switching to the zero send."%(send_info['Send Name']))
            self.logs.append("Warning! The above message occurred during the changeEcoSend method, which means something's probably wrong with the code!")
            self.warnings.append(len(self.logs) - 1)
            self.warnings.append(len(self.logs) - 2)
            send_info['Send Name'] = 'Zero'


        # First, check if the send has any fortied, camo, or regrow characteristics
        eco_cost_multiplier = 1
        if send_info['Fortified'] == True:
            eco_cost_multiplier *= game_globals['Fortified Multiplier']
        if send_info['Camoflauge'] == True:
            eco_cost_multiplier *= game_globals['Camoflauge Multiplier']
        if send_info['Regrow'] == True:
            eco_cost_multiplier *= game_globals['Regrow Multiplier']

        self.send_name = send_info['Send Name']

        # If an eco send is a MOAB class send, fortifying it doubles the eco penalty

        eco_gain_multiplier = 1
        if eco_send_info[self.send_name]['MOAB Class'] and send_info['Fortified']:
            eco_gain_multiplier = 2

        self.eco_cost = eco_cost_multiplier*eco_send_info[self.send_name]['Price']
        self.eco_gain = eco_gain_multiplier*eco_send_info[self.send_name]['Eco']
        self.eco_time = eco_send_info[self.send_name]['Send Duration']

        #Setting the max_send_amount
        self.max_send_amount = send_info['Max Send Amount']
        self.number_of_sends = 0

        #Setting the max_eco_amount
        self.max_eco_amount = send_info['Max Eco Amount']

        #Setting the max_send_time
        self.max_send_time = send_info['Max Send Time']

        #Setting the queue threshold
        self.attack_queue_threshold = send_info['Queue Threshold']

        self.logs.append("Modified the eco send to %s"%(self.send_name))
        self.event_messages.append({
            'Time': self.current_time, 
            'Type': "Eco",
            'Message': "Change eco to %s"%(self.send_name)
        })

    def showWarnings(self,warnings):
        for index in warnings:
            print(self.logs[index])
        
    def fastForward(self, target_time = None, target_round = None, interval = 0.1):
        self.logs.append("MESSAGE FROM GameState.fastForward: ")
        self.valid_action_flag = True #To prevent the code from repeatedly trying to perform a transaction that obviously can't happen
        self.simulation_start_time = self.current_time
        
        # If a target round is given, compute the target_time from that
        if target_round is not None:
            target_time = self.rounds.getTimeFromRound(target_round)

        # Append messages to the event messages list showing when each round starts
        given_round = self.current_round
        end_round = self.rounds.getRoundFromTime(target_time)
        while given_round <= end_round:
            self.event_messages.append({
                'Time': self.rounds.getTimeFromRound(given_round),
                'Type': "Round",
                'Message': "Round %s start"%(given_round)
            })
            given_round += 1
            
        #A fail-safe to prevent the code from trying to go backwards in time
        if target_time < self.current_time:
            target_time = self.current_time
        
        while self.current_time < target_time:
            intermediate_time = min(max(np.floor(self.current_time/interval + 1)*interval,self.current_time + interval/2),target_time)
            self.logs.append("Advancing game to time %s"%(np.round(intermediate_time,3)))
            self.advanceGameState(target_time = intermediate_time)
            self.logs.append("----------")

        # Sort the messages in self.event_messages so that they are listed chronologically
        self.event_messages = sorted(self.event_messages, key=lambda x: x['Time']) 

        #FOR SPOONOIL: Show warning messages for fail-safes triggered during simulation
        self.showWarnings(self.warnings)
        
        self.logs.append("Advanced game state to round " + str(self.current_round))
        self.logs.append("The current time is " + str(self.current_time))
        self.logs.append("The next round starts at time " + str(self.rounds.round_starts[self.current_round+1]))
        self.logs.append("Our new cash and eco is given by (%s,%s) \n"%(np.round(self.cash,2),np.round(self.eco,2)))

    def advanceGameState(self, target_time = None, target_round = None):
        # self.logs.append("MESSAGE FROM GameState.advanceGameState: ")
        # Advance the game to the time target_time, 
        # computing the new money and eco amounts at target_time

        # NOTE: This function only works so long as nothing about the player's income sources changes.
        # Thus, if the player makes a purchase or changes eco sends, we will terminate prematurely.

        ###################
        #PART 0: FAIL-SAFES
        ###################

        # If the eco queue has the player try to use eco sends when they unavailable, automatically modify the queue so this doesn't happen
        self.ecoQueueCorrection()
        
        # FAIL-SAFE: Terminate advanceGameState early if an eco change is scheduled before the target_time.
        if len(self.eco_queue) > 0 and self.eco_queue[0]['Time'] is not None and self.eco_queue[0]['Time'] < target_time:
            #Yes, an eco change will occur
            target_time = self.eco_queue[0]['Time']

        # FAIL-SAFE: Check whether the current eco send is valid. If it is not, change the eco send to zero.
        if eco_send_info[self.send_name]['End Round'] < self.current_round:
            self.logs.append("Warning! The eco send %s is no longer available! Switching to the zero send."%(self.send_name))
            self.warnings.append(len(self.logs) - 1)
            self.eco_queue.insert(0,ecoSend(time = 0, send_name='Zero'))
            target_time = self.eco_queue[0]['Time']

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
        
        # Now that payouts have been computed and sorted, award them in the order they are meant to be awarded in.
        # The general flow of the code in this part is this:
            # Compute the impact of eco between payments
            # Award payment
            # Try to make purchases immediately after receiving the payment.
        
        made_purchase = False
        for i in range(len(payout_times)):
            payout = payout_times[i]
            
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            #First, compute the impact of eco from the previous payout (or starting time) to the current one
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

            self.updateEco(payout['Time'])

            if (self.max_send_amount is not None and self.number_of_sends >= self.max_send_amount) or (self.max_eco_amount is not None and self.eco >= self.max_eco_amount) or (self.max_send_time is not None and self.current_time > self.max_send_time):
                self.logs.append("Reached the limit on eco'ing for this send! Moving to the next send in the queue.")

                #Switch to the zero send
                if len(self.eco_queue) == 0:
                    self.logs.append("No more sends in the eco queue! Switching to the zero send.")
                    self.eco_queue.append(ecoSend(send_name = 'Zero'))
                else:
                    # Adjust the time of the next eco send so that the simulator attempts to change to it at simulation end
                    self.eco_queue[0]['Time'] = self.current_time
                
                # In rare cases, we may break from the eco queue on exactly same time that we are slated to receive a payment
                # In that rare case, we need to award the payment for that time and check the buy queue to ensure that we do not "skip" over anything essential.
                if self.current_time < payout['Time']:
                    break
                else:
                    made_purchase = True

            
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
            #Next, award the payout at the given time
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            
            # WARNING! If an IMF Loan is active, half of the payment must go towards the loan.
            
            if payout['Payout Type'] == 'Direct':
                #This case is easy! Just award the payment and move on
                if payout['Source'] != 'Ghost': # To avoid having the "ghost payment" included in the logs
                    new_cash, new_loan = impact(self.cash,self.loan, payout['Payout'])

                    if payout['Source'] == 'Farm':
                        #Track the money generated by the farm
                        key = payout['Index']
                        farm = self.farms[key]
                        farm.revenue += new_cash - self.cash

                    self.cash, self.loan = new_cash, new_loan
                    self.logs.append("Awarded direct payment %s at time %s"%(np.round(payout['Payout'],2),np.round(payout['Time'],2)))
                
                
            elif payout['Payout Type'] == 'Bank Payment':
                #Identify the bank that we're paying and deposit money into that bank's account
                #NOTE: Bank deposits are not impacted by IMF Loans. It is only when we withdraw the money that the loan is repaid
                key = payout['Index']
                farm = self.farms[key]
                farm.account_value += payout['Payout']
                self.logs.append("Awarded bank payment %s at time %s to farm at index %s"%(np.round(payout['Payout'],2),np.round(payout['Time'],2), key))
                if farm.account_value >= farm.max_account_value:
                    #At this point, the player should withdraw from the bank.
                    farm.account_value = 0
                    new_cash, new_loan = impact(self.cash,self.loan,farm.max_account_value)
                    farm.revenue += new_cash - self.cash #Track the money generated by the farm
                    self.cash, self.loan = new_cash, new_loan
                    self.logs.append("The bank at index %s reached max capacity! Withdrawing money"%(key))
                self.logs.append("The bank's new account value is %s"%(farm.account_value))
            elif payout['Payout Type'] == 'Bank Interest':
                #Identify the bank that we're paying and deposit $400, then give 20% interest
                key = payout['Index']
                farm = self.farms[key]
                farm.account_value += 400
                farm.account_value *= 1.2
                self.logs.append("Awarded bank interest at time %s to the farm at index %s"%(np.round(payout['Time'],2), key))
                if farm.account_value >= farm.max_account_value:
                    farm.account_value = 0
                    new_cash, new_loan = impact(self.cash,self.loan,farm.max_account_value)
                    farm.revenue += new_cash - self.cash #Track the money generated by the farm
                    self.cash, self.loan = new_cash, new_loan
                    self.logs.append("The bank at index %s reached max capacity! Withdrawing money"%(key))
                self.logs.append("The bank's new account value is %s"%(farm.account_value))
            elif payout['Payout Type'] == 'Eco':
                self.cash, self.loan = impact(self.cash,self.loan, self.eco)
                self.logs.append("Awarded eco payment %s at time %s"%(np.round(self.eco,2),np.round(payout['Time'],2)))
            
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            #Now, check whether we can perform the next buy in the buy queue
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            
            # The simulation should attempt to process the buy queue after every payout, *except* if multiple payouts occur at the same time
            # If multiple payouts occur at the same time, only access the buy queue after the *last* of those payments occurs.

            try_to_buy = False

            if i == len(payout_times)-1:
                try_to_buy = True
            elif payout_times[i]['Time'] < payout_times[i+1]['Time']:
                try_to_buy = True
            
            if try_to_buy:
                if self.processBuyQueue(payout):
                    made_purchase = True
            
            #~~~~~~~~~~~~~~~~~~~~
            # Automated Purchases
            #~~~~~~~~~~~~~~~~~~~~

            # There are actions in actions.py which let the player trigger the action of repeatedly buying supply drops or druid farms.
            # These while loops process *those* transactions independently of the buy queue.
            # WARNING: Unusual results will occur if you attempt to implement automated purchases of multiple alt eco's at the same time.
            # WARNING: Because automated purchases are processed after checking the buy queue, unexpected results may occur if items in the buy queue do not have a min_buy_time designated.

            if payout['Time'] <= self.supply_drop_max_buy_time and try_to_buy == True:
                while self.cash >= sniper_globals['Supply Drop Cost'] + self.supply_drop_buffer:
                    made_purchase = True
                    self.cash -= sniper_globals['Supply Drop Cost']
                    self.supply_drops[self.sniper_key] = payout['Time']
                    self.sniper_key += 1
                    self.logs.append("Purchased a supply drop! (Automated purchase)")

            if payout['Time'] <= self.druid_farm_max_buy_time and try_to_buy == True:
                while self.cash >= druid_globals['Druid Farm Cost'] + self.druid_farm_buffer:
                    made_purchase = True
                    self.cash -= druid_globals['Druid Farm Cost']
                    self.druid_farms[self.druid_key] = payout['Time']
                    self.druid_key += 1
                    self.logs.append("Purchased a druid farm! (Automated purchase)")

            if payout['Time'] <= self.heli_farm_max_buy_time and try_to_buy == True:
                while self.cash >= heli_globals['Heli Farm Cost'] + self.heli_farm_buffer:
                    made_purchase = True
                    self.cash -= heli_globals['Heli Farm Cost']
                    self.heli_farms[self.heli_key] = payout['Time']
                    self.heli_key += 1
                    self.logs.append("Purchased a heli farm! (Automated purchase)")
            
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            #Record the cash & eco history and advance the game time
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            
            #print("New cash and eco is (%s,%s)"%(np.round(self.cash,2), np.round(self.eco,2)))
            self.time_states.append(payout['Time'])
            self.cash_states.append(self.cash)
            self.eco_states.append(self.eco)
            self.logs.append("Recorded cash and eco values (%s,%s) at time %s"%(np.round(self.cash,2),np.round(self.eco,2),np.round(payout['Time'],2)))
            
            # NOTE: The last payment is a "ghost" payment to be awarded at the target time.
            self.current_time = payout['Time']

            #If a purchase occured in the buy queue, exit the processing of payments early
            if made_purchase == True:
                target_time = self.current_time
                break

            #end of for loop
        
        # After going through the for loop, we have accounted for all payments that could occur in the time period of interest
        # and also performed any purchases in our buy queue along the way. 
            
        ####################################
        #PART 3: UPDATE GAME TIME PARAMETERS
        ####################################
        
        # DEVELOPER'S NOTE: The list of payments always includes a "ghost" payment of 0 dollars at the designated target time. That payment helps to simplify this code. 
        self.current_time = target_time

        while self.rounds.round_starts[self.current_round] <= self.current_time:
            self.current_round += 1
        self.current_round -= 1
        
        #Update the eco send, if necessary
        if len(self.eco_queue) > 0 and self.eco_queue[0]['Time'] and target_time >= self.eco_queue[0]['Time']:
            self.changeEcoSend()
        
        #self.logs.append("Advanced game state to round " + str(self.current_round))
        #self.logs.append("The current time is " + str(self.current_time))
        #self.logs.append("The next round starts at time " + str(self.rounds.round_starts[self.current_round+1]))
        #self.logs.append("Our new cash and eco is given by (%s,%s) \n"%(np.round(self.cash,2),np.round(self.eco,2)))
           
    def computePayoutSchedule(self, target_time):
        # Helper method for advanceGameState
        # Given a target time target_time, return an order list of all payouts to occur from the game state's current time until the designated target time.
        # Each entry in the returned array is a dictionary detailing the time the payment is to occur and either the payment to give or instructions to compute that payment (necessary for eco for banks)

        payout_times = []
        
        #ECO PAYOUTS
        eco_time = 6*(np.floor(self.current_time/6)+1)
        while eco_time <= target_time:
            payout_entry = {
                'Time': eco_time,
                'Payout Type': 'Eco'
            }
            payout_times.append(payout_entry)
            eco_time += 6

        #DRUID FARMS
        if self.druid_farms is not None:
            for key in self.druid_farms.keys():
                druid_farm = self.druid_farms[key]

                #Determine the earliest druid farm activation that could occur within the interval of interest (self.current_time,target_time]
                use_index = max(1,np.floor(1 + (self.current_time - druid_farm - druid_globals['Druid Farm Initial Cooldown'])/druid_globals['Druid Farm Usage Cooldown'])+1)
                druid_farm_time = druid_farm + druid_globals['Druid Farm Initial Cooldown'] + druid_globals['Druid Farm Usage Cooldown']*(use_index-1)
                while druid_farm_time <= target_time:
                    payout_entry = {
                        'Time': druid_farm_time,
                        'Payout Type': 'Direct',
                        'Payout': druid_globals['Druid Farm Payout'],
                        'Source': 'Druid'
                    }
                    payout_times.append(payout_entry)
                    druid_farm_time += druid_globals['Druid Farm Usage Cooldown']

                if key == self.sotf:
                    #Spirit of the Forest has a start of round payment of 3000 dollars in addition to the payouts that x4x druids can give out 
                    #At the start of each round, append a payout entry with the SOTF payout
                    self.inc = 1
                    while self.rounds.getTimeFromRound(self.current_round + self.inc) <= target_time:
                        payout_entry = {
                            'Time': self.rounds.getTimeFromRound(self.current_round + self.inc),
                            'Payout Type': 'Direct',
                            'Payout': druid_globals['Spirit of the Forest Bonus'],
                            'Source': 'Druid'
                        }
                        payout_times.append(payout_entry)
                        self.inc += 1


        #SUPPLY DROPS
        if self.supply_drops is not None:
            for key in self.supply_drops.keys():
                supply_drop = self.supply_drops[key]
                if key == self.elite_sniper:
                    payout_amount = sniper_globals['Elite Sniper Payout']
                else:
                    payout_amount = sniper_globals['Supply Drop Payout']

                #Determine the earliest supply drop activation that could occur within the interval of interest (self.current_time,target_time]
                drop_index = max(1,np.floor(1 + (self.current_time - supply_drop - sniper_globals['Supply Drop Initial Cooldown'])/sniper_globals['Supply Drop Usage Cooldown'])+1)
                supply_drop_time = supply_drop + sniper_globals['Supply Drop Initial Cooldown'] + sniper_globals['Supply Drop Usage Cooldown']*(drop_index-1)
                while supply_drop_time <= target_time:
                    
                    payout_entry = {
                        'Time': supply_drop_time,
                        'Payout Type': 'Direct',
                        'Payout': payout_amount,
                        'Source': 'Sniper'
                    }
                    payout_times.append(payout_entry)
                    supply_drop_time += sniper_globals['Supply Drop Usage Cooldown']

        #HELI FARMS
        if self.heli_farms is not None:
            for key in self.heli_farms.keys():
                heli_farm = self.heli_farms[key]
                if key == self.special_poperations:
                    payout_amount = heli_globals['Special Poperations Payout']
                else:
                    payout_amount = heli_globals['Heli Farm Payout']

                #Determine the earliest heli farm usage that could occur within the interval of interest (self.current_time,target_time]
                drop_index = max(1,np.floor(1 + (self.current_time - heli_farm - heli_globals['Heli Farm Initial Cooldown'])/heli_globals['Heli Farm Usage Cooldown'])+1)
                heli_farm_time = heli_farm + heli_globals['Heli Farm Initial Cooldown'] + heli_globals['Heli Farm Usage Cooldown']*(drop_index-1)
                while heli_farm_time <= target_time:
                    
                    payout_entry = {
                        'Time': heli_farm_time,
                        'Payout Type': 'Direct',
                        'Payout': payout_amount,
                        'Source': 'Heli'
                    }
                    payout_times.append(payout_entry)
                    heli_farm_time += heli_globals['Heli Farm Usage Cooldown']

        #FARMS
        if len(self.farms) > 0:
            for key, farm in enumerate(self.farms):
                if farm.sell_time is None:
                    #If the farm is a monkeynomics, determine the payout times of the active ability
                    if farm.upgrades[1] == 5:
                        farm_time = farm.min_use_time
                        while farm_time <= target_time:
                            if farm_time > self.current_time:
                                payout_entry = {
                                    'Time': farm_time,
                                    'Payout Type': 'Direct',
                                    'Payout': farm_globals['Monkeynomics Payout'],
                                    'Source': 'Farm',
                                    'Index': key
                                }
                                payout_times.append(payout_entry)
                            farm_time += farm_globals['Monkeynomics Usage Cooldown']
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
                                
                                #WARNING: If the farm we are dealing with is a bank, we must direct the payment into the bank rather than the player.
                                #WARNING: If the farm we are dealing with is a MWS, we must check whether we are awarding the MWS bonus payment!
                                #WARNING: If the farm we are dealing with is a BRF, we must check whether the BRF buff is being applied or not!
                                
                                if farm.upgrades[1] >= 3:
                                    if i == 0 and self.current_round + self.inc > farm_purchase_round:
                                        #At the start of every round, every bank gets a $400 payment and then is awarded 20% interest.
                                        payout_entry = {
                                            'Time': farm_time,
                                            'Payout Type': 'Bank Interest',
                                            'Index': key,
                                            'Source': 'Farm'
                                        }
                                        payout_times.append(payout_entry)
                                    payout_entry = {
                                        'Time': farm_time,
                                        'Payout Type': 'Bank Payment',
                                        'Index': key,
                                        'Payout': farm.payout_amount,
                                        'Source': 'Farm'
                                    }
                                elif i == 0 and farm.upgrades[2] == 5 and self.current_round + self.inc > farm_purchase_round:
                                    payout_entry = {
                                        'Time': farm_time,
                                        'Payout Type': 'Direct',
                                        'Payout': farm.payout_amount + farm_globals['Monkey Wall Street Bonus'],
                                        'Source': 'Farm',
                                        'Index': key
                                    }
                                elif farm.upgrades[0] == 4 and self.T5_exists[0] == True:
                                    payout_entry = {
                                        'Time': farm_time,
                                        'Payout Type': 'Direct',
                                        'Payout': farm.payout_amount*farm_globals['Banana Central Multplier'],
                                        'Source': 'Farm',
                                        'Index': key
                                    }
                                else:
                                    payout_entry = {
                                        'Time': farm_time,
                                        'Payout Type': 'Direct',
                                        'Payout': farm.payout_amount,
                                        'Source': 'Farm',
                                        'Index': key
                                    }
                                payout_times.append(payout_entry)
                            elif farm_time > target_time:
                                #self.logs.append("The payout time of %s is too late! Excluding payout time!"%(farm_time))
                                self.flag = True
                                break
                        self.inc += 1
        
        #BOAT FARMS
        if len(self.boat_farms) > 0:

            #Is there a Trade Empire on screen right now? 
            if self.Tempire_exists == True:
                #Yes, determine the buff to be applied to other boat farm payments.
                active_boats = 0
                for key in self.boat_farms.keys():
                    boat_farm = self.boat_farms[key]
                    if boat_farm['Sell Time'] is None:
                        active_boats += 1
                arg = min(active_boats - 1,20)
            else:
                #No, there is not.
                arg = 0

            multiplier = 1 + 0.05*arg

            #Determine the amount of the money the boats will give each round
            boat_payout = 0
            for key in self.boat_farms.keys():
                boat_farm = self.boat_farms[key]
                if boat_farm['Sell Time'] is None:
                    boat_payout += multiplier*boat_payout_values[boat_farm['Upgrade'] - 3]

            #At the start of each round, append a payout entry with the boat payout
            self.inc = 1
            while self.rounds.getTimeFromRound(self.current_round + self.inc) <= target_time:
                payout_entry = {
                    'Time': self.rounds.getTimeFromRound(self.current_round + self.inc),
                    'Payout Type': 'Direct',
                    'Payout': boat_payout,
                    'Source': 'Boat',
                }
                payout_times.append(payout_entry)
                self.inc += 1

        #JERICHO PAYOUTS
        jeri_time = self.jericho_steal_time
        while jeri_time <= min(target_time, self.jericho_steal_time + (hero_globals['Jericho Number of Steals']-1)*hero_globals['Jericho Steal Interval']):
            if jeri_time > self.current_time:
                payout_entry = {
                    'Time': jeri_time,
                    'Payout Type': 'Direct',
                    'Payout': self.jericho_steal_amount,
                    'Source': 'Jericho',
                }
                payout_times.append(payout_entry)
            jeri_time += hero_globals['Jericho Steal Interval']

        #GHOST PAYOUT
        #This special payout prevents the code from waiting possibly several seconds to carry out purchases in the buy queue that can obviously be afforded
        payout_entry = {
            'Time': target_time,
            'Payout Type': 'Direct',
            'Payout': 0,
            'Source': 'Ghost',
        }
        payout_times.append(payout_entry)

        #Now that we determined all the payouts, sort the payout times by the order they occur in
        payout_times = sorted(payout_times, key=lambda x: x['Time']) 

        #self.logs.append("Sorted the payouts in order of increasing time!")

        return payout_times

    def updateEco(self, target_time):
        # Helper method which updates eco from the current game time to the specified target_time.
        # self.logs.append("Running updateEco!")

        # DEVELOPER'S NOTE: Because of a shortcoming in the code, if the player runs out of cash in the simulator while eco'ing, 
        # There is a very small delay between when the player earns enough cash to eco again and when they actually start eco'ing again.
        # This shortcoming is due to the fact that, if the player is to receive a payment on the same time that they try to send a set of bloons, the simulator will try to send the bloons first before awarding the payment.
        # There is a known fix for this issue, but I do not wish to implement out of fear that it may hamper code performance and make the code more difficult to read and understand.

        # self.logs.append("Attack Queue Unlock time: %s"%(self.attack_queue_unlock_time))
        # self.logs.append("Send Name: %s"%(self.send_name))
        # self.logs.append("Number of Sends: %s"%(self.number_of_sends))
        # self.logs.append("Max Send Amount: %s"%(self.max_send_amount))

        while self.attack_queue_unlock_time <= target_time and self.send_name != 'Zero' and (self.max_send_amount is None or self.number_of_sends < self.max_send_amount) and (self.max_eco_amount is None or self.eco < self.max_eco_amount) and (self.max_send_time is None or self.attack_queue_unlock_time <= self.max_send_time):
            self.current_time = max(self.attack_queue_unlock_time, self.current_time)
            # self.logs.append("Advanced current time to %s"%(self.current_time))

            # First, check if we can remove any items from the attack queue
            while len(self.attack_queue) > 0 and self.current_time >= self.attack_queue[0]:
                self.attack_queue.pop(0)
            
            # Next, try to add an attack to the attack_queue.
            # Can we send an attack?
            if self.cash >= self.eco_cost and len(self.attack_queue) < min(6, self.attack_queue_threshold):
                # Yes, the queue is empty and we have enough cash
                if len(self.attack_queue) == 0:
                    self.attack_queue.append(self.current_time + self.eco_time)
                else:
                    self.attack_queue.append(max(self.attack_queue[-1] + self.eco_time, self.current_time + self.eco_time))
                self.cash -= self.eco_cost
                self.eco += self.eco_gain
                self.logs.append("Sent a set of %s at time %s"%(self.send_name, self.current_time))
                self.logs.append("Currently, the send queue looks like this: ")
                self.logs.append(str(self.attack_queue))

                # Did the attack fill up the eco queue?
                if len(self.attack_queue) >= min(6, self.attack_queue_threshold):
                    # Yes, The next send will cause the attack queue to fill up. Wait until the queue empties (if necessary)
                    self.attack_queue_unlock_time = max(self.current_time + self.eco_delay, self.attack_queue[0])
                else:
                    # No, there's still space afterwards. Check again after the eco delay is up.
                    self.attack_queue_unlock_time = self.current_time + self.eco_delay
                
                self.number_of_sends += 1

            elif len(self.attack_queue) >= min(6, self.attack_queue_threshold):
                # No, the queue is full!
                # NOTE: This block of code won't get reached unless the game state is initalized with a full attack queue.
                self.attack_queue_unlock_time = self.attack_queue[0]
            
            elif self.cash < self.eco_cost:
                # No, we don't have money!
                self.attack_queue_unlock_time = target_time + self.eco_delay/2

    def processBuyQueue(self, payout):
        # Helper function for advanceGameState
        
        made_purchase = False
        buy_message_list = []
        
        # DEVELOPER'S NOTE: It is possible for the queue to be empty but for there to still be purchases to be performed (via automated purchases)
        while len(self.buy_queue) > 0 and self.valid_action_flag == True:
            
            # To begin, pull out the first item in the buy queue and determine the hypothetical cash and loan amounts 
            # if this transaction was performed, as well as the minimum buy time for the transaction.

            # Also determine the hypothetical changes in revenue if the transaction was to be performed
            # Developer's Note: We must determine the hypoethetical changes in revenue beforehand rather than only when transactions are performed because of the presence of loans in the simulation.
            
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
                    
                # self.logs.append("Determined the minimum buy time of the next purchase to be %s"%(self.min_buy_time))
                        
            # If we have not yet reached the minimum buy time, break the while loop. 
            # We will check this condition again later:
            if payout['Time'] < self.min_buy_time:
                break
            
            # Next, let's compute the cash and loan values we would have if the transaction was performed
            # We will compute the hypothetical revenues each farm would have if the transactions were carried out
            # In general the this step is necessary if there are in the presence of loans.
            # NOTE: Loans do not influence purchases, so we can process expense tracking for farms only when a transaction actually occurs.

            #For tracking the revenue of farms
            for farm in self.farms:
                farm.h_revenue = farm.revenue

            #For tracking the revenue of boat farms
            for key in self.boat_farms.keys():
                boat_farm = self.boat_farms[key]
                boat_farm['Hypothetical Revenue'] = boat_farm['Revenue']
            
            for dict_obj in purchase_info:

                h_cash, h_loan = self.processAction(dict_obj, payout, h_cash = h_cash, h_loan = h_loan, stage = 'check')

                #Immediately abort attempting the purchase if we try to process an action that is not possible:
                if not self.valid_action_flag:
                    break
                    
                #If at any point while performing these operations our cash becomes negative, then prevent the transaction from occurring:
                if h_cash < 0:
                    # self.logs.append("WARNING! Reached negative cash while attempting the transaction!")
                    break

                #Read the buffer associated with the buy if any
                #NOTE: Only one object in purchase_info should have buffer info
                #If there are multiple buffers, the code rectifies the matter by
                #adding them all together

                if dict_obj.get('Buffer') is not None:
                    self.buffer += dict_obj.get('Buffer')
            
            #Immediately break from processing the buy queue entirely if we try to process an action that is not possible.
            if not self.valid_action_flag:
                break
            
            # If the amount of cash we have exceeds our buffer, perform the transaction.
            # Note at this point we have already checked whether we have reached the minimum time for the buy and also
            # we have already checked whether the buy item is valid. We now just need to check whether we have enough money!
            
            #self.logs.append("We have %s cash, but the next buy costs %s and has a buffer of %s and needs to be made on or after time %s!"%(np.round(self.cash,2), np.round(self.cash - h_cash,2),np.round(self.buffer,2), self.min_buy_time))
            if h_cash >= self.buffer:
                #If we do, perform the buy!
                made_purchase = True
                self.logs.append("We have %s cash! We can do the next buy, which costs %s and has a buffer of %s and a minimum buy time of %s!"%(np.round(self.cash,2), np.round(self.cash - h_cash,2),np.round(self.buffer,2),np.round(self.min_buy_time,2)))

                # Make the adjustments to the cash and loan amounts
                self.cash = h_cash
                self.loan = h_loan

                # Track the revenue made by each farm
                for farm in self.farms:
                    farm.revenue = farm.h_revenue

                # Track the revenue made by each boat farm
                for key in self.boat_farms.keys():
                    boat_farm = self.boat_farms[key]
                    boat_farm['Revenue'] = boat_farm['Hypothetical Revenue']

                # self.logs.append("The new lists of farm revenues and expenses are given by: ")
                # self.logs.append(str(self.farm_revenues))
                # self.logs.append(str(self.farm_expenses))

                for dict_obj in purchase_info:

                    buy_message_list.append(dict_obj['Message'])
                    self.processAction(dict_obj, payout, stage = 'process')

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
            self.event_messages.append({
                'Time': payout['Time'], 
                'Type': "Buy", 
                'Message': buy_message
            })
        
        return made_purchase
    
    def processAction(self, dict_obj, payout, h_cash = None, h_loan = None, stage = 'check'):
        # Helper method for processBuyQueue
        # This is essentially just one giant if-elif block

        # processBuyQueue will use this method in two stages. 
        # The first stage is for checking if the next transaction in the buy queue can be performed.
        # The second stage is for actually carrying out the transaction

        # DEFENSE RELATED MATTERS
        if dict_obj['Type'] == 'Buy Defense':
            if stage == 'check':
                h_cash, h_loan = impact(h_cash, h_loan, -1*dict_obj['Cost'])
            # We don't need to do anything here in the processing stage
        # FARM RELATED MATTERS
        elif dict_obj['Type'] == 'Buy Farm':
            if stage == 'check':
                h_new_cash, h_new_loan = impact(h_cash, h_loan, -1*farm_globals['Farm Cost'])
            else:
                self.logs.append("Purchasing farm!")
                farm_info = {
                    'Purchase Time': self.current_time,
                    'Upgrades': [0,0,0]
                }
                farm = MonkeyFarm(farm_info)
                self.farms.append(farm)

                #For revenue and expense tracking
                farm.revenue = 0
                farm.expenses = farm_globals['Farm Cost']
        elif dict_obj['Type'] == 'Upgrade Farm':
            if stage == 'check':
                ind = dict_obj['Index']
                path = dict_obj['Path']
                farm = self.farms[ind]
                #Do not upgrade a farm that has already been sold!
                if farm.sell_time is not None:
                    self.logs.append("WARNING! Tried to upgrade a farm that was already sold! Aborting buy queue!")
                    self.warnings.append(len(self.logs)-1)
                    self.valid_action_flag = False

                #The following code prevents from the player from having multiple T5's in play
                if farm.upgrades[path]+1 == 5 and self.T5_exists[path] == True:
                    self.logs.append("WARNING! Tried to purchase a T5 farm when one of the same kind already existed! Aborting buy queue!")
                    self.warnings.append(len(self.logs)-1)
                    self.valid_action_flag = False
                h_cash, h_loan = impact(h_cash, h_loan, -1*farm_upgrades_costs[path][farm.upgrades[path]])
            else:
                ind = dict_obj['Index']
                path = dict_obj['Path']
                
                self.logs.append("Upgrading path %s of the farm at index %s"%(path, ind))
                farm = self.farms[ind]

                #For expense tracking
                farm.expenses += farm_upgrades_costs[path][farm.upgrades[path]]

                farm.upgrades[path] += 1

                #Update the payout information of the farm
                farm.payout_amount = farm_payout_values[tuple(farm.upgrades)][0]
                farm.payout_frequency = farm_payout_values[tuple(farm.upgrades)][1]
                
                #So that we can accurately track payments for the farm
                farm.purchase_time = payout['Time']
                
                #Update the sellback value of the farm
                farm.sell_value = farm_sellback_values[tuple(farm.upgrades)]
                
                self.logs.append("The new farm has upgrades (%s,%s,%s)"%(farm.upgrades[0],farm.upgrades[1],farm.upgrades[2]))
                
                #If the resulting farm is a Monkey Bank, indicate as such and set its max account value appropriately
                if farm.upgrades[1] >= 3 and path == 1:
                    farm.bank = True
                    farm.max_account_value = farm_bank_capacity[farm.upgrades[1]]
                    self.logs.append("The new farm is a bank! The bank's max capacity is %s"%(farm.max_account_value))
                    
                #If the resulting farm is an IMF Loan or Monkeyopolis, determine the earliest time the loan can be used
                if farm.upgrades[1] > 3 and path == 1:
                    farm.min_use_time = payout['Time'] + farm_globals['Monkeynomics Initial Cooldown']
                
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
            if stage == 'check':
                ind = dict_obj['Index']
                farm = self.farms[ind]
                withdraw = dict_obj['Withdraw']

                #Check whether the farm is actually on screen before selling it:
                h_new_cash, h_new_loan = h_cash, h_loan
                if farm.sell_time is None:
                    #If indicated, withdraw from the bank before selling it
                    if withdraw and farm.upgrades[1] >= 3:
                        h_new_cash, h_new_loan = impact(h_new_cash, h_new_loan, farm.account_value)
                    #Selling a farm counts as that farm generating revenue
                    h_new_cash, h_new_loan = impact(h_new_cash, h_new_loan, farm_sellback_values[tuple(farm.upgrades)])
                    farm.h_revenue += h_new_cash - h_cash
                    h_cash, h_loan = h_new_cash, h_new_loan
                else:
                    self.logs.append("WARNING! Tried to sell a farm that is not on screen! Aborting buy queue")
                    self.warnings.append(len(self.logs)-1)
                    self.valid_action_flag = False
            else:
                ind = dict_obj['Index']
                farm = self.farms[ind]
                self.logs.append("Selling the farm at index %s"%(ind))

                # If the farm being sold is a Banana Central, we must turn off the BRF buff
                # If the farm is a T5 of any sorts, ensure that the game state knows we no longer that particular T5

                if farm.upgrades[0] == 5:
                    self.logs.append("The farm we're selling is a Banana Central! Removing the BRF buff.")
                    self.T5_exists[0] = False
                elif farm.upgrades[1] == 5:
                    self.T5_exists[1] = False
                elif farm.upgrades[2] == 5:
                    self.T5_exists[2] = False

                #Mark the farm's sell time. The code checks whether this value is a number or not before trying to compute farm payments
                farm.sell_time = payout['Time']
        elif dict_obj['Type'] == 'Sell All Farms':
            if stage == 'check':
                for farm in self.farms:
                    if farm.sell_time is None:
                        h_new_cash, h_new_loan = h_cash, h_loan
                        #Withdraw from the bank first, provided that the withdraw argument is True *and* the farm given is actually a bank
                        if withdraw and farm.upgrades[1] >= 3:
                            h_new_cash, h_new_loan = impact(h_new_cash, h_new_loan, farm.account_value)

                        #Now, sell the farm
                        h_new_cash, h_new_loan = impact(h_new_cash, h_new_loan, farm_sellback_values[tuple(farm.upgrades)])
                        farm.h_revenue += h_new_cash - h_cash
                        h_cash, h_loan = h_new_cash, h_new_loan
            else:
                self.logs.append("Selling all farms!")
                self.T5_exists = [False for i in range(3)] #Obviously, if we sell all farms we won't have any T5's anymore!
                for farm in self.farms:
                    farm.sell_time = payout['Time']
        elif dict_obj['Type'] == 'Withdraw Bank':
            if stage == 'check':
                #WARNING: The farm in question must actually be a bank for us to perform a withdrawal!
                #If it isn't, break the loop prematurely
                ind = dict_obj['Index']
                farm = self.farms[ind]
                if farm.sell_time is not None:
                    self.logs.append("WARNING! Tried to withdraw from a bank that was already sold! Aborting buy queue!")
                    self.warnings.append(len(self.logs)-1)
                    self.valid_action_flag = False

                if farm.upgrades[1] < 3:
                    self.logs.append("WARNING! Tried to Withdraw from a farm that is not a bank! Aborting buy queue!")
                    self.warnings.append(len(self.logs)-1)
                    self.valid_action_flag = False
                
                h_new_cash, h_new_loan = impact(h_cash, h_loan, farm.account_value)
                # self.logs.append("Detected bank withdrawal of %s"%(h_new_cash - h_cash))
                farm.h_revenue += h_new_cash - h_cash
                h_cash, h_loan = h_new_cash, h_new_loan
            else:
                ind = dict_obj['Index']
                self.logs.append("Withdrawing money from the bank at index %s"%(ind))
                farm = self.farms[ind]
                farm.account_value = 0
        elif dict_obj['Type'] == 'Activate IMF':
            if stage == 'check':
                #WARNING: The farm in question must actually be an IMF Loan for us to use this ability!
                #If it isn't, set a flag to False and break the loop.
                #DEVELOPER'S NOTE: A farm that has a min_use_time is not necessarily an IMF loan, it could also be an Monkeyopolis
                #Do not upgrade a farm that has already been sold!
                ind = dict_obj['Index']
                farm = self.farms[ind]

                if farm.sell_time is not None:
                    self.logs.append("WARNING! Tried to take out a loan from a bank that was already sold! Aborting buy queue!")
                    self.warnings.append(len(self.logs)-1)
                    self.valid_action_flag = False

                if farm.upgrades[1] != 4:
                    self.logs.append("WARNING! Tried to take out a loan from a farm that is not an IMF! Aborting buy queue!")
                    self.warnings.append(len(self.logs)-1)
                    self.valid_action_flag = False
                    
                ind = dict_obj['Index']
                farm = self.farms[ind]
                
                #When, a loan is activated, treat it like a payment, then add the debt
                h_new_cash, h_new_loan = impact(h_cash, h_loan, farm_globals['IMF Loan Amount'])
                farm.h_revenue += h_new_cash - h_cash
                h_new_loan += farm_globals['IMF Loan Amount']
                h_cash, h_loan = h_new_cash, h_new_loan
            else:
                ind = dict_obj['Index']
                farm = self.farms[ind]
                self.logs.append("Taking out a loan from the IMF at index %s"%(ind))
                farm.min_use_time = payout['Time'] + farm_globals['IMF Usage Cooldown']
        # BOAT FARM RELATED MATTERS
        elif dict_obj['Type'] == 'Buy Boat Farm':
            if stage == 'check':
                h_cash, h_loan = impact(h_cash, h_loan, -1*boat_globals['Merchantmen Cost'])
            else:
                self.logs.append("Purchasing boat farm!")
                boat_farm = {
                    'Initial Purchase Time': self.current_time,
                    'Purchase Time': self.current_time,
                    'Upgrade': 3,
                    'Revenue': 0,
                    'Expenses': boat_globals['Merchantmen Cost'],
                    'Hypothetical Revenue': 0,
                    'Sell Time': None
                }
                self.boat_farms[self.boat_key] = boat_farm
                self.boat_key += 1
        elif dict_obj['Type'] == 'Upgrade Boat Farm':
            if stage == 'check':
                ind = dict_obj['Index']
                boat_farm = self.boat_farms[ind]
                #The following code prevents from the player from having multiple Trade Empires in play
                if boat_farm['Upgrade']+1 == 5 and self.Tempire_exists == True:
                    self.logs.append("WARNING! Tried to purchase a Trade Empire when one already exists! Aborting buy queue!")
                    self.warnings.append(len(self.logs)-1)
                    self.valid_action_flag = False
                upgrade_cost = boat_upgrades_costs[boat_farm['Upgrade']-3]
                h_cash, h_loan = impact(h_cash, h_loan, -1*upgrade_cost)
            else:
                ind = dict_obj['Index']
                        
                self.logs.append("Upgrading the boat farm at index %s"%(ind))
                boat_farm = self.boat_farms[ind]
                boat_farm['Upgrade'] += 1

                #Expense tracking
                boat_farm['Expenses'] += boat_upgrades_costs[boat_farm['Upgrade'] - 4]
                
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
            if stage == 'check':
                ind = dict_obj['Index']
                boat_farm = self.boat_farms[ind]

                #Check whether the boat farm is actually on screen before selling it:
                if boat_farm['Sell Time'] is None:
                    #Selling a farm counts as that farm generating revenue
                    h_new_cash, h_new_loan = impact(h_cash, h_loan, boat_sell_values[boat_farm['Upgrade']-3])
                    boat_farm['Hypothetical Revenue'] += h_new_cash - h_cash
                    h_cash, h_loan = h_new_cash, h_new_loan
                else:
                    self.logs.append("WARNING! Tried to sell a boat farm that is not on screen! Aborting buy queue")
                    self.warnings.append(len(self.logs)-1)
                    self.valid_action_flag = False
            else:
                ind = dict_obj['Index']
                boat_farm = self.boat_farms[ind]
                self.logs.append("Selling the boat farm at index %s"%(ind))
                #If the farm being sold is a Trade Empire, indicate as such
                if boat_farm['Upgrade'] == 5:
                    self.logs.append("The boat farm we're selling is a Trade Empire! Removing the Tempire buff.")
                    self.Tempire_exists = False

                #Mark the boat farm's sell time
                boat_farm['Sell Time'] = payout['Time']
        # DRUID FARM RELATED MATTERS
        elif dict_obj['Type'] == 'Buy Druid Farm':
            if stage == 'check':
                h_cash, h_loan = impact(h_cash, h_loan, -1*druid_globals['Druid Farm Cost'])
            else:
                self.druid_farms[self.druid_key] = payout['Time']
                self.druid_key += 1
                self.logs.append("Purchased a druid farm!")
        elif dict_obj['Type'] == 'Sell Druid Farm':
            if stage == 'check':
                if dict_obj['Index'] == self.sotf:
                    h_cash, h_loan = impact(h_cash, h_loan, game_globals['Sellback Value']*(druid_globals['Druid Farm Cost'] + druid_globals['Spirit of the Forest Upgrade Cost']))
                else:
                    h_cash, h_loan = impact(h_cash, h_loan, game_globals['Sellback Value']*druid_globals['Druid Farm Cost'])
            else:
                ind = dict_obj['Index']
                self.logs.append("Selling the druid farm at index %s"%(ind))
                #If the druid we're selling is actually SOTF...
                if self.sotf is not None and ind == self.sotf:
                    self.logs.append("The druid farm being sold is a Spirit of the Forest!")
                    self.sotf = None
                    self.sotf_min_use_time = None
        elif dict_obj['Type'] == 'Buy Spirit of the Forest':
            if stage == 'check':
                #WARNING: There can only be one sotf at a time!
                if self.sotf is not None:
                    self.logs.append("WARNING! Tried to purchase a Spirit of the Forest when one already exists! Aborting buy queue!")
                    self.warnings.append(len(self.logs)-1)
                    self.valid_action_flag = False
                h_cash, h_loan = impact(h_cash, h_loan, -1*druid_globals['Spirit of the Forest Upgrade Cost'])
            else:
                ind = dict_obj['Index']
                self.sotf = ind
                self.logs.append("Upgrading the druid farm at index %s into a Spirit of the Forest!"%(ind))
                #Determine the minimum time that the SOTF active could be used
                i = np.floor((20 + payout['Time'] - self.druid_farms[ind])/40) + 1
                self.sotf_min_use_time = payout['Time'] + 20 + 40*(i-1)
        elif dict_obj['Type'] == 'Repeatedly Buy Druid Farms':
            #Note, there is no "checking" stage for this action.
            if stage != 'check':
                self.druid_farm_max_buy_time = dict_obj['Maximum Buy Time']
                self.druid_farm_buffer = dict_obj['Buffer']
                self.logs.append("Triggered automated druid farm purchases until time %s"%(self.druid_farm_max_buy_time))
        # SUPPLY DROP RELATED MATTERS
        elif dict_obj['Type'] == 'Buy Supply Drop':
            if stage == 'check':
                h_cash, h_loan = impact(h_cash, h_loan, -1*sniper_globals['Supply Drop Cost'])
            else:
                self.supply_drops[self.sniper_key] = payout['Time']
                self.sniper_key += 1
                self.logs.append("Purchased a supply drop!")
        elif dict_obj['Type'] == 'Sell Supply Drop':
            if stage == 'check':
                if dict_obj['Index'] == self.elite_sniper:
                    h_cash, h_loan = impact(h_cash, h_loan, game_globals['Sellback Value']*(sniper_globals['Supply Drop Cost'] + sniper_globals['Elite Sniper Upgrade Cost']) )
                else:
                    h_cash, h_loan = impact(h_cash, h_loan, game_globals['Sellback Value']*sniper_globals['Supply Drop Cost'])
            else:
                ind = dict_obj['Index']
                self.logs.append("Selling the supply drop at index %s"%(ind))
                #If the supply drop we're selling is actually an E-sniper, then...
                if self.elite_sniper is not None:
                    if ind == self.elite_sniper:
                        self.logs.append("The supply drop being sold is an elite sniper!")
                        self.elite_sniper = None
        elif dict_obj['Type'] == 'Buy Elite Sniper':
            if stage == 'check':
                #WARNING: There can only be one e-sniper at a time!
                if self.elite_sniper is not None:
                    self.logs.append("WARNING! Tried to purchase an Elite Sniper when one already exists! Aborting buy queue!")
                    self.warnings.append(len(self.logs)-1)
                    self.valid_action_flag = False
                h_cash, h_loan = impact(h_cash, h_loan, -1*sniper_globals['Elite Sniper Upgrade Cost'])
            else:
                ind = dict_obj['Index']
                self.elite_sniper = ind
                self.logs.append("Upgrading the supply drop at index %s into an elite sniper!"%(ind))
        elif dict_obj['Type'] == 'Repeatedly Buy Supply Drops':
            #There is no checking stage for this action
            if stage != 'check':
                self.supply_drop_max_buy_time = dict_obj['Maximum Buy Time']
                self.supply_drop_buffer = dict_obj['Buffer']
                self.logs.append("Triggered automated supply drop purchases until time %s"%(self.supply_drop_max_buy_time))
        # HELI FARM RELATED MATTERS
        elif dict_obj['Type'] == 'Buy Heli Farm':
            if stage == 'check':
                h_cash, h_loan = impact(h_cash, h_loan, -1*heli_globals['Heli Farm Cost'])
            else:
                self.heli_farms[self.heli_key] = payout['Time']
                self.heli_key += 1
                self.logs.append("Purchased a heli farm!")
        elif dict_obj['Type'] == 'Sell Heli Farm':
            if stage == 'check':
                if dict_obj['Index'] == self.special_poperations:
                    h_cash, h_loan = impact(h_cash, h_loan, game_globals['Sellback Value']*(heli_globals['Heli Farm Cost'] + heli_globals['Special Poperations Upgrade Cost']) )
                else:
                    h_cash, h_loan = impact(h_cash, h_loan, game_globals['Sellback Value']*heli_globals['Heli Farm Cost'])
            else:
                ind = dict_obj['Index']
                self.logs.append("Selling the heli farm at index %s"%(ind))
                #If the supply drop we're selling is actually a special poperations, then...
                if self.special_poperations is not None:
                    if ind == self.special_poperations:
                        self.logs.append("The heli farm being sold is a special poperations!")
                        self.elite_sniper = None
                
                self.supply_drops.pop(ind)
        elif dict_obj['Type'] == 'Buy Special Poperations':
            if stage == 'check':
                #WARNING: There can only be one Special Poperations on screen at a time!
                if self.special_poperations is not None:
                    self.logs.append("WARNING! Tried to purchase Special Poperations when one already exists! Aborting buy queue!")
                    self.warnings.append(len(self.logs)-1)
                    self.valid_action_flag = False
                h_cash, h_loan = impact(h_cash, h_loan, -1*heli_globals['Special Poperations Upgrade Cost'])
            else:
                ind = dict_obj['Index']
                self.special_poperations = ind
                self.logs.append("Upgrading the heli farm at index %s into special poperations!"%(ind))
        elif dict_obj['Type'] == 'Repeatedly Buy Heli Farms':
            #This action does not have a checking stage.
            if stage != 'check':
                self.heli_farm_max_buy_time = dict_obj['Maximum Buy Time']
                self.heli_farm_buffer = dict_obj['Buffer']
                self.logs.append("Triggered automated heli farm purchases until time %s"%(self.heli_farm_max_buy_time))
        # JERICHO RELATED MATTERS
        elif dict_obj['Type'] == 'Jericho Steal':
            if stage != 'check':
                self.jericho_steal_time = dict_obj['Minimum Buy Time']
                self.jericho_steal_amount = dict_obj['Steal Amount']
                self.cash, self.loan = impact(self.cash,self.loan, dict_obj['Steal Amount']) #If this line is not here, the sim would fail to capture the jeri payment that occurs immediately upon activation.
                
        if stage == 'check':
            return h_cash, h_loan
        elif stage == 'process':
            return None
            
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



# %% [markdown]
# The goal of a simulator like this is to compare different strategies and see which one is better. To this end, we define a function capable of simulating multiple game states at once and comparing them.

# %%
def compareStrategies(initial_state, eco_queues, buy_queues, target_time = None, target_round = 30, display_farms = True, font_size = 12):
    
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

    ax[0].legend(loc='upper left', fontsize = font_size)
    ax[1].legend(loc='upper left', fontsize = font_size)
    
    d = {'Game State': [i for i in range(N)], 'Farm Income': [farm_incomes[i] for i in range(N)]}
    df = pd.DataFrame(data=d)
    
    fig.tight_layout()
    display(df)
    logs.append("Successfully generated graph! \n")