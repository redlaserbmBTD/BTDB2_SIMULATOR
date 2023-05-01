------------
INTRODUCTION
------------

Hi there! Welcome to the Bloons TD Battles 2 Eco Simulator! I'm redlaserbm, the code's main developer. The goal of this project is to develop a program that can quickly and accurate simulate eco/farm/alt-eco strategies within b2 so that players can more quickly theory craft and optimize their strategies in-game. Note, however, that this project is all back-end code, with no fancy UI of any sorts associated with it. With this in mind, the following readme is primarily aimed at:

1. Front-end developers who want to develop a UI for the project so that the common man can operate the simulator with ease.
2. Technical audiences with a strong math/coding background who wish to utilize the code for advanced purposes that the common player is unlikely to encounter.

------------------
OPERATING THE CODE
------------------

Users new to the code should view the "Simulation Examples" section in main.ipynb. In general, the procedure for simulating a game looks like this:

1. Set the round lengths by creating an instance of Rounds(stall_factor). stall_factor is a variable from 0 to 1 indicating the level of stall in the game (higher means more stall).
2. Define the buy queue and eco queue for your game state. These queues are lists containing the eco flowchart and flowchart of purchases you intend to follow as you progress through the game.
3. Declare the initial state of the game. How much cash do you have? Eco? Current round? etc.
4. Create an instance game_state of GameState using the info defined above, and then use game_state.fastForward(target_round = X) to simulate what would happen if the game were to progress to round X according to your strategy.

--------------------------------------------
FARM/ALT-ECO OBJECTS IN THE GameState CLASS:
--------------------------------------------

FARMS IN THE GameState CLASS:
Information about farms is stored in the class variable "farms". The farms object is a dictionary with integer keys starting at 0 representing ordinally when the farm was bought, starting from 0. Thus, if there are three farms in the game state, the third one will have index 2. Note that when a farm is sold, the indexing of other farms will note index. Thus, if we have three farms, sell the second one (index 1) and then buy a new farm, the new farm will have index 3, and the game state will have farms corresponding to indices 0,2,3. This structure helps substantially simplify the process of simulating compound purchases.

SNIPER FARMS:
Sniper farms are also stored as a dictionary object, this time in the class variable "supply_drops". The values in this dictionary are just the purchase times of the snipers. A separate variable "elite_sniper" is an integer which states which key in "supply_drops" corresponds to the elite sniper (it has value None if there is none).

BUY QUEUE:

The buy queue works by arranging a sequence of purchases in order, and performing each purchase in the queue as soon as it becomes possible to do so. The code will always check whether you have enough money first, but the user can optionally specify how much extra money beyond the purchase cost they want to save before making the purchase --- this is called "buffer" --- or a minimum time before which the purchase cannot be made.

Purchases can include a sequence of multiple operations. A purchase could be as simple as buying defense, or it could be as complex as selling one farm to buy an upgrade for another.

ECO QUEUE:

The eco queue works by arranging a sequence of items consisting of an eco send paired with a time, and switching the eco send the player is using to the next one in the queue once the player reaches the associated time.

-----------------
KNOWN LIMITATIONS
-----------------

1. Eco simulation - 
The simulator assumes for simplicity that eco works as a continuous "stream" rather than as sending discrete sets of bloons into the eco queue like in the game. This means the sim cannot account for the initial eco bonus gotten from eco'ing into an empty queue and the eco penalty that occurs when the player stop eco'ing from a full queue.

2. Farms - 
If a bank is declared in the initial game state with a purchase time set prior to the simulation's starting time, the simulator currently does not compute the payments the bank would receive in the time between purchase time and initial time. 

3. Elite Sniper - 
If a game state is initialized with an elite sniper, the code assumes the first crate may be issued 20 seconds (initial cooldown) after the purchase time. In practice, the elite sniper inherits the cooldown of the supply drop that it is upgraded from.

4. Round lengths -
The round length data is based on old data collected from spoonoil and ninjayas back in October 2022. This data only goes up to the conclusion of R30 and may be outdated. I *also* assume that the minimum time for a round is the amount of time it takes for all natural bloons to appear plus 4 seconds. There may be inaccuracies in the data collected arising from these assumptions.
