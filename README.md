# Welcome!

Hi there! I'm redlaserbm, the main developer of the BTDB2 Eco simulator. To get started with using the code, please read through this README file! 

- To learn how to operate the code, see the examples folder.
- Want to request features for the code? Want to help out with the code? Found a bug? Don't hesitate to contact me! The most immediate way to get my attention with regards to this code is to join the b2 Popology discord server and ping me there: https://discord.gg/axHnkcVe6E

# Operating the Code

To run the code, do the following: 
1. Install python on your computer. 
2. In the terminal, do `pip install b2sim`.
3. Using an IDE like Visual Studio Code, open a new .ipynb file and type `import b2sim as b2` in the first line and hit enter.
4. You now have a file which you can use to generate simulations! Check out the tutorial files for more info on how to operate the library. 

# Code Features

1. **Simultaneous simulation of eco, farms, and alt-eco:** When given an eco send to use and some arrangement of farms and alt-eco, the simulator accurately tracks the progression of the player's cash and eco over time. The results of the simulator are nearly true to the game.
2. **Easy operation:** Simply input your initial cash and eco, the round to start on, and the purchases you intend to make and the eco flowchart you intend to follow over the course of the match. The code runs in one click and delivers results in seconds.
3. **Complete Farm support:** The simulator supports IMF Loans and Monkeyopolis. Also, the simulator supports compound purchases, such as selling into Monkey Wall Street.
4. **Advanced Optimization Potential:** The code can be used in conjuction with optimization or nonlinear root-finding methods to determine the absolute best times to makes your moves during the game. 

# Update Log
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

# Feature To-Do List

- (High priority) Expanded revenue tracking:
   - It would also be nice if the sim could track stats related to alt eco. Such stats could include revenue, expenses, long-run eco, and the aggregate revenue and expenses of each alt eco over the course of the simulation.
   - For farms in particular, I wish to implement a stat called "equivalent eco impact" which shows the amount of eco that would've earned exactly the same amount that the farm did during its lifespan within simulation time. 
- (High Priority) Improved Jeri functionality
   - The improved Jericho functionality would ideally include support for Highwayman steals, as well as support for being stolen from.
   - Although cumbersome with diminishing returns to accompany it, the computation of hero XP and hero levels would help to simplify the experience of using Jericho in the sim.
- (Medium priority) Village support:
   - Village support would help answer the question of how useful Monkey City/Monkey Town actually are.
- (Medium priority) Restructure the code:
   - There may be a way to rewrite 'processBuyQueue' so that it uses less lines of code and is easier to understand. (will explain idea here later)
- (Low priority) Robust logging when comparing different strategies
   - The idea here is this: If I have two or more game states that share the same round class and are simulated over the same time span, they are directly comparable. While a method already exists to compare multiple game states with this principle, because it does not share code with the `Game State` class method `viewCashAndEcoHistory`, it is currently inflexible with regards to updates and lacks some of the pizazz the class method has right now.
- (Low Priority) Optimization of the buy queue to prevent redundant computations
   - The code is already reasonably fast, but there are selected cases where the simulator is known to perform the same computation repeatedly when this sort of thing can be avoided.
