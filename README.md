# Welcome!

Hi there! I'm redlaserbm, the main developer of the BTDB2 Eco simulator. To get started with using the code, please read through this README file! 

- To learn more about how the code works, see the documentation file at documentation/documentation.pdf
- To operate the code, see the section on operating the code.
- Want to request features for the code? Want to help out with the code? Found a bug? Don't hesitate to contact me! The most immediate way to get my attention with regards to this code is to join the B2 Popology discord server and ping me there: https://discord.gg/axHnkcVe6E

# Operating the Code

Users unfamiliar with coding who just need essential functionality should use the lightweight version of this simulator on spoonoil's website https://b2.lol. Newbies unfamiliar with coding who nonetheless want to operate the back-end code should follow the steps below to get the code up and running:
1. Download the latest Anaconda distribution to your computer https://www.anaconda.com/download/ The Anaconda distribution contains a Python "environment" which allows you to run Python code on your computer
2. Use GitHub Desktop to clone the repository to your desktop. 
3. One of the programs bundled with the Anaconda distribution is jupyter notebook. Launch jupyter notebook, navigate to where you cloned the repository, and open examples.ipynb
4. You are now ready to operate the code!

## Running a simulation in code

Check out the "examples" folder for tutorial files on how to run the code!

## Advanced Sim Usage

### Custom Round Times

When using the sim with a flat stall factor applied to all rounds, the sim may tend to undershoot the duration of earlier rounds and overshoot the duration of later ones. There are two ways to work around this:
1. Set different stall factors for different points in the game
2. Set round times manually.

Method 1 is quick and dirty, while method 2 is slow but precise. To do method 1, initialize the rounds like so

```python
Rounds([(0,0),(6,0.5),(11,0.3)])
```
Here, the rounds class is being initialized with a list of tuples, and each tuple `(round,stall_factor)` instructs the code to change the stall factor to `stall_factor` after reaching round `round`.

To do method 2, after initializing the Rounds class (say as `rounds = Rounds(0.0)`, modify the list `rounds.round_starts`. The ith index of this list determines what time round i begins on.

# Code Features

1. **Simultaneous simulation of eco, farms, and alt-eco:** When given an eco send to use and some arrangement of farms and alt-eco, the simulator accurately tracks the progression of the player's cash and eco over time. The results of the simulator are nearly true to the game.
2. **Easy operation:** Simply input your initial cash and eco, the round to start on, and the purchases you intend to make and the eco flowchart you intend to follow over the course of the match. The code runs in one click and delivers results in seconds.
3. **Complete Farm support:** The simulator supports IMF Loans and Monkeyopolis. Also, the simulator supports compound purchases, such as selling into Monkey Wall Street.
4. **Strategy Comparison:** You can compare multiple different strategies, see how cash and eco progresses over time for each one, and decide what strategy you like better with the compareStrategies() function.
5. **Advanced Optimization Potential:** The code's fast run time means that it operates well when used in black-box optimization problems.

# Update Log
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

- (High Priority) Heli alt-eco
- (High Priority) Improved Jeri functionality
   - The improved Jericho functionality would ideally include support for Highwayman steals, as well as support for being stolen from.
   - Although cumbersome with diminishing returns to accompany it, the computation of hero XP and hero levels would help to simplify the experience of using Jericho in the sim.
- (High Priority) Availability on pypi
   - My goal is to have the code available on pypi on Friday. Then, any user with python installed on their machine can install the code with a `pip install [module_name]` command and use it on their machine without the need to even import this repository!
- (Medium priority) Village support:
   - Village support would help answer the question of how useful Monkey City/Monkey Town actually are.
- (Medium priority) Restructure the code:
   - There may be a way to rewrite 'processBuyQueue' so that it uses less lines of code and is easier to understand. (will explain idea here later)
- (Low priority) Robust logging when comparing different strategies
   - The idea here is this: If I have two or more game states that share the same round class and are simulated over the same time span, they are directly comparable. While a method already exists to compare multiple game states with this principle, because it does not share code with the `Game State` class method `viewCashAndEcoHistory`, it is currently inflexible with regards to updates and lacks some of the pizazz the class method has right now.
- (Low Priority) Optimization of the buy queue to prevent redundant computations
   - The code is already reasonably fast, but there are selected cases where the simulator is known to perform the same computation repeatedly when this sort of thing can be avoided.
