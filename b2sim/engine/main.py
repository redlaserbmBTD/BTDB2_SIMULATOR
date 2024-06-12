# %%
from math import floor, ceil
from b2sim.engine.info import *
from b2sim.engine.actions import *
from b2sim.engine.farms import *
from b2sim.engine.alt_eco import *
from copy import deepcopy as dc

# %%


# %%
def impact(cash: float, loan: float, amount: float):
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

    def __init__(self, initial_state: dict):
        
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
            self.current_round = int(starting_round)
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

        # Next, supply drops!
        # This should be a list of Sniper objects
        self.supply_drops = initial_state.get('Supply Drops')

        # Is there an elite sniper among these supply drops?
        # If so, where is it located?
        self.elite_sniper = None
        if self.supply_drops is None:
            self.supply_drops = []
        for i in range(len(self.supply_drops)):
            if self.supply_drops[i].T5 and self.elite_sniper is None:
                self.elite_sniper = i
            if self.supply_drops[i].T5 and self.elite_sniper is not None:
                # Prevents the sim from running with multiple T5 snipers
                self.supply_drops[i].T5 = False
                self.supply_drops[i].update()

        #Next, heli farms!
        self.heli_farms = initial_state.get('Heli Farms')
        if self.heli_farms is not None:
            self.special_poperations = self.heli_farms['Special Poperations Index']
            self.heli_key = len(self.heli_farms) - 2
        else:
            self.special_poperations = None
            self.heli_key = 0

        # Next, overclocks!
        overclock_info = initial_state.get('Overclocks')
        if overclock_info is not None:
            self.overclocks = overclock_info['Overclocks']
            self.ultraboost_index = overclock_info['Ultraboost Index']
        else:
            self.overclocks = []
            self.ultraboost_index = None

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
            self.eco_queue = []
        self.number_of_sends = 0

        eco_send = initial_state.get('Eco Send')
        self.send_name = None
        if eco_send is not None:
            eco_send['Time'] = 0
            self.send_name = eco_send['Send Name']
            self.eco_queue.insert(0,eco_send)

        if len(self.eco_queue) == 0: # In case there's no specified sends at all
            self.eco_queue = [ecoSend(time = 0, send_name = 'Zero')]

        self.available_sends = [] # Tracks the available eco sends at a given point in time.
        for send_name in eco_send_info.keys():
            if eco_send_info[send_name]['Start Round'] <= self.current_round <= eco_send_info[send_name]['End Round']:
                self.available_sends.append(send_name)
        self.last_checked_round = self.current_round

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

        #For the AI
        self.save = 0 # When eco'ing, we will not let our cash dip below this amount.

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
            self.supply_drops = []
        self.simulation_start_time = 0

        self.max_send_amount = None
        self.max_eco_amount = None
        self.max_send_time = None
            
        self.logs.append("MESSAGE FROM GameState.__init__(): ")
        self.logs.append("Initialized Game State!")
        self.logs.append("The current game round is %s"%(self.current_round))
        self.logs.append("The current game time is %s seconds"%(self.current_time))
        self.logs.append("The game round start times are given by %s \n"%(self.rounds.round_starts))

    def sortFarms(self, debug = False):
        '''
        Sorts farms by the following criteria:
        1. Active vs. inactive farms (active farms go first)
        2. Increasing cost.
        '''

        if len(self.farms) > 0:
            # print(self.farms)
            def crit(farm):
                val = farm_total_cost_values[tuple(farm.upgrades)]
                # print("val: %s"%(val))
                if farm.sell_time:
                    # Since no single farm costs $200,000 or more, this causes all inactive farms to be sorted *last* when we sort in increasing order
                    val += 200000
                return val
            
            self.farms.sort(key=crit)
        
        if debug:
            print(self.farms)

    def argsortFarms(self):
        '''
        Returns a list of indices corresponding to farms sorted by the following criteria:
        1. Active vs. inactive farms (active farms go first)
        2. Increasing sellback value

        Returns None if no farms (active or inactive) are present
        '''
        # print("RUNNING ARGSORT")
        if len(self.farms) > 0:
            def crit(n):
                farm = self.farms[n]
                val = farm_sellback_values[tuple(farm.upgrades)]
                if farm.sell_time:
                    val = val + 200000
                return val
            
            arg_list = [i for i in range(len(self.farms))]
            arg_list.sort(key=crit)
            # print("RESULT: %s"%(arg_list))
            return arg_list
        else:
            # print("WARNING! No farms to sort!")
            return None

    def checkProperties(self):
        '''
        Helper method for self.ecoQueueCorrection. 

        Looks at the first send in the eco queue and modifies properties of that send if those properties are not available to the eco send.

        '''
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
        ''' 
        Automatically adjusts the eco queue so that the first send in the queue is valid.
        Automatically adjust the list of available eco sends.

        Essentially, the code works like this:
        Look at the first send in the queue and decide if the time to use the send is too early or late, or if there is otherwise no circumstance under which the send will be used during simulation.
        - If it's too late (we are beyond the last round which we would use the send), remove the send from the queue
        - If it's too early, adjust the time to earliest available time we can use the send
        
        If the process above results in the first send in the queue being slated to be used after the second, *remove* the first send.
        The process above repeats until either the queue is empty or the first send in the queue is valid.

        Once it is determined that the first send in the queue is valid, check for and remove any properties from the eco which cannot be applied to said send.

        When the process above is complete, we must check whether we should change to first send in the queue right now or not.
        - If the answer is no, we can exit the process.
        - If the answer is yes, switch to said send, and then rerun the queue correction process so that the *new* first eco send in the queue is valid (if necessary).
        ''' 

        # To begin, if necessary, update the list of available eco sends to use.
        if self.last_checked_round is None or self.last_checked_round < self.current_round:
            # If we have yet to form the list of available eco sends...
            self.available_sends = []
            for send_name in eco_send_info.keys():
                if eco_send_info[send_name]['Start Round'] <= self.current_round <= eco_send_info[send_name]['End Round']:
                    self.available_sends.append(send_name)
            self.last_checked_round = self.current_round

        # This flag is set to true when the first send in the queue is known to be valid AND it is not possible to change to that send right now.
        # The code is finished then this flag is set to True OR the eco queue is empty
        future_flag = False

        while len(self.eco_queue) > 0 and future_flag == False:
            # This flag is set to true as soon as it is known that the first send in the queue is valid.
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
                                print(self.eco_queue)
                                if len(self.eco_queue) < 2 or (self.eco_queue[1]['Time'] is None or self.eco_queue[0]['Time'] < self.eco_queue[1]['Time']):
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
            
            if self.changeNow():
                self.changeEcoSend()
            else:
                # Add code here which changes to the 0 send if for whatever reason there isn't already a send in the queue
                if self.eco_cost is None:
                    self.eco_queue[0] = ecoSend(send_name='Zero')
                    self.changeEcoSend()
                future_flag = True

    def changeNow(self):
        '''
        Helper method for ecoQueueCorrection. 
        Determines during the queue correction process whether it is necessary to change to the next send in the queue or not

        Returns:
        Boolean
        '''

        # Do NOT change if there is not a send in the queue to change to
        if not len(self.eco_queue) > 0:
            self.logs.append("self.changeNow returned False! The queue is empty!")
            return False
        
        # Do change if there is a given time to use that send and we are beyond that given time
        if (self.eco_queue[0]['Time'] is not None and self.eco_queue[0]['Time'] <= self.current_time):
            return True

        max_flag, eco_flag, time_flag = False, False, False
        
        # print(self.max_send_amount)
        # print(self.max_eco_amount)
        # print(self.max_send_time)

        if self.max_send_amount is None or (self.max_send_amount and self.number_of_sends >= self.max_send_amount):
            max_flag = True
        
        if self.max_eco_amount is None or (self.max_eco_amount and self.eco >= self.max_eco_amount):
            eco_flag = True

        if self.max_send_time is None or (self.max_send_time and self.current_time > self.max_send_time):
            time_flag = True
        
        # If there is no given time, check whether we have exhausted the break conditions on the existing send. 
        if self.eco_queue[0]['Time'] is None and max_flag and eco_flag and time_flag:
            return True
        
        self.logs.append("self.changeNow returned False!")
        return False
        
    def changeEcoSend(self):
        '''
        Attempt to change to the first send available in the eco queue. 
        If the send is not yet available, switch to the zero send and reinsert the send in question back into the queue at a later time.
        If the send is no longer available, switch to the zero send and remove the send from the queue entirely.

        Contributors/Pracitioners: As a best practice, please avoid writing code or running simulations which may trigger the fail-safes in this method.
        '''
        
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
            self.eco_queue.insert(0,dc(send_info))
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


        # First, check if the send has any fortifed, camo, or regrow characteristics
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
        '''
        Simulates the game state over the time period (self.current_time, target_time].

        Parameters:
        target_time: The time the simulation should end at
        target_round: The round the simulation should end at. If both a target_time and a target_round are given, the code will prioritize the target_round
        interval: Determines how frequently the code will record cash and eco values.

        Returns:
        None
        '''

        self.logs.append("MESSAGE FROM GameState.fastForward: ")
        self.valid_action_flag = True #To prevent the code from repeatedly trying to perform a transaction that obviously can't happen
        self.simulation_start_time = self.current_time
        
        # If a target round is given, compute the target_time from that
        if target_round is not None:
            target_time = self.rounds.getTimeFromRound(target_round)

        # Append messages to the event messages list showing when each round starts
        given_round = floor(self.rounds.getRoundFromTime(self.current_time, get_frac_part = True) + 1)
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
            intermediate_time = min(max(floor(self.current_time/interval + 1)*interval,self.current_time + interval/2),target_time)
            self.logs.append("Advancing game to time %s"%(round(intermediate_time,3)))
            self.advanceGameState(target_time = intermediate_time)
            #self.logs.append("----------")

        # Sort the messages in self.event_messages so that they are listed chronologically
        self.event_messages = sorted(self.event_messages, key=lambda x: x['Time']) 

        # Show warning messages for fail-safes triggered during simulation
        self.showWarnings(self.warnings)
        
        self.logs.append("Advanced game state to round " + str(self.current_round))
        self.logs.append("The current time is " + str(self.current_time))
        self.logs.append("The next round starts at time " + str(self.rounds.round_starts[self.current_round+1]))
        self.logs.append("Our new cash and eco is given by (%s,%s) \n"%(round(self.cash,2),round(self.eco,2)))

    def advanceGameState(self, target_time = None, target_round = None):
        '''
        Helper method for self.fastForward, attempts to simulate the game state to target_time but terminates early if:
        - The code needs to change eco sends
        - A purchase is made in the buy queue

        In order to simulate to the desired target time, fastForward *repeatedly* runs this method until the game state finally reachs the target time.
        '''

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
                    self.logs.append("The break time does not occur exactly when a payout is scheduled.")
                    target_time = self.current_time
                    break
                else:
                    self.logs.append("The break time does occur exactly when a payout is scheduled.")
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
                    elif payout['Source'] == 'Sniper':
                        key = payout['Index']
                        sniper = self.supply_drops[key]
                        sniper.revenue += new_cash - self.cash

                    self.cash, self.loan = new_cash, new_loan
                    self.logs.append("Awarded direct payment %s at time %s"%(round(payout['Payout'],2),round(payout['Time'],2)))
                
                
            elif payout['Payout Type'] == 'Bank Payment':
                #Identify the bank that we're paying and deposit money into that bank's account
                #NOTE: Bank deposits are not impacted by IMF Loans. It is only when we withdraw the money that the loan is repaid
                key = payout['Index']
                farm = self.farms[key]
                farm.account_value += payout['Payout']
                self.logs.append("Awarded bank payment %s at time %s to farm at index %s"%(round(payout['Payout'],2),round(payout['Time'],2), key))
                if farm.account_value >= farm.max_account_value:
                    #At this point, the player should withdraw from the bank.
                    farm.account_value = 0
                    new_cash, new_loan = impact(self.cash,self.loan,farm.max_account_value)
                    farm.revenue += new_cash - self.cash #Track the money generated by the farm
                    self.cash, self.loan = new_cash, new_loan
                    self.logs.append("The bank at index %s reached max capacity! Withdrawing money"%(key))
                self.logs.append("The bank's new account value is %s"%(farm.account_value))
            elif payout['Payout Type'] == 'Bank Interest':
                #Identify the bank that we're paying and deposit the start of round bank bonus, then give interest
                key = payout['Index']
                farm = self.farms[key]
                farm.account_value += farm.payout(payout['Time'], bank_interest = True)
                farm.account_value *= farm_globals['Start of Round Bank Multiplier']
                self.logs.append("Awarded bank interest at time %s to the farm at index %s"%(round(payout['Time'],2), key))
                if farm.account_value >= farm.max_account_value:
                    farm.account_value = 0
                    new_cash, new_loan = impact(self.cash,self.loan,farm.max_account_value)
                    farm.revenue += new_cash - self.cash #Track the money generated by the farm
                    self.cash, self.loan = new_cash, new_loan
                    self.logs.append("The bank at index %s reached max capacity! Withdrawing money"%(key))
                self.logs.append("The bank's new account value is %s"%(farm.account_value))
            elif payout['Payout Type'] == 'Eco':
                self.cash, self.loan = impact(self.cash,self.loan, self.eco)
                self.logs.append("Awarded eco payment %s at time %s"%(round(self.eco,2),round(payout['Time'],2)))
            
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
                    self.supply_drops.append(Sniper(payout['Time']))
                    self.supply_drops[-1].expenses += sniper_globals['Supply Drop Cost']
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
            
            #print("New cash and eco is (%s,%s)"%(round(self.cash,2), round(self.eco,2)))
            if i == len(payout_times)-1 or payout_times[i]['Time'] < payout_times[i+1]['Time']:
                self.time_states.append(payout['Time'])
                self.cash_states.append(self.cash)
                self.eco_states.append(self.eco)

            #If either the cash or eco values changed since last time, record this in the log
            if len(self.cash_states) == 1 or self.cash_states[-1] != self.cash_states[-2] or len(self.eco_states) == 1 or self.eco_states[-1] != self.eco_states[-2]:
                self.logs.append("Recorded cash and eco values (%s,%s) at time %s"%(round(self.cash,2),round(self.eco,2),round(payout['Time'],2)))
            
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
        #self.logs.append("Our new cash and eco is given by (%s,%s) \n"%(round(self.cash,2),round(self.eco,2)))
           
    def computePayoutSchedule(self, target_time: float):
        '''
        Helper method for advanceGameState

        Given a target time target_time, return an ordered list of all payouts to occur from the game state's current time until the designated target time.
        
        Parameters:
        target_time (float): the latest time (inclusive) of any payment to be included in the payout schedule.

        Returns:
        payout_times (List[dict]): a list of dictionaries, each of which represents a payment.

        '''
        
        
        payout_times = []
        
        #ECO PAYOUTS
        eco_time = 6*(floor(self.current_time/6)+1)
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
                use_index = max(1,floor(1 + (self.current_time - druid_farm - druid_globals['Druid Farm Initial Cooldown'])/druid_globals['Druid Farm Usage Cooldown'])+1)
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
        for i in range(len(self.supply_drops)):
            sniper = self.supply_drops[i]
            if sniper.sell_time is None:
                payout_amount = sniper.payout_amount

                supply_drop = sniper.purchase_time
                #Determine the earliest supply drop activation that could occur within the interval of interest (self.current_time,target_time]
                drop_index = max(1,floor(1 + (self.current_time - supply_drop - sniper_globals['Supply Drop Initial Cooldown'])/sniper_globals['Supply Drop Usage Cooldown'])+1)
                supply_drop_time = supply_drop + sniper_globals['Supply Drop Initial Cooldown'] + sniper_globals['Supply Drop Usage Cooldown']*(drop_index-1)
                while supply_drop_time <= target_time:
                    
                    payout_entry = {
                        'Time': supply_drop_time,
                        'Payout Type': 'Direct',
                        'Payout': payout_amount,
                        'Source': 'Sniper',
                        'Index': i
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
                drop_index = max(1,floor(1 + (self.current_time - heli_farm - heli_globals['Heli Farm Initial Cooldown'])/heli_globals['Heli Farm Usage Cooldown'])+1)
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
        for key, farm in enumerate(self.farms):
            farm_payout_times = farm.computePayoutSchedule(self.current_time, target_time, self.rounds, self.T5_exists[0])
            for farm_payout_entry in farm_payout_times:
                farm_payout_entry['Index'] = key
            payout_times.extend(farm_payout_times)
        
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
        '''
        Helper method which simulates eco *only* in the game state from the current game time to the specified target_time.
        The general purpose of this method is to compute the amount of cash and eco gained/lost in between payouts from other sources.

        Contributors, do NOT write code which asks this function to operate over a time period during which a different income source may award a payment.

        Parameters:
        target_time (float): The time to simulate to.

        Returns:
        None
        '''
        
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
            if self.cash >= max(self.eco_cost, self.save) and len(self.attack_queue) < min(6, self.attack_queue_threshold):
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
            
            elif self.cash < max(self.eco_cost, self.save):
                # No, we don't have money!
                self.attack_queue_unlock_time = target_time + self.eco_delay/2

    def processBuyQueue(self, payout):
        '''
        Helper function for advanceGameState. Examine the buy queue and determine if any purchases can be made within said queue.
        Generally, this method is called every time a payout is received in the simulator.

        Parameters:
        payout (dict): The payout just received before looking at the buy queue

        Returns:
        None
        '''
        
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

                    #If the dict_obj is a Overclock use, force self.min_buy_time to be least the use time of the Overclock
                    if dict_obj['Type'] == 'Use Overclock':
                        ind = dict_obj['Engineer Index']
                        if self.overclocks[ind]['Use Time'] is not None and self.overclocks[ind]['Use Time'] > self.min_buy_time:
                            self.min_buy_time = self.overclocks[ind]['Use Time']
                    
                # self.logs.append("Determined the minimum buy time of the next purchase to be %s"%(self.min_buy_time))
                        
            # If we have not yet reached the minimum buy time, break the while loop. 
            # We will check this condition again later:
            if payout['Time'] < self.min_buy_time:
                break

            # If the purchase info requires us to upgrade a farm more than once...
            new_actions = []
            for i in range(len(purchase_info)):
                if purchase_info[i]['Type'] == 'Upgrade Farm' and purchase_info[i]['Upgrades'] is not None:
                    upgrades = list(purchase_info[i]['Upgrades'])
                    ind = purchase_info[i]['Index']
                    farm = self.farms[ind]
                    current_upgrades = dc(farm.upgrades)

                    # How many times do we have to upgrade the farm in order for it to reach it's desired path?
                    num_upgrades = sum([upgrades[j] - current_upgrades[j] for j in range(3)])
                    # print("num_upgrades: %s"%(num_upgrades))

                    if num_upgrades > 1:
                        # Which path would be the farm's primary path?
                        arr = [0,1,2]
                        arr.sort(key = lambda n: upgrades[n])
                        primary_path = arr[-1]
                        secondary_path = arr[-2]

                        # Amend the buy queue by adding items which upgrade the farm in a certain order
                        # First, if necessary, build the 200 farm
                        while current_upgrades[0] < min(2, upgrades[0]):
                            current_upgrades[0] += 1
                            new_actions.append([upgradeFarm(ind, upgrades=tuple(current_upgrades))])
                        
                        # Next, build the farm's *primary* path to T3
                        while current_upgrades[primary_path] < min(3, upgrades[primary_path]):
                            current_upgrades[primary_path] += 1
                            new_actions.append([upgradeFarm(ind, upgrades=tuple(current_upgrades))])

                        # Next, build the farm's crosspath up twice
                        while current_upgrades[secondary_path] < min(2,upgrades[secondary_path]):
                            current_upgrades[secondary_path] += 1
                            new_actions.append([upgradeFarm(ind, upgrades=tuple(current_upgrades))])

                        # Finally, build the primary path up completely
                        while current_upgrades[primary_path] < min(5, upgrades[primary_path]):
                            current_upgrades[primary_path] += 1
                            new_actions.append([upgradeFarm(ind, upgrades=tuple(current_upgrades))])

                        # If the original compound action *also* involved automatic farm selling, tack this on to the *final* element in new actions
                        if len(new_actions) > 0:
                            new_actions[-1][0]['Auto Sell'] = purchase_info[i]['Auto Sell']

                        # Carryovers
                        for action in new_actions:
                            action[0]['Buffer'] = purchase_info[i]['Buffer']
                            action[0]['Minimum Buy Time'] = purchase_info[i]['Minimum Buy Time']
                        break
            
            # Break up multiple farm upgrades into different actions
            if len(new_actions) > 0:
                self.buy_queue.pop(0)
                self.buy_queue = new_actions + self.buy_queue
                # self.logs.append("Warning! Automatically splitting a farm upgrade action into multiple actions! The new buy queue is %s"%(self.buy_queue))
                # self.warnings.append(len(self.logs)-1)
                purchase_info = new_actions[0]
                
            # If the purchase info includes an action for automated selling into more complicated purchases
            # print("Checking for compound purchase:")
            for i in range(len(purchase_info)):
                # print(purchase_info[i]['Type'] + ' ' + str(purchase_info[i].get('Auto Sell')))
                if purchase_info[i]['Type'] == 'Upgrade Farm' and purchase_info[i]['Auto Sell'] is not None:
                    arg_list = self.argsortFarms()
                    new_purchase_info = dc(purchase_info[0:i])
                    
                    try:
                        arg_list.remove(purchase_info[i]['Index'])
                    except:
                        pass
                    
                    j = 0
                    while (arg_list is not None) and (j < min(len(arg_list), purchase_info[i]['Auto Sell'])) and (self.farms[arg_list[j]].sell_time is None):
                        # self.logs.append("GOT TO HERE!")
                        # self.warnings.append(len(self.logs)-1)
                        new_purchase_info.append(sellFarm(arg_list[j]))
                        j += 1
                            

                    purchase_info[i]['Auto Sell'] = None
                    new_purchase_info.extend(purchase_info[i:])
                    purchase_info = dc(new_purchase_info)
                    self.buy_queue[0] = dc(new_purchase_info)

                    # self.logs.append("Warning! Automatically determining farms to sell for a compound upgrade! The new buy queue is %s"%(self.buy_queue))
                    # self.warnings.append(len(self.logs)-1)
                    break

                
            
            # Next, let's compute the cash and loan values we would have if the transaction was performed
            # We will compute the hypothetical revenues each farm would have if the transactions were carried out
            # In general the this step is necessary if there are in the presence of loans.
            # NOTE: Loans do not influence purchases, so we can process expense tracking for farms only when a transaction actually occurs.

            #For tracking the revenue of farms
            for farm in self.farms:
                farm.h_revenue = farm.revenue

            #For tracking the revenue of snipers
            for sniper in self.supply_drops:
                sniper.h_revenue = sniper.revenue

            #For tracking the revenue of boat farms
            for key in self.boat_farms.keys():
                boat_farm = self.boat_farms[key]
                boat_farm['Hypothetical Revenue'] = boat_farm['Revenue']
            
            for dict_obj in purchase_info:

                h_loan_before = h_loan
                h_cash, h_loan = self.processAction(dict_obj, payout, h_cash = h_cash, h_loan = h_loan, stage = 'check')

                #Immediately abort attempting the purchase if we try to process an action that is not possible:
                if not self.valid_action_flag:
                    break
                    
                #If at any point while performing these operations our cash becomes negative OR if we took on more debt while still in debt, then prevent the transaction from occurring:
                if h_cash < 0 or h_loan > h_loan_before:
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
            
            #self.logs.append("We have %s cash, but the next buy costs %s and has a buffer of %s and needs to be made on or after time %s!"%(round(self.cash,2), round(self.cash - h_cash,2),round(self.buffer,2), self.min_buy_time))
            if h_cash >= self.buffer:
                #If we do, perform the buy!
                made_purchase = True
                self.logs.append("We have %s cash! We can do the next buy, which costs %s and has a buffer of %s and a minimum buy time of %s!"%(round(self.cash,2), round(self.cash - h_cash,2),round(self.buffer,2),round(self.min_buy_time,2)))

                # Make the adjustments to the cash and loan amounts
                self.cash = h_cash
                self.loan = h_loan

                # Track the revenue made by each farm
                for farm in self.farms:
                    farm.revenue = farm.h_revenue

                # Track the revenue made by each sniper farm
                for sniper in self.supply_drops:
                    sniper.revenue = sniper.h_revenue

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
                farm_cost = farm_total_cost_values[dict_obj['Upgrades']]
                h_cash, h_loan = impact(h_cash, h_loan, -1*farm_cost)
            else:
                self.logs.append("Purchasing farm!")
                farm_info = initFarm(purchase_time = payout['Time'], upgrades = list(dict_obj['Upgrades']))
                farm = MonkeyFarm(farm_info)
                self.farms.append(farm)

                #For revenue and expense tracking
                farm.revenue = 0
                farm.expenses = farm_total_cost_values[dict_obj['Upgrades']]
        elif dict_obj['Type'] == 'Upgrade Farm':
            # There are two ways this function can be used. 
            ind = dict_obj['Index']
            path = dict_obj['Path']
            upgrades = dict_obj['Upgrades']
            farm = self.farms[ind]

            if stage == 'check':
                #Do not upgrade a farm that has already been sold!
                if farm.sell_time is not None:
                    self.logs.append("WARNING! Tried to upgrade a farm that was already sold! Aborting buy queue!")
                    self.warnings.append(len(self.logs)-1)
                    self.valid_action_flag = False
                
                #If the user specified for a specific set of upgrades, use that argument
                if upgrades is not None:
                    #Prevent the user from upgrading to a T5 farm if that T5 is already in play
                    for i in range(3):
                        if upgrades[i] == 5 and self.T5_exists[i]:
                            self.logs.append("WARNING! Tried to purchase a T5 farm when one of the same kind already existed! Aborting buy queue!")
                            self.warnings.append(len(self.logs)-1)
                            self.valid_action_flag = False

                    #For each of top path, middle path, and bottom path, determine the number of upgrades that need to be made
                    #Then, determine the cost of those upgrades
                    upgrades_costs = 0
                    for i in range(3):
                        #How many times do we need to upgrade the path?
                        times_to_upgrade = upgrades[i] - farm.upgrades[i]
                        if times_to_upgrade < 0:
                            self.logs.append("----")
                            self.logs.append("WARNING! Tried to downgrade a farm! Aborting buy queue!")
                            self.logs.append("The farm at index %s was a (%s,%s,%s) farm"%(ind, farm.upgrades[0], farm.upgrades[1], farm.upgrades[2]))
                            self.logs.append("We tried to upgrade it to a (%s,%s,%s) farm"%(upgrades[0],upgrades[1],upgrades[2]))
                            self.logs.append("The current list of farms is given by:")
                            self.logs.append(self.farms)
                            self.logs.append("The current buy queue looks like: ")
                            self.logs.append(self.buy_queue)
                            for i in range(8,0,-1):
                                self.warnings.append(len(self.logs)-i)
                            self.valid_action_flag = False

                        #How much do those upgrades cost?
                        for j in range(times_to_upgrade):
                            upgrades_costs += farm_upgrades_costs[i][farm.upgrades[i] + j]

                    h_cash, h_loan = impact(h_cash, h_loan, -1*upgrades_costs)

                elif path is not None:
                    #If the user specifies a specfic path, 
                    #Prevent the user from upgrading to a T5 farm if that T5 is already in play
                    if farm.upgrades[path]+1 == 5 and self.T5_exists[path] == True:
                        self.logs.append("WARNING! Tried to purchase a T5 farm when one of the same kind already existed! Aborting buy queue!")
                        self.warnings.append(len(self.logs)-1)
                        self.valid_action_flag = False
                    
                    h_cash, h_loan = impact(h_cash, h_loan, -1*farm_upgrades_costs[path][farm.upgrades[path]])
            else:
                if upgrades is not None:
                    farm.upgrade(payout['Time'], upgrades, mode = 'Upgrades')
                    self.logs.append("Upgraded the farm at index %s to (%s,%s,%s)"%(ind,upgrades[0],upgrades[1],upgrades[2]))

                elif path is not None:
                    self.logs.append("Upgrading path %s of the farm at index %s"%(path, ind))
                    farm.upgrade(payout['Time'], path, mode = 'Path')

                    self.logs.append("Upgraded the farm at index %s to (%s,%s,%s)"%(ind, farm.upgrades[0],farm.upgrades[1],farm.upgrades[2]))
                    
                #If the resulting farm is a Banana Central, activate the BRF buff, giving them 25% more payment amount
                if farm.upgrades[0] == 5 and path == 0:
                    self.logs.append("The new farm is a Banana Central!")
                    self.T5_exists[0] = True
                    
                #If the resutling farm is a Monkeynomics, mark the x5x_exists flag as true to prevent the user from trying to have multiple of them
                if farm.upgrades[1] == 5 and path == 1:
                    self.T5_exists[1] = True
                
                #If the resulting farm is a MWS, mark the MWS_exists flag as true to prevent the user from trying to have multiple of them.
                if farm.upgrades[2] == 5 and path == 2:
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
            withdraw = dict_obj['Withdraw']
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
        elif dict_obj['Type'] == 'Withdraw All Banks':
            if stage == 'check':
                for farm in self.farms:
                    if farm.bank:
                        h_new_cash, h_new_loan = impact(h_cash, h_loan, farm.account_value)
                        farm.h_revenue += h_new_cash - h_cash
                        h_cash, h_loan = h_new_cash, h_new_loan
            else:
                self.logs.append("Withdrawing money from all banks!")
                for farm in self.farms:
                    if farm.bank:
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
                boat_farm['Purchase Time'] = payout['Time']
                
                #Update the sellback value of the boat farm
                boat_farm['Sell Value'] = boat_sell_values[boat_farm['Upgrade'] - 3]

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
                i = floor((20 + payout['Time'] - self.druid_farms[ind])/40) + 1
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
                self.supply_drops.append(Sniper(payout['Time']))
                self.supply_drops[-1].expenses = sniper_globals['Supply Drop Cost']
                self.logs.append("Purchased a supply drop!")
        elif dict_obj['Type'] == 'Sell Supply Drop':
            ind = dict_obj['Index']
            sniper = self.supply_drops[ind]
            if stage == 'check':
                h_new_cash, h_new_loan = h_cash, h_loan
                if dict_obj['Index'] == self.elite_sniper:
                    h_new_cash, h_new_loan = impact(h_cash, h_loan, game_globals['Sellback Value']*(sniper_globals['Supply Drop Cost'] + sniper_globals['Elite Sniper Upgrade Cost']) )
                else:
                    h_new_cash, h_new_loan = impact(h_cash, h_loan, game_globals['Sellback Value']*sniper_globals['Supply Drop Cost'])
                sniper.h_revenue += h_new_cash - h_cash
                h_cash, h_loan = h_new_cash, h_new_loan
            else:
                ind = dict_obj['Index']
                self.logs.append("Selling the supply drop at index %s"%(ind))
                #If the supply drop we're selling is actually an E-sniper, then...
                if self.elite_sniper is not None and ind == self.elite_sniper:
                    self.logs.append("The supply drop being sold is an elite sniper!")
                    self.elite_sniper = None
                    self.supply_drops[ind].T5 = False
                    self.supply_drops[ind].sell_time = payout['Time']
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
                self.supply_drops[ind].upgrade()
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
                        self.special_poperations = None
                
                self.heli_farms.pop(ind)
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
        # OVERCLOCK RELATED MATTERS
        elif dict_obj['Type'] == 'Buy Overclock':
            if stage == 'check':
                h_cash, h_loan = impact(h_cash, h_loan, -1*engi_globals['Overclock Cost'])
            else:
                self.logs.append("Purchasing overclock!")
                self.overclocks.append({
                    'Initial Purchase Time': payout['Time'],
                    'Use Time': payout['Time'],
                    'Sell Time': None
                })
        elif dict_obj['Type'] == 'Use Overclock':
            ind = dict_obj['Engineer Index']
            overclock = self.overclocks[ind]

            if stage == 'check':
                if overclock['Sell Time'] is not None:
                    self.logs.append("WARNING! Tried to use an overclock that was already sold! Aborting buy queue!")
                    self.warnings.append(len(self.logs)-1)
                    self.valid_action_flag = False
            else:
                # Overclock the farm
                farm = self.farms[dict_obj['Farm Index']]
                farm.overclock(payout['Time'])

                # Update the use time of the overclock
                if self.ultraboost_index is not None and ind == self.ultraboost_index:
                    #The overclock is in fact an ultraboost
                    overclock['Use Time'] = payout['Time'] + engi_globals['Ultraboost Usage Cooldown']
                else:
                    #The overclock is just a normal overclock
                    overclock['Use Time'] = payout['Time'] + engi_globals['Overclock Usage Cooldown']


        elif dict_obj['Type'] == 'Sell Overclock':
            ind = dict_obj['Index']
            overclock = self.overclocks[ind]
            if stage == 'check':
                #Check whether the overclock is actually on screen before selling it:
                if overclock['Sell Time'] is None:
                    if self.ultraboost_index is not None and ind == self.ultraboost_index:
                        sell_value = game_globals['Sellback Value']*(engi_globals['Overclock Cost'] + engi_globals['Ultraboost Upgrade Cost'])
                    else:
                        sell_value = game_globals['Sellback Value']*engi_globals['Overclock Cost']
                    h_cash, h_loan = impact(h_cash, h_loan, sell_value)
                else:
                    self.logs.append("WARNING! Tried to sell an overclock that is not on screen! Aborting buy queue")
                    self.warnings.append(len(self.logs)-1)
                    self.valid_action_flag = False
            else:
                ind = dict_obj['Index']
                overclock = self.overclocks[ind]
                overclock['Sell Time'] = payout['Time']

                #If the overclock being sold is an ultraboost, update the ultraboost index
                if self.ultraboost_index is not None and ind == self.ultraboost_index:
                    self.ultraboost_index = None
                
                self.logs.append("Selling the overclock at index %s"%(ind))
        elif dict_obj['Type'] == 'Buy Ultraboost':
            if stage == 'check':
                #Do not allow the ultraboost to be purchased if there is already an ultraboost on screen.
                if self.ultraboost_index is not None:
                    self.logs.append("WARNING! There is already an Ultraboost on screen! Aborting buy queue")
                    self.warnings.append(len(self.logs)-1)
                    self.valid_action_flag = False
                h_cash, h_loan = impact(h_cash, h_loan, engi_globals['Ultraboost Upgrade Cost'])
            else:
                ind = dict_obj['Index']
                overclock = self.overclocks[ind]
                overclock['Use Time'] = payout['Time'] #The Ultraboost ability is battle ready.
                self.ultraboost_index = ind

        if stage == 'check':
            return h_cash, h_loan
        elif stage == 'process':
            return None
            