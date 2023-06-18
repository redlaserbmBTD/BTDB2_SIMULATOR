# Welcome!

Hi there! I'm redlaserbm, the main developer of the BTDB2 Eco simulator. To get started with using the code, please read through this README file! 

- To learn more about how the code works, see the documentation file at documentation/documentation.pdf
- To operate the code, see the section on operating the code
- Want to request features for the code? Want to help out with the code? Found a bug? Don't hesitate to contact me! The quickest way to reach me concerning the code is by messaging me on discord at redlaserbm#1347

# Operating the Code

Users unfamiliar with coding who just need essential functionality should use the lightweight version of this simulator on spoonoil's website https://b2.lol. Newbies unfamiliar with coding who nonetheless want to operate the back-end code should follow the steps below to get the code up and running:
1. Download the latest Anaconda distribution to your computer https://www.anaconda.com/download/ The Anaconda distribution contains a Python "environment" which allows you to run Python code on your computer
2. Use GitHub Desktop to clone the repository to your desktop. 
3. One of the programs bundled with the Anaconda distribution is jupyter notebook. Launch jupyter notebook, navigate to where you cloned the repository, and open examples.ipynb
4. You are now ready to operate the code!

## Running a simulation in code

To begin running a simulation, first start by initilizaing the rounds class.

```python
rounds = Rounds(0.0)
```
The number inside is the *stall factor* of the game. This number may vary from 0 to 1, and a higher number means longer rounds. Next, if you have any farms presently in play, go ahead and declare those like so:

```python
farms = {
    0: initFarm(0, upgrades = [4,2,0]), 
    1: initFarm(0, upgrades = [2,0,4]),
    2: initFarm(rounds.getTimeFromRound(19.999), upgrades = [2,0,4])
}
```
The indexes of the farm dictionary should nonnegative integers. The first argument of `InitFarm` specifies the purchase time of the farm. Our next step is to initialize the eco and buy queues, which determine our strategy for eco'ing and the purchases we intend to make over the course of the simuation. 

```python
buy_queue = [
    
    #Sell into MWS
    [sellFarm(0), sellFarm(1), upgradeFarm(2,2)], 
    
    #Buy a 420 Farm
    [buyFarm()],
    [upgradeFarm(3,0)],
    [upgradeFarm(3,0)],
    [upgradeFarm(3,0)],
    [upgradeFarm(3,1)],
    [upgradeFarm(3,1)],
    [upgradeFarm(3,0)],
    
    #Buy another 420 Farm
    [buyFarm()],
    [upgradeFarm(4,0)],
    [upgradeFarm(4,0)],
    [upgradeFarm(4,0)],
    [upgradeFarm(4,1)],
    [upgradeFarm(4,1)],
    [upgradeFarm(4,0)],
    
    #Sell into BC
    [sellFarm(2),upgradeFarm(3,0)]
]
```
The buy queue is a list of lists. That is, each item in the buy queue is a list which specifies a set of transactions to perform simultaneously. In most cases this list will only contain one element, but there are moments where it is useful to specify multiple at once --- consider for example, selling one farm and immediately buying an upgrade on another farm with the money. --- Finally, let's collect all components of our initial game state into a dictionary:

```python
initial_state_game = {
    'Cash': 0,
    'Eco': 2000,
    'Eco Send': 'Zero',
    'Rounds': rounds,
    'Game Round': 24.5,
    'Farms': farms,
    'Buy Queue': buy_queue
}
```
To simulate, we do something like the following:
```python
game_state = GameState(initial_state_game)
game_state.fastForward(target_round = 28)
game_state.viewCashEcoHistory()
print("Current Cash and Eco: (%s,%s)"%(np.round(game_state.cash,0),np.round(game_state.eco,0)))
```
The 2nd to last line displays a graph of eco and cash over time, along with a labellings of when rounds start, changes in eco are made, and when purchases are made.

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
- (June 16, 2023 - v0.9.5)
   - Remedied an issue where the eco simualator would sometimes ignore items in the buy queue for several seconds. The eco simulator now checks the buy queue at the minimum every `interval` seconds.
- (June 1, 2023 - v0.9.4)
   - Various updates to keep the game in line with v1.10.3 of the game
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

- (High priority) Restructure the code:
   - While usage of the code for simulation purposes is relatively easy, reading the code to understand how it does what it does is *not*. The goal is to clean up the code so that potential collaborators may be more inclined to contribute.
- (High priority) Implementation of more accurate eco system:
   - This simulator currently makes the simpifying assumption that eco works as a continuous stream of income generation rather than how it actually functions in the game, which is as discrete "packs" which award eco in chunks. This simplifying assumption causes the sim to underestimate eco values compared to actual game scenarios.
- Robust logging when comparing different strategies
- Optimization of the buy queue to prevent redundant computations
- Heli alt-eco
