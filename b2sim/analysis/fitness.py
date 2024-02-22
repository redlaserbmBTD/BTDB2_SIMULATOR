import b2sim.engine as b2
from bisect import bisect_left

def cashGen(game_state, parameters = {'Units To Measure': 3, 'Unit Type': 'Rounds', 'Minimum Eco': 0, 'Eco Tolerance': 0}):
    '''
    Evaluates the fitness of a GameState object by determining the amount of cash it generates over the next number of specified rounds or seconds.
    By default the function evaluates over *rounds*.

    The parameters for Minimum Eco and Eco Tolerance allow the end-user to force the AI to seek strategies that gain a certain amount of eco.
    '''

    units_to_measure = parameters['Units To Measure']
    unit_type = parameters['Unit Type']

    fitness_multiplier = 1

    min_eco = parameters.get('Minimum Eco')
    if min_eco is None:
        min_eco = 0
    
    eco_tolerance = parameters.get('Eco Tolerance')
    if eco_tolerance is None:
        eco_tolerance = 0

    lim_eco = min_eco - eco_tolerance

    if game_state.eco <= lim_eco:
        return 0
    elif lim_eco < game_state.eco < min_eco:
        fitness_multiplier = (game_state.eco - lim_eco)/(min_eco - lim_eco)

    # Record the current cash on hand and also what's currently held in banks
    current_cash = game_state.cash
    for farm in game_state.farms:
        if farm.upgrades[1] >= 3:
            current_cash += farm.account_value
    
    game_state.eco_queue.append(b2.ecoSend(send_name = 'Zero'))

    if unit_type == 'Rounds':
        current_round = game_state.rounds.getRoundFromTime(game_state.current_time, get_frac_part = True)
        game_state.fastForward(target_round = current_round + units_to_measure)
    else:
        game_state.fastForward(target_time = game_state.current_time + units_to_measure)

    end_cash = game_state.cash
    for farm in game_state.farms:
        if farm.upgrades[1] >= 3:
            end_cash += farm.account_value

    return fitness_multiplier*max(end_cash - current_cash,0)

def terminalCash(game_state, parameters = {'Target Time': None}):
    '''
    Evaluate the fitness of a GameState object by evaluating the amount of cash it holds at a set time in the future.
    By default, the evaluation occurs at the game state's current time.
    '''

    if parameters['Target Time'] is None:
        target_time = game_state.current_time
    else:
        target_time = parameters['Target Time']

    return game_state.fastForward(target_time)

def penaltyCash(game_state, parameters = {'Penalty Intensity': 1, 'Cash Threshold': [(0,0)], 'Greedy': False}):
    '''
    Penalty function which penalizes the fitness of a GameState object when it fails to maintain a certain level of cash.
    The penalty scales linearly with respect to the amount of time spent below the threshold and the amount of cash short of the threshold.

    Parameters:
    Penalty Intensity determines how harsh the penalty is.
    Cash Threshold is a list of tuples (r,c), where from round r onwards (fractional rounds supported), a penalty is applied for failing for maintain at least c cash.
    If the greedy option is enabled, the sim will consider whether cash + eco exceeds the threshold or not
    '''

    penalty = 0

    cash_threshold = parameters['Cash Threshold']
    target_indices = []
    for entry in cash_threshold:
        ind = bisect_left(game_state.time_states, game_state.rounds.getTimeFromRound(entry[0], get_frac_part = True))
        target_indices.append(ind)

    threshold_index = 0
    cash_threshold = 0
    penalty_intensity = parameters['Penalty Intensity']
    greedy = parameters['Greedy']
    
    for i in range(len(game_state.time_states)):

        # Determine if we need to update the current cash threshold or not
        if threshold_index < len(target_indices) and i >= target_indices[threshold_index]:
            cash_threshold = target_indices[threshold_index]
            threshold_index += 1
        
        # Determine if we are holding enough cash or not. 
        # If not, increase the penalty
        cash = game_state.cash_states[i]
        if greedy:
            cash += game_state.eco_states[i]

        if cash < cash_threshold and i > 0:
            penalty += penalty_intensity*(game_state.time_states[i] - game_state.time_states[i-1])*(cash_threshold - cash)
    
    return penalty