# %%
import numpy as np

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

eco_send_info = {
    'Zero': (0,0),
    'Grouped Reds': (150,6.75),
    'Spaced Blues': (60,3.2),
    'Grouped Blues': (240,10),
    'Spaced Greens': (93.96,4.698),
    'Grouped Greens': (525,21),
    'Spaced Yellows': (125.28,6.264),
    'Grouped Yellows': (1000,40),
    'Spaced Pinks': (186.667,9.333),
    'Grouped Pinks': (1800,69),
    'Spaced Whites': (214.2,10.71),
    'Grouped Whites': (1300,52),
    'Spaced Blacks': (264,12.8),
    'Grouped Blacks': (1406.25,56.25),
    'Spaced Purples': (262.5,12.375),
    'Grouped Purples': (3943.35,99.441),
    'Spaced Zebras': (600,27),
    'Grouped Zebras': (3000,87.5),
    'Spaced Leads': (180,8.4),
    'Grouped Leads': (1500,45),
    'Spaced Rainbows': (1199.8,51.42),
    'Grouped Rainbows': (3750,90),
    'Spaced Ceramics': (1200,45),
    'Grouped Ceramics': (10000,45)
}

eco_send_availability = {
    'Zero': (0,30),
    'Grouped Reds': (1,10),
    'Spaced Blues': (1,2),
    'Grouped Blues': (3,10),
    'Spaced Greens': (2,4),
    'Grouped Greens': (5,16),
    'Spaced Yellows': (3,6),
    'Grouped Yellows': (7,19),
    'Spaced Pinks': (4,8),
    'Grouped Pinks': (9,30),
    'Spaced Whites': (5,30),
    'Grouped Whites': (10,21),
    'Spaced Blacks': (6,9),
    'Grouped Blacks': (10,30),
    'Spaced Purples': (8,10),
    'Grouped Purples': (11,30),
    'Spaced Zebras': (9,10),
    'Grouped Zebras': (11,30),
    'Spaced Leads': (10,11),
    'Grouped Leads': (12,30),
    'Spaced Rainbows': (12,12),
    'Grouped Rainbows': (13,30),
    'Spaced Ceramics': (13,15),
    'Grouped Ceramics': (16,30)
    
}
