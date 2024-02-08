import neat
import b2sim.analysis.visualize as viz
from b2sim.analysis.graphs import viewHistory
import b2sim.engine as b2
from copy import deepcopy as dc
from bisect import bisect_left
import os

# To begin, form a list of all AI farm actions
# I'll *also* form a dictionary that points upgrade tuples to per round incomes

ai_actions_base = []
farm_incomes = {}
for key in b2.farm_payout_values.keys():
    ppr = b2.farm_payout_values[key][0]*b2.farm_payout_values[key][1]
    if key[2] == 5:
        #Accounting for the MWS bonus
        ppr += 10000
    
    if key[1] >= 3:
        #Accounting for banks in particular
        ppr = b2.farm_globals['Start of Round Bank Multiplier']*(ppr + b2.farm_globals['Start of Round Bank Payment'])
    
    entry = {
        'Type': 'Purchase',
        'Upgrades': key,
        'Income': ppr,
        'Cost': b2.farm_total_cost_values[key]
    }
    ai_actions_base.append(entry)
    farm_incomes[key] = ppr

# Some of these farms are inefficient, let's wipe those entries corresponding to inefficient farms
def pruneActions(arr):
    arr.sort(key=lambda x: x['Cost'])
    payout_to_beat = 0
    i = 0
    while i < len(arr):
        if arr[i]['Income'] <= payout_to_beat:
            arr.pop(i)
        else:
            payout_to_beat = arr[i]['Income']
            i += 1

    return arr

ai_actions_base = dc(pruneActions(ai_actions_base))

def simulate(neural_net, game_state, target_time, increment_value = 6, max_farms = 5):
    '''
    Simulate a GameState from its current time to the target time by having a neural network automatically
    determine what actions to take during the simulation.
    '''
    
    while game_state.current_time < target_time:
        # Pass the current game info through the genome, giving it the chance to process and spit out an output
        output = neural_net.activate((game_state.cash, game_state.eco, game_state.current_time, farmIncome(game_state)))
        eco_intensity, buy_farms = 20*output[0],output[1]

        # What eco send should we use next?
        available_sends = efficientFrontier(game_state.available_sends)
        eco_send = ecoIntensity(eco_intensity, available_sends)
        if game_state.send_name != eco_send:
            game_state.eco_queue.append(b2.ecoSend(send_name = eco_send))

        # Determine if we should purchase farms or not.
        if buy_farms >= 0.9:
            cash_to_spend = game_state.cash*buy_farms
            if len(game_state.farms) < max_farms:
                ai_actions = aiGetActions(game_state.farms, ai_actions_base)
            else:
                ai_actions = aiGetActions(game_state.farms, [])

            action_dict = aiBuyFarm(cash_to_spend, ai_actions)
            if action_dict is not None:
                # Unwrap the action dict to determine what action the AI should take next
                # if 'Index' in action_dict.keys() and action_dict['Index'] >= len(game_state.farms):
                #     print("Stats before failure: ")
                #     print("Number of farms: %s"%(len(game_state.farms)))
                #     print("List of actions: ")
                #     print(aiGetActions(game_state.farms, ai_actions_base, debug=True))
                #     print("Predicted action:")
                #     print(aiBuyFarm(cash_to_spend, ai_actions, debug=True))

                if action_dict['Type'] == 'Purchase':
                    # Identify the type of farm we intend to purchase and amend that to the queue
                    game_state.buy_queue.append([b2.buyFarm(upgrades=tuple(action_dict['Upgrades']))])
                else:
                    # The action type is an upgrade. Identify which farm is to be upgraded, then append the action to the queue
                    game_state.buy_queue.append([b2.upgradeFarm(index=action_dict['Index'], upgrades=tuple(action_dict['Upgrades']))])
            
        # Finally, run the simulation for some time
        game_state.fastForward(target_time = min(game_state.current_time + increment_value, target_time))

    return game_state

def processGenome(genome, config, initial_state_game, target_time, increment_value = 6):
    '''
    Determine the fitness of a given genome.

    Returns:
    fitness (float): A rating of how well the genome performed
    '''

    # Form the GameState object from the initial state info
    game_state = b2.GameState(dc(initial_state_game))
    
    # From the neural network we'll use to simulate from the genome and config info
    net = neat.nn.FeedForwardNetwork.create(genome, config)

    # Run a simulation to the target time using the neural network
    game_state = simulate(net, game_state, target_time, increment_value = increment_value)

    # Use the cashGen function to assign a fitness score to the AI
    return cashGen(game_state, units_to_measure = 3, unit_type = 'Rounds', eco_threshold = 0)

def evalGenomes(genomes, config, initial_state_game, target_time, increment_value = 6):
    for genome_id, genome in genomes:
        genome.fitness = processGenome(genome, config, initial_state_game, target_time, increment_value = increment_value)
        # print("Genome %s achieved fitness %s"%(genome_id, genome.fitness))

def run(config_file, initial_state_game, target_time, increment_value=6, num_generations = 50):
    # Load configuration.
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(5))

    def eval(genomes, config):
        evalGenomes(genomes, config, initial_state_game, target_time, increment_value)
    
    # Run for up to 300 generations.
    winner = p.run(eval, num_generations)

    # Display the winning genome.
    print('\nBest genome:\n{!s}'.format(winner))

    # Show output of the most fit genome against training data.
    print('\nOutput:')
    winner_net = neat.nn.FeedForwardNetwork.create(winner, config)
    
    # How much fitness did the winning genome achieve?
    winner_fitness = processGenome(winner, config, initial_state_game, target_time, increment_value = increment_value)
    print("The winning network achieved a fitness of %s"%(winner_fitness))

    # viz.draw_net(config, winner, True)
    # viz.draw_net(config, winner, True, prune_unused=True)
    # viz.plot_stats(stats, ylog=False, view=True)
    # viz.plot_species(stats, view=True)

    return winner_net

def efficientFrontier(eco_sends):
    '''
    Given a list of eco sends, determine which ones belong to the efficient eco frontier
    
    Parameters:
    eco_sends (List[str]): A list containing names of eco sends for consideration

    Returns:
    (List[str]): A list containing names of non-dominated pure eco sends
    '''

    # First, sort the sends based on cost intensity
    eco_sends.sort(key = lambda send_name: b2.eco_send_info[send_name]['Cost Intensity'])

    # Now determine the indices that correspond to eef sends
    i = 0
    eef = [0]
    while i < len(eco_sends)-1:
        
        #Test remaining eco sends to determine which ones belong on the EEF
        slope = 0
        index = None
        for j in range(i+1,len(eco_sends)):
            test_num = b2.eco_send_info[eco_sends[j]]['Eco Intensity'] - b2.eco_send_info[eco_sends[i]]['Eco Intensity']
            test_den = b2.eco_send_info[eco_sends[j]]['Cost Intensity'] - b2.eco_send_info[eco_sends[i]]['Cost Intensity']
            test_val = test_num/test_den
            #print("Test value for index (" + str(i) + ", " + str(j) + "): " + str(test_val))
            if test_val > slope:
                slope = test_val
                index = j
                
        # When the correct index is discovered, append it to eef
        if index is not None and index > i:
            eef.append(index)
            i = index
        else:
            #It is possible we may run out of eco sends to add to the frontier, in which case...
            break
        
    return [eco_sends[ind] for ind in eef]

def ecoIntensity(intensity: float, eco_sends):
    '''
    Given a desired eco intensity and a list of non-dominated eco_sends sorted in order of increasing intensity, 
    determine the highest intensity eco send among all currently available that does not exceed the given desired eco intensity.

    The eco intensity of an eco send is defined as the eco awarded divided by the amount of time it takes to send.
    
    Parameters:
    intensity (float): The highest desired rate of eco gain (expressed in terms of eco gained per 6 seconds)
    eco_sends (List[str]): A list of non-dominated eco sends to be considered, sorted in order of increasing cost intensity

    Returns:
    eco_send (str): A string which names an eco send and corresponds to an entry in the eco_send_info dictionary
    '''
    ind = bisect_left(eco_sends, intensity, key = lambda send_name: b2.eco_send_info[send_name]['Eco Intensity']) - 1
    if ind >= 0:
        return eco_sends[ind]
    else:
        return eco_sends[0]
    
def aiGetActions(farms, arr, debug = False):
    '''
    Given a list of MonkeyFarm objects, return a list of non-dominated farm actions suitable for use by aiBuyFarm
    '''
    arr = dc(arr)

    for h in range(len(farms)):
        if debug:
            print("Considering farm %s"%(h))
        farm = farms[h]
        for i in range(3):
            # Check if the AI has the option to upgrade the ith crosspath of the given farm or not.
            # If they do, create a new farm action and append it to arr

            # Is the farm a T4 or less farm?
            if farm.upgrades[i] < 5:
                # Yes, it is!
                
                # Is it a T3 elsewhere?
                # Are BOTH the other paths upgraded?
                T3_elsewhere = False
                both_upgraded = True
                for j in range(3):
                    if j != i and farm.upgrades[j] >= 3:
                        T3_elsewhere = True
                        break
                    if j != i and farm.upgrades[j] == 0:
                        both_upgraded = False
                
                if (not T3_elsewhere) and (not both_upgraded):
                    # Build the entry and append it to AI actions_base
                    new_upgrades = dc(farm.upgrades)
                    new_upgrades[i] += 1
                    ppr = farm_incomes[tuple(new_upgrades)] - farm_incomes[tuple(farm.upgrades)] 
                    entry = {
                        'Type': 'Upgrade',
                        'Index': h,
                        'Upgrades': tuple(new_upgrades),
                        'Income': ppr,
                        'Cost': b2.farm_upgrades_costs[i][farm.upgrades[i]]
                    }
                    if debug:
                        print("Appended entry:")
                        print(entry)
                    arr.append(entry)

    arr = pruneActions(arr)
    return arr

def aiBuyFarm(cash, ai_actions, debug = False):
    '''
    Given an amount of a cash and a sorted list of non-dominated farms, purchase the most expensive farm in the list that does
    not exceed the given cash level. Returns none if none of the farms can be afforded

    Parameters:
    cash (float)
    farms_list (List[tuple]): A list of non-dominated farms identified by their upgrades (e.g. (0,1,0), (2,3,0), ...)

    Returns:
    Tuple or None
    '''

    ind = bisect_left(ai_actions, cash, key = lambda entry: entry['Cost']) - 1
    if ind >= 0:
        return ai_actions[ind]
    else:
        return None
    
def farmIncome(gs):
    '''
    Given a GameState class object, determine how much per round income the farms from that game_state object produces.
    If the GameState object has any banks, we will withdraw from those banks upon simulation end.

    Parameters:
    gs (GameState): A GameState object

    Returns:
    (float): How much money the farms will generate 
    '''

    round_income = 0
    for farm in gs.farms:
        ppr = b2.farm_payout_values[tuple(farm.upgrades)][0]*b2.farm_payout_values[tuple(farm.upgrades)][1]
        if gs.T5_exists[0] and farm.upgrades[0] == 4:
            ppr = ppr*b2.farm_globals['Banana Central Multiplier']

        round_income += ppr
        if farm.upgrades[2] == 5:
            round_income += 10000

    return round_income

def cashGen(game_state, units_to_measure = 1, unit_type = 'Rounds', eco_threshold = 0):
    '''
    Evaluates the income of a GameState object by determining the amount of cash it generates over the next number of specified rounds or seconds.
    By default the function evaluates over *rounds*.
    This function is intended to be used in conjunction with the AI features to evaluate the effectiveness of the AI.
    '''

    if game_state.eco < eco_threshold:
        return 0

    current_cash = game_state.cash
    game_state.eco_queue.append(b2.ecoSend(send_name = 'Zero'))

    if unit_type == 'Rounds':
        current_round = game_state.rounds.getRoundFromTime(game_state.current_time, get_frac_part = True)
        game_state.fastForward(target_round = current_round + units_to_measure)
    else:
        game_state.fastForward(target_time = game_state.current_time + units_to_measure)

    return max(game_state.cash - current_cash,0)

# Determine path to configuration file. This path manipulation is
# here so that the script will run successfully regardless of the
# current working directory.
local_dir = os.path.dirname(__file__)
config_path = os.path.join(local_dir, '..')
config_path = os.path.join(config_path, 'templates/config.txt')