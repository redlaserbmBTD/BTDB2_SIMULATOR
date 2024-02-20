# %%
import csv
import os
from copy import deepcopy as dc

# %%

# These dictionaries contain all the "hard-coded" values that the simulator uses. I could've put this all in one dictionary but decided against it to improve presentability.

farm_payout_values = {
    
    #Base Farm
    (0,0,0): (40,3),
    
    ####################
    #UNCROSSPATHED FARMS
    ####################
    
    #Top path
    (1,0,0): (40,5),
    (2,0,0): (40,7),
    (3,0,0): (40,16),
    (4,0,0): (600,5),
    (5,0,0): (2800,5),
    
    #Middle path
    (0,1,0): (40,3),
    (0,2,0): (50,3),
    (0,3,0): (50,3),
    (0,4,0): (50,3),
    (0,5,0): (50,3),
    
    #Bottom path
    (0,0,1): (40,3),
    (0,0,2): (40,3),
    (0,0,3): (40,14),
    (0,0,4): (160,14),
    (0,0,5): (160,14),
    
    ######################
    #TOP CROSSPATHED FARMS
    ######################
    
    #Middle path
    (1,1,0): (40,5),
    (1,2,0): (50,5),
    (1,3,0): (50,5),
    (1,4,0): (50,5),
    (1,5,0): (50,5),
    
    (2,1,0): (40,7),
    (2,2,0): (50,7),
    (2,3,0): (50,7),
    (2,4,0): (50,7),
    (2,5,0): (50,7),
    
    #Bottom path
    (1,0,1): (40,5),
    (1,0,2): (40,5),
    (1,0,3): (40,16),
    (1,0,4): (160,16),
    (1,0,5): (160,16),
    
    (2,0,1): (40,7),
    (2,0,2): (40,7),
    (2,0,3): (40,18),
    (2,0,4): (160,18),
    (2,0,5): (160,18),
    
    #########################
    #MIDDLE CROSSPATHED FARMS
    #########################
    
    #Top path
    (3,1,0): (40,16),
    (4,1,0): (600,5),
    (5,1,0): (2800,5),
    
    (3,2,0): (50,16),
    (4,2,0): (750,5),
    (5,2,0): (3500,5),
    
    #Bottom path
    (0,1,1): (40,3),
    (0,1,2): (40,3),
    (0,1,3): (40,14),
    (0,1,4): (160,14),
    (0,1,5): (160,14),
    
    (0,2,1): (50,3),
    (0,2,2): (50,3),
    (0,2,3): (50,14),
    (0,2,4): (200,14),
    (0,2,5): (200,14),
    
    #########################
    #BOTTOM CROSSPATHED FARMS
    #########################
    
    #This is admittedly redundant but I do this beacuse it makes the code easier to read/use
    
    #Top path
    (3,0,1): (40,16),
    (4,0,1): (600,5),
    (5,0,1): (2800,5),
    
    (3,0,2): (40,16),
    (4,0,2): (600,5),
    (5,0,2): (2800,5),
    
    #Middle path
    (0,3,1): (50,3),
    (0,4,1): (50,3),
    (0,5,1): (50,3),

    (0,3,2): (50,3),
    (0,4,2): (50,3),
    (0,5,2): (50,3),
    
}

game_globals = {
    'Eco Delay': 0.15, #The delay between eco sends, in seconds, assuming the attack queue is not full and the player has enough cash to send eco.
    'Fortified Multiplier': 2.0,
    'Camoflauge Multiplier': 2.0,
    'Regrow Multiplier': 1.6,
    'Regrow Round': 8,
    'Camoflauge Round': 12,
    'Fortified Round': 18,
    'Sellback Value': 0.7,
    'Max Queue Length': 6 #The maximum number of bloon sends that can exist in the attack queue at any given time.
}

farm_globals = {
    'Farm Cost': 1000,
    'Farm Upgrade Costs': [[550,550,2750,16000,66000],[200,700,4600,8000,45000],[250,200,2800,13000,46000]],
    'Farm Bank Capacity': [0,0,0,14000,20000,30000],
    'IMF Loan Amount': 20000,
    'IMF Initial Cooldown': 20,
    'IMF Usage Cooldown': 90,
    'Monkey Wall Street Bonus': 10000,
    'Monkeynomics Payout': 20000,
    'Monkeynomics Initial Cooldown': 25,
    'Monkeynomics Usage Cooldown': 50,
    'Banana Central Multiplier': 1.25,
    'Start of Round Bank Payment': 550,
    'Start of Round Bank Multiplier': 1.2
}

# This is admittedly not the cleanest way of organizing this info but
# this way was the most compatible with older versions of the code
boat_globals = {
    'Merchantmen Cost': 2800,
    'Upgrade Costs': [5400, 19000], # Upgrade costs of favored trades and Trade Empire respectively
    'Payout Values': [300, 1000, 3000], # Payout values of Merchantmen, Favored Trades, and Trade Empire respectively.
    'Sellback Values': [1960, 6560, 21760] # Sellback amounts of Merchantment, Favored Trdes, and Trade Empire respectively.
}

druid_globals = {
    'Druid Farm Cost': 4675,
    'Druid Farm Initial Cooldown': 15,
    'Druid Farm Usage Cooldown': 40,
    'Druid Farm Payout': 1000,
    'Spirit of the Forest Upgrade Cost': 35000,
    'Spirit of the Forest Bonus': 3000
}

sniper_globals = {
    'Supply Drop Cost': 9550,
    'Supply Drop Initial Cooldown': 15,
    'Supply Drop Usage Cooldown': 40,
    'Supply Drop Payout': 2000,
    'Elite Sniper Upgrade Cost': 14000,
    'Elite Sniper Payout': 5000
}

heli_globals = {
    'Heli Farm Cost': 12150,
    'Heli Farm Initial Cooldown': 20,
    'Heli Farm Usage Cooldown': 60,
    'Heli Farm Payout': 4000,
    'Special Poperations Upgrade Cost': 30000,
    'Special Poperations Payout': 8000
}

hero_globals = {
    'Jericho Number of Steals': 10,
    'Jericho Steal Interval': 1
}

engi_globals = {
    'Overclock Cost': 15350,
    'Ultraboost Upgrade Cost': 100000,
    'Overclock Usage Cooldown': 45, #There is no initial cooldown for the Overclock active
    'Ultraboost Usage Cooldown': 20,
    'Overclock Payout Modifier': 1.5
}

# %%

boat_upgrades_costs = boat_globals['Upgrade Costs']
boat_payout_values = boat_globals['Payout Values']
boat_sell_values = boat_globals['Sellback Values'] 

farm_upgrades_costs = farm_globals['Farm Upgrade Costs']
farm_bank_capacity = farm_globals['Farm Bank Capacity']
farm_cost = farm_globals['Farm Cost']
sellback_value = game_globals['Sellback Value']

def computeSellbackValues(farm_upgrades_costs, farm_cost):
    farm_sellback_values = {}
    farm_sellback_values[tuple([0,0,0])] = farm_cost  

    #####################
    # UNCROSSPATHED FARMS
    #####################

    for i in range(3):
        money_spent = farm_cost
        for j in range(5):
            money_spent += farm_upgrades_costs[i][j]

            upgrades_of_interest = [0,0,0]
            upgrades_of_interest[i] = j+1

            farm_sellback_values[tuple(upgrades_of_interest)] = money_spent

    ###################
    # CROSSPATHED FARMS
    ###################

    # We start with top path farms.
    for i in [1,2]:
        #Determines whether we are working with middle or bottom crosspath
        crosspath_money_spent = 0
        for j in range(2):
            #Determines whether we are working a full or partial crosspath
            crosspath_money_spent += farm_upgrades_costs[i][j]
            for k in range(1,6):
                #Iterates through the different tiers
                upgrades_of_interest = [k,0,0]
                upgrades_of_interest[i] = j+1
                farm_sellback_values[tuple(upgrades_of_interest)] = farm_sellback_values[(k,0,0)] + crosspath_money_spent

    #Next on our list is the middle path farms.

    for i in [0,2]:
        #Determines whether we are working with top or bottom crosspath
        crosspath_money_spent = 0
        for j in range(2):
            #Determines whether we are working a full or partial crosspath
            crosspath_money_spent += farm_upgrades_costs[i][j]
            for k in range(1,6):
                #Iterates through the different tiers
                if i != 0 or k >= 3:
                    upgrades_of_interest = [0,k,0]
                    upgrades_of_interest[i] = j+1
                    farm_sellback_values[tuple(upgrades_of_interest)] = farm_sellback_values[(0,k,0)] + crosspath_money_spent
    
    #Finally, we have bottom path farms
    for i in [0,1]:
        #Determines whether we are working with top or middle crosspath
        crosspath_money_spent = 0
        for j in range(2):
            #Determines whether we are working a full or partial crosspath
            crosspath_money_spent += farm_upgrades_costs[i][j]
            for k in range(3,6):
                #Iterates through the different tiers
                upgrades_of_interest = [0,0,k]
                upgrades_of_interest[i] = j+1
                farm_sellback_values[tuple(upgrades_of_interest)] = farm_sellback_values[(0,0,k)] + crosspath_money_spent

    farm_total_cost_values = dc(farm_sellback_values)

    for key in farm_sellback_values:
        if key[2] >= 2:
            farm_sellback_values[key] = (sellback_value+0.1)*farm_sellback_values[key]
        else:
            farm_sellback_values[key] = sellback_value*farm_sellback_values[key]

    return farm_total_cost_values, farm_sellback_values

farm_total_cost_values, farm_sellback_values = computeSellbackValues(farm_upgrades_costs, farm_cost)
farm_total_cost_values[(0,0,0)] = farm_cost

# %%

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, "../templates/eco_send_info.csv")

eco_send_info = {}

def boolConvert(word):
    if word == 'TRUE':
        return True
    elif word == 'FALSE':
        return False
    else:
        return None

with open(filename, newline='') as csvfile:
    first_row = True
    rows = csv.reader(csvfile)
    for row in rows:
        if first_row:
            first_row = False
        else:
            eco_send_info[row[0]] = {
                'Price': float(row[1]),
                'Eco': float(row[2]),
                'Start Round': int(row[3]),
                'End Round': int(row[4]),
                'Send Duration': float(row[5]),
                'Fortified': boolConvert(row[6]),
                'Camoflauge': boolConvert(row[7]),
                'Regrow': boolConvert(row[8]),
                'MOAB Class': boolConvert(row[9]),
                
                # Additional Parameters for the AI
                'Eco Intensity': float(row[2])/float(row[5]) if float(row[5]) > 0 else 0,
                'Cost Intensity': float(row[1])/float(row[5]) if float(row[5]) > 0 else 0
            }

# %%


