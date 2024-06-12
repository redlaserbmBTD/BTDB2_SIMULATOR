import pandas as pd
import matplotlib.pyplot as plt

def viewHistory(gs, dim = (12,6), display_farms = True, display_snipers = True, font_size = 12):
        '''
        Given an instance of an GameState on which a simulation has been run, graph the history of cash and eco over the course of that simulation.

        Parameters:
        gs (GameState): An instance of the GameState class whose cash and eco history we want to graph

        Returns: 
        None

        '''
        # gs.logs.append("MESSAGE FROM GameState.viewCashEcoHistory():")
        # gs.logs.append("Graphing history of cash and eco!")

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #Create a table that shows when each significant event in simulation occurs
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        event_df = pd.DataFrame(gs.event_messages)
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
        ax1.plot(gs.time_states, gs.cash_states, label = "Cash", color = color)
        ax1.tick_params(axis ='y', labelcolor = color)

        #Graphing eco
        color = 'tab:orange'
        ax2 = ax1.twinx()
        ax2.set_ylabel('Eco', color = color)
        ax2.plot(gs.time_states, gs.eco_states, label = "Eco", color = color)
        ax2.tick_params(axis ='y', labelcolor = color)

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #Mark on the graph messages in gs.event_messages
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        cash_min = min(gs.cash_states)
        eco_min = min(gs.eco_states)
        
        cash_max = max(gs.cash_states)
        eco_max = max(gs.eco_states)

        for message in gs.event_messages:

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
        gs.farm_revenues = []
        gs.farm_expenses = []
        gs.farm_profits = []
        gs.farm_eis = []
        gs.farm_starts = []
        gs.farm_ends = []

        for farm in gs.farms:
            gs.farm_revenues.append(farm.revenue)
            gs.farm_expenses.append(farm.expenses)
            gs.farm_profits.append(farm.revenue - farm.expenses)

            #Also, measure the equivalent eco impact of the farm
            start_time = max(farm.init_purchase_time, gs.simulation_start_time)
            if farm.sell_time == None:
                end_time = gs.current_time
            else:
                end_time = farm.sell_time

            gs.farm_starts.append(start_time)
            gs.farm_ends.append(end_time)

            gs.farm_eis.append(6*farm.revenue/(end_time - start_time))

        # dictionary of lists 
        if display_farms and len(gs.farms) > 0:
            farm_table = {
                'Farm Index': [int(i) for i in range(len(gs.farms))], 
                'Revenue': gs.farm_revenues, 
                'Expenses': gs.farm_expenses, 
                'Profit': gs.farm_profits, 
                'Eco Impact': gs.farm_eis, 
                'Start Time': gs.farm_starts, 
                'End Time': gs.farm_ends
            } 
            df = pd.DataFrame(farm_table)
            df = df.set_index('Farm Index')
            df = df.round(0)
            display(df)

        
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #Create a table that displays the revenue/expenses of each sniper farm
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        gs.sniper_revenues = []
        gs.sniper_expenses = []
        gs.sniper_profits = []
        gs.sniper_starts = []
        gs.sniper_ends = []

        for sniper in gs.supply_drops:
            gs.sniper_revenues.append(sniper.revenue)
            gs.sniper_expenses.append(sniper.expenses)
            gs.sniper_profits.append(sniper.revenue - sniper.expenses)

            start_time = max(sniper.purchase_time, gs.simulation_start_time)
            if sniper.sell_time == None:
                end_time = gs.current_time
            else:
                end_time = sniper.sell_time

            gs.sniper_starts.append(start_time)
            gs.sniper_ends.append(end_time)
        
        # dictionary of lists 
        if display_snipers and len(gs.supply_drops) > 0:
            sniper_table = {
                'Sniper Index': [int(i) for i in range(len(gs.supply_drops))], 
                'Revenue': gs.sniper_revenues, 
                'Expenses': gs.sniper_expenses, 
                'Profit': gs.sniper_profits,
                'Start Time': gs.sniper_starts, 
                'End Time': gs.sniper_ends
            } 
            df = pd.DataFrame(sniper_table)
            df = df.set_index('Sniper Index')
            df = df.round(0)
            display(df)

        # gs.logs.append("Successfully generated graph! \n")