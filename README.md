# Overview

The `b2sim` Python library is an extensive feature-rich library for simulating flowcharts within battles 2. Simulating essential aspects of battles 2's income sources with virtually 100% accuracy, the library is a must-use tool for optimizing eco'ing and farming with any flowchart. Results from the simulator can be used to better inform practical decisions made during games, improving player game sense and leading to more optimal play. The code is relatively easy to use and does not require prior coding experience to effectively operate.

- To install the code, first download Python on your machine, and then in the terminal type `pip install b2sim` and hit 'Enter'.
- To learn how to operate the code, see the examples folder in this GitHub repo. It contains numerous examples with code explained in plain English.
- Want to request features for the code? Want to help out with the code? Found a bug? Don't hesitate to contact me! The most immediate way to get my attention with regards to this code is to join the b2 Popology discord server and ping me there: https://discord.gg/axHnkcVe6E
- Potential collaborators interested with helping out with the code should view the "Feature Requests" section below for more info on tasks that need to be completed.

# Running the Code

For noobs:
1. Install python on your computer here: https://www.anaconda.com/download/
2. Open the anaconda prompt and type `pip install b2sim`.
3. Your installation of anaconda came with a program called "Jupyter Notebook", which allows you to create and edit .ipynb files which you will use to operate the code. Open Jupyter, and create a new .ipynb file wherever you wish on your computer.
4. In the first cell of this new .ipynb file you've created, type `import b2sim as b2` and hit enter. 
5. Congratulations, you now have a file which you can use to generate simulations! Check out the tutorial files in this repo (examples folder) for more info on how to operate the library.

For experienced coders:
1. Type `pip install b2sim` in the terminal to download.
2. Check out the tutorial files in this repo (examples folder) for more info on how to operate the library.

Alternative installation instructions:
If for whatever reason pip installation does not work, try the following:
1. Clone this GitHub repository onto your computer (using a program like GitHub Desktop)
2. Navigate to where you cloned the repository in the terminal, and then run the command `python3 setup.py install --user`

# Code Features

1. **Simultaneous simulation of eco, farms, and alt-eco:** When given an eco send to use and some arrangement of farms and alt-eco, the simulator accurately tracks the progression of the player's cash and eco over time. The results of the simulator are nearly true to the game.
2. **Easy operation:** Simply input your initial cash and eco, the round to start on, and the purchases you intend to make and the eco flowchart you intend to follow over the course of the match. The code runs in one click and delivers results in seconds.
3. **Complete Farm support:** The simulator supports IMF Loans and Monkeyopolis. Also, the simulator supports compound purchases, such as selling into Monkey Wall Street.
4. **Advanced Optimization Potential:** The code can be used in conjuction with optimization or nonlinear root-finding methods to determine the absolute best times to makes your moves during the game. 

# Update Log
- (July 10, 2023 - v1.0.8)
   - Initializing boat farms is now also done with a list structure just like with regular farms.
   - Changed round lengths in the spreadsheet. Natural round lengths were inferred by a test between spoonoil and ninjayas but the old numbers led to underestimates. The new numbers may still underestimate actual natural round lengths but are closer to the truth than before.
- (July 4, 2023 - v1.0.7)
   - Fixed various bugs which caused the simulator to behave incorrectly when fail-safes were triggered. Such issues were related to when the eco sim tried to change eco sends as a consequence of a break condition (such as `max_eco_amount`) on the current send being satisfied.
   - Updated display for graphs. The legend shows (approximated to the nearest tenth) when each action is carried out in the simulation.
- (July 2, 2023 - v1.0.6)
   - Fixed an issue which effectively caused the attack queue size to be 5 instead of 6.
   - New action `sellAllFarms` for rapidly selling all farms.
- (July 2, 2023 - v1.0.5)
   - Improved support for eco numbers. It is no longer mandatory when specifying eco sends in the eco queue to specify a time for the player to start triggering that send. Note that if you place a send in the queue without a time specified, the previous send must have some sort of break condition (like `max_eco_amount` or `max_send_amount`) specified which compels the simulator to switch sends, otherwise the next send in the queue will never be triggered.
- (July 1, 2023 - v1.0.4)
   - Fixed an issue which caused the attack queue (which concerns the queue of bloons sent to your opponent) to sometimes fail to remove sends from the queue that already finished sending, resulting in the simulator computing incorrect eco amounts during simulation.
   - You can now change the text size of the legend in the `viewCashEcoHistory` by using the `text_size` argument.
- (July 1, 2023 - v1.0.3)
   - Added back support for *eco impact*. Whenever a farm is used in a simulation, the simulator computes the equivalent amount of eco that would've made the exact same money as the farm during its lifetime in the simulation. Thus, a farm that is on screen for 6 seconds and generates 100 dollars would have an eco impact of 100.
   - Rectified an error in the build which caused installing from pip to not work.
   - The revenue and expenses of a given farm is now stored in the `MonkeyFarm` class. Previously, revenue and expense tracking were handled by the `GameState` class.
   - Selling farms no longer actually removes the `MonkeyFarm` object from the simulator. Instead, the farm's sell time is marked, and the simulator whenever processing payments for a farm checks whether the farm has been sold or not first. This behavior makes it easier to write code concerning revenue/expense tracking of farms.
- (June 29, 2023 - v1.0.1)
   - The python code is now available to install on pip! Just do `pip install b2sim=1.0.1` to install the code on your computer and run it!
   - If a simulation involves farms, the `GameState` class will track the revenue and expenses of each farm over the course of the simulation.
   - NOTE: The function for computing equivalentEcoImpact has been phased out. It will be replaced with a better function in a future update. 
- (June 26, 2023 - v0.9.11)
   - Better handling of global values. To improve the ease at which the sim can be updated when balance changes come around, hard-coded values are now defined in `info.py` and then imported into `main.py`.
   - Updated Druid farms. Because of the recent changes to druid, it is no longer necessary to treat the money-making active ability of Spirit of the Forest as an "optional" action.
   - Added support for maximum eco amounts. This new feature allows you to specify to the simulator to switch to the next eco send after reaching a specified amount of eco.
   - Slightly improved `ecoQueueCorrection` method. The new method (again) follows the philosophy of only modifying the eco queue on an "as-needed" basis.
   - Fixed a bug which caused boat farms to not work at all.
- (June 23, 2023 - v0.9.10)
   - Added support for eco modifiers and eco numbers. This new update *changes* how the eco queue works. Now, instead of putting tuples into the eco queue, you use the function `ecoSend` from `actions.py`. This new function lets you specify modifiers for the send you are placing in the queue, and also has functionality to force the simulator to switch to the next item in the queue after sending some number of sets. This functionality is generally useful for determining how to eco while still affording your hero + essential defense on R1, or for mapping out the impact of rushing your opponent.
   - The "examples" folder contains two tutorial files on how to operate the simulator. The purpose of these files is to improve presentability of the code and encourage usage by top level players.
- (June 21, 2023 - v0.9.9)
   - Added support for Jericho money stealing. Note that it is the player's responsbility to correctly indicate the amount that Jericho steals. The code operates under the assumption that Jericho's steal is never blocked.
   - Fixed an issue which made it so that files which imported the library had to be placed in a certain location relative to the repo location in order for importing to work correctly.
- (June 19, 2023 - v0.9.8)
   - The code now simulates eco in a way faithful to the mechanics of battles 2. Previously, the simulator assumed eco worked as a continuous flow of income generation, which led the simulator to underestimate eco relative to actual game scenarios. In this new update, the class variable `attack_queue` tracks bloons that have been sent by the player. The simulator tracks the progression of eco between payments by repeatedly checking the eco queue at key times, during each check removing bloon sends that have already been sent and adding a new send to the queue provided that the queue is not full and the player has enough money to do so.
- (June 19, 2023 - v0.9.7)
   - Some code has been reorganized in the `GameState` class definition. Some functionality of the `advanceGameState` method has been moved to new helper methods `computePayoutSchedule` and `processBuyQueue`. It should be easier now for potential collaborators to gain a high-level understanding of how the code performs simulation.
   - The code now supports simulation all rounds 0 - 50. The data for natural send lengths from rounds 1-30 is inferred from a test done by spoonoil and ninjayas back in October 2022. The data for natural send lengths for rounds 31-50 is due to vic++. 
- (June 19, 2023 - v0.9.6)
   - `main.ipynb` has been phased out. The "meat" of the code is now contained in `main.py`. Some portions of code previously in `main.py` have been moved to other files. Namely:
        - `farm_init.py` contains info on eco sends and farms. It also contains a function which automatically computes the sellback value of farms given their upgrade costs, which will save time in the future when NK inevitably rebalances farms.
        - `actions.py` contains a list of actions which may be fed into the buy queue when running the eco simulator. See the section "Operating the Code" for more details on this.
   - Changes to farm data and round length data have been made to reflect the upcoming version 2.0 changes to the game. Eco changes have not been made because I anticipate modifying how the simulator handles eco so that it is more faithful to in-game behavior.
- (June 16, 2023 - v0.9.5)
   - Remedied an issue where the eco simualator would sometimes ignore items in the buy queue for several seconds. The eco simulator now checks the buy queue at the minimum every `interval` seconds.
- (June 1, 2023 - v0.9.4)
   - Various updates to keep the game in line with v1.10.4 of the game (vTri)
- (May 16, 2023 - v0.9.3)
   - New syntax for initializing `Rounds()` class which allows the user specify rounds with various levels of stall throughout the game simulation
   - Fixed an issue which would cause the simulation to incorrectly compute the money gained from selling Elite Sniper and Spirit of the Forest
   - The simulation now prints logs messages of importance to the player when a safe-guard is triggered.
   - When the code terminates the buy queue as a consequence of attempting to perform a disallowed action (such as buying multiple T5's), the code now abandons running the buy queue entirely, speeding up simulation time in this edge case.
- (May 12, 2023 - v0.9.2) 
   - Graphs from `GameState.viewCashEcoHistory()` are now more informative.
   - `GameState.viewCashEcoHistory(dim=(w,h))` lets you set the width and height of the graphs.
   - Fixed a bug which would cause the code to get stuck in an infinite loop if `GameState.fastForward()` if the argument interval was set to a small number.
   - `GameState.fastForward()` now by default uses `interval = 0.1`. This will lead to sharper graphs and surprisngly does not appear to slow down the code much.
- (May 11, 2023 - v0.9.1) 
   - Added druid farm support. Currently untested!

# Feature Requests
- (High Priority) Reorganize `GameState.processBuyQueue()` so that the process of adding actions to the simulator is more straightforward. 
- (High Priority) More actions in `actions.py` to expand functionality and improve ease of use, including:
   - Selling all Supply Drops, Selling all Druid Farms, Selling all Boat Farms
   - Selling into a farm upgrade
   - Withdrawing from all banks at once
   - Buying, selling, and using overclock (on farms)
- (High Priority) Expanded revenue tracking:
   - It would also be nice if the sim could track stats related to alt eco. Such stats could include revenue, expenses, long-run eco, and the aggregate revenue and expenses of each alt eco over the course of the simulation.
   - In order for players to understand the `eco impact` statistic, display the farm's start and end of availability during the simulation.
- (High Priority) Change the formatting for storing farms and boat farms:
   - In a previous update, the behavior of farm selling was changed so that, from the perspective of the simulator, the farm is not sold, but rather "disabled". The `GameState` class continues to store the farms but does not compute their payments or award them.
   - This new behavior circumvents an issue in early builds that used a list structure to store farms where a selling one farm could cause other farms' identifying index to shift, essentially making it impossible to implement support for compound transactions.
   - Because of this, farms can now be stored in a simple list structure.
   - Naturally, when revenue/expense tracking support is also implemented for boat farms, we will in the same way want to change the data structure for storing them to a list.
- (Medium priority) Village support:
   - Village support would help answer the question of how useful Monkey City/Monkey Town actually are.
- (Medium priority) Restructure the code:
   - There may be a way to rewrite 'processBuyQueue' so that it uses less lines of code and is easier to understand. (will explain idea here later)
- (Low priority) Robust logging when comparing different strategies
   - The idea here is this: If I have two or more game states that share the same round class and are simulated over the same time span, they are directly comparable. While a method already exists to compare multiple game states with this principle, because it does not share code with the `Game State` class method `viewCashAndEcoHistory`, it is currently inflexible with regards to updates and lacks some of the pizazz the class method has right now.
- (Low Priority) Optimization of the buy queue to prevent redundant computations
   - The code is already reasonably fast, but there are selected cases where the simulator is known to perform the same computation repeatedly when this sort of thing can be avoided.
