# %%
import numpy as np
import pandas as pd

# %%
farm_upgrades_costs = [[550,550,2600,16000,66000],[200,700,5100,7500,45000],[250,200,2800,13000,46000]]
farm_bank_capacity = [0,0,0,14000,20000,30000]
farm_cost = 1000
sellback_value = 0.7

# %%
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

    for key in farm_sellback_values:
        if key[2] >= 2:
            farm_sellback_values[key] = (sellback_value+0.1)*farm_sellback_values[key]
        else:
            farm_sellback_values[key] = sellback_value*farm_sellback_values[key]

    return farm_sellback_values

farm_sellback_values = computeSellbackValues(farm_upgrades_costs, farm_cost)

# %%
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
    (1,1,0): (40,5),
    (2,1,0): (40,7),
    (3,1,0): (40,16),
    (4,1,0): (600,5),
    (5,1,0): (2800,5),
    
    (1,2,0): (50,5),
    (2,2,0): (50,7),
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
    (1,0,1): (40,5),
    (2,0,1): (40,7),
    (3,0,1): (40,16),
    (4,0,1): (600,5),
    (5,0,1): (2800,5),
    
    (1,0,2): (40,5),
    (2,0,2): (40,7),
    (3,0,2): (40,16),
    (4,0,2): (600,5),
    (5,0,2): (2800,5),
    
    #Middle path
    (0,1,1): (40,3),
    (0,2,1): (50,3),
    (0,3,1): (50,3),
    (0,4,1): (50,3),
    (0,5,1): (50,3),
    
    (0,1,2): (40,3),
    (0,2,2): (50,3),
    (0,3,2): (50,3),
    (0,4,2): (50,3),
    (0,5,2): (50,3),
    
}

# %%

eco_send_table = pd.read_csv("b2sim/eco_send_info.csv")
eco_send_info = {}

for index, row in eco_send_table.iterrows():
    eco_send_info[row['send_name']] = {
        'Price': row['price'],
        'Eco': row['eco'],
        'Start Round': row['start_round'],
        'End Round': row['end_round'],
        'Send Duration': row['send_duration']
    }

# %%


