import neat
import b2sim.analysis.visualize as viz
from b2sim.analysis.graphs import viewHistory
import b2sim.engine as b2
from copy import deepcopy as dc
from bisect import bisect_left
import multiprocessing
import os
import math

def processGenome(genome, config, initial_state_game, target_time, increment_value = 1, show_results = False):
    '''
    Determine the fitness of a given genome.

    Returns:
    fitness (float): A rating of how well the genome performed
    '''

    game_state = b2.GameState(dc(initial_state_game))
    # For now, we can place this function here, but only for now...
    

    net = neat.nn.FeedForwardNetwork.create(genome, config)

    fitness_value = 0
    capture_start = False
    capture_end = False

    while game_state.current_time < target_time:
        # Pass the current game info through the genome, giving it the chance to process and spit out an output
        output = net.activate((game_state.cash, game_state.eco, game_state.current_time, farmIncome(game_state)))
        eco_intensity, buy_farms = 20*output[0],output[1]

        # if show_results:
        #     print(output[0],output[1],output[2])

        # What eco send should we use next?
        available_sends = efficientFrontier(game_state.available_sends)
        eco_send = ecoIntensity(eco_intensity, available_sends)
        if game_state.send_name != eco_send:
            game_state.eco_queue.append(b2.ecoSend(send_name = eco_send))

        # How much money should we save?
        # game_state.save += amount_to_save

        # Determine if we should purchase farms or not.
        if buy_farms >= 0.9:
            cash_to_spend = game_state.cash*buy_farms
            upgrade_tuple = aiBuyFarm(cash_to_spend, ai_farms_list)
            if upgrade_tuple is not None:
                game_state.buy_queue.append([b2.buyFarm(upgrades=upgrade_tuple)])

            # Reset the save counter
            # game_state.save = 0
            
        # Finally, run the simulation for some time
        game_state.fastForward(target_time = min(game_state.current_time + increment_value, target_time))

    # We want to rate how good the income config for the AI is. Run the simulation for one further round and record the change in cash
    current_cash = game_state.cash
    current_eco = game_state.eco

    if current_eco < 1200:
        return 0
    
    current_round = game_state.rounds.getRoundFromTime(game_state.current_time, get_frac_part = True)
    game_state.fastForward(target_round = current_round + 3)
    if show_results:
        viewHistory(game_state)
        print("Listing all farms: ")
        for farm in game_state.farms:
            print(farm.upgrades)

    return game_state.cash - current_cash 

def evalGenomes(genomes, config, initial_state_game, target_time, increment_value = 30):
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
    pe = neat.ThreadedEvaluator(4, eval)
    winner = p.run(eval, num_generations)

    # Display the winning genome.
    print('\nBest genome:\n{!s}'.format(winner))

    # Show output of the most fit genome against training data.
    print('\nOutput:')
    winner_net = neat.nn.FeedForwardNetwork.create(winner, config)
    
    # How much fitness did the winning genome achieve?
    winner_fitness = processGenome(winner, config, initial_state_game, target_time, increment_value = increment_value, show_results = True)
    print("The winning network achieved a fitness of %s"%(winner_fitness))

    # viz.draw_net(config, winner, True)
    viz.draw_net(config, winner, True, prune_unused=True)
    # viz.plot_stats(stats, ylog=False, view=True)
    # viz.plot_species(stats, view=True)

    p = neat.Checkpointer.restore_checkpoint('neat-checkpoint-4')
    p.run(eval, max(1,int(num_generations/10)))

def pruneFarms(farms_list):
    '''
    Given a list of farms, determine which farms are dominated and remove them to return to a list of non-dominated farms.
    A farm is considered dominated if there exists a cheaper farm that pays the same or greater.
    This function is intended to help the AI make decisions on what farms to purchase

    Parameters:
    farms_list (List[tuple]): A list of farms identified by their upgrades (e.g. (0,1,0), (2,3,0), ...)

    Returns:
    List[tuple]: A list of nondominated farms
    '''

    farm_info = []
    for key in farms_list:
        if key[1] < 3:
            ppr = b2.farm_payout_values[key][0]*b2.farm_payout_values[key][1]
            if key[2] == 5:
                ppr += 10000
            farm_info.append((key,b2.farm_total_cost_values[key],ppr))
    farm_info.sort(key=lambda x: x[1])

    i = 0
    payout_to_beat = 0
    while i < len(farm_info):
        if farm_info[i][2] <= payout_to_beat:
            farm_info.pop(i)
        else:
            payout_to_beat = farm_info[i][2]
            i += 1

    return [farm_info[i][0] for i in range(len(farm_info))]

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

def aiBuyFarm(cash, farms_list):
    '''
    Given an amount of a cash and a sorted list of non-dominated farms, purchase the most expensive farm in the list that does
    not exceed the given cash level. Returns none if none of the farms can be afforded

    Parameters:
    cash (float)
    farms_list (List[tuple]): A list of non-dominated farms identified by their upgrades (e.g. (0,1,0), (2,3,0), ...)

    Returns:
    Tuple or None
    '''

    ind = bisect_left(farms_list, cash, key = lambda upgrades: b2.farm_total_cost_values[upgrades]) - 1
    if ind >= 0:
        return farms_list[ind]
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

ai_farms_list = pruneFarms(b2.farm_total_cost_values.keys())
# Determine path to configuration file. This path manipulation is
# here so that the script will run successfully regardless of the
# current working directory.
local_dir = os.path.dirname(__file__)
config_path = os.path.join(local_dir, '..')
config_path = os.path.join(config_path, 'templates/config.txt')