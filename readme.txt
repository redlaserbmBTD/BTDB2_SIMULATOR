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

----------------------------
DESCRIPTION OF THE ALGORITHM
----------------------------

The following is a high-level description of how the eco sim operates. Simulation is governed by the "GameState" class, which in essence is an instance of a game of Battles 2 boiled down to the essential details needed for accurate eco/farm simulation. The primary driver of that simulation is a method within the GameState class called "advanceGameState". This method works as follows: Given a game's current state of time, cash, eco, and farms, and a designated target time, advanceGameState computes the cash, eco, and farms the player will have at the target time. To do this, the code goes through the general procedure:

- Determine from each income source (eco, farm 1, farm 2, etc.) the times that those income sources will pay out to the player and how much will be paid out.
- After all those payout times are determined, sort them in increasing order.
- Finally, one-by-one administer each payment to the player.

While advanceGameState awards payments, it checks whether there is enough money to make purchases or whether sufficient time has passed to change eco sends. A limitation of advanceGameState is that it cannot compute payouts correctly if anything about the player's income sources changes midway through the simulation from the current time to the target time --- say they change eco sends, buy a farm, sell a farm, etc. To counter this, we simply terminate advanceGameState and re-run it in case this occurs. We also define a method "fastForward" which repeatedly runs advanceGameState until the game state is advanced to the target time.

In practice, it is ideal to run advanceGameState repeatedly over small intervals of time, because if advanceGameState is run over a long period of time and has to terminate early, then the computation time spent on payments beyond the early termination time will be wasted. By default, we have fastForward repeatedly run advanceGameState over one second intervals until the target time is reached.

~~ THE BUY QUEUE & ECO QUEUE ~~

The buy queue in essence is the player's flowchart of purchases they intend to make throughout the game. An item in the buy queue is not necessarily just one purchase but possibly a combination of purchases and sells --- i.e. selling a Central Market into a Banana Central. The eco queue in essence is the strategy of eco'ing the player intends to follow throughout the game --- i.e. eco Grouped Reds on Rounds 1-2, then eco Grouped Blues on Rounds 3-4, etc. 

After all payouts in a given time have been issued --- in rare cases, multiple income sources may pay out at the same time --- advanceGameState will check whether the first item in the buy queue can be carried out by computing the hypothetical cash (and loan amount, if the player has an outstanding IMF loan) the player would have in hand if they were to perform the transaction now. If the purchase sequence can be performed, advanceGameState performs it, and then terminates early. advanceGameState will also check whether time has progressed enough for the player to switch eco sends. Again, the process is terminated early in the event of an eco change.

~~ DATA VISUALIZATION ~~

Whenever advanceGameState terminates or awards a payment to a player, it records the cash and eco the player has at the time of payment and also records the time of that payment too. By repeatedly running advanceGameState as we do using the fastForward method, the simulation effectively records the player's cash and eco at least every second, and possibly even more frequently when there are payment or the user specifies a tighter interval to run advanceGameState repeatedly along.

~~ ECO SAFEGUARDING ~~

To prevent the player from using unavailable eco sends, the code has built in safeguards. The safeguarding is performed entirely by the "ecoQueueCorrection" method within the GameState class. Here is how it works:

The safeguard looks at the very first send in the eco queue and determines whether the time associated with it is valid or not. If the time is too late, then the send is discarded from the eco queue. If it is too early, the code will modify the time to the earliest time that it is available. If this change results in the second item in the eco queue being listed at a time before the first item, then the first item is discarded. Otherwise, we keep the send and check whether the new time is (still) before the current time in the Game State. If it is, then we exercise the first item in the eco queue.

If the safeguard discards or exercises a send in the eco queue, it will restart the above procedure for the next send, continuing either until the queue is empty, or the first item in the eco queue is determined to be valid (not too late or too early, but *just* right!)

-----------------
KNOWN LIMITATIONS
-----------------

1. Eco simulation - 
- The simulator assumes for simplicity that eco works as a continuous "stream" rather than as sending discrete sets of bloons into the eco queue like in the game. This means the sim cannot account for the initial eco bonus gotten from eco'ing into an empty queue and the eco penalty that occurs when the player stop eco'ing from a full queue.
- advanceGameState only checks the eco_queue just before terminating. If it's run every second, this is *okay* since it means that it checks every second that we can go from one eco send to the next, but end users may desire finer control over this aspect.

2. Farms - 
If a bank is declared in the initial game state with a purchase time set prior to the simulation's starting time, the simulator currently does not compute the payments the bank would receive in the time between purchase time and initial time. 

3. Elite Sniper - 
If a game state is initialized with an elite sniper, the code assumes the first crate may be issued 20 seconds (initial cooldown) after the purchase time. In practice, the elite sniper inherits the cooldown of the supply drop that it is upgraded from.

4. Round lengths -
The round length data is based on old data collected from spoonoil and ninjayas back in October 2022. This data only goes up to the conclusion of R30 and may be outdated. I *also* assume that the minimum time for a round is the amount of time it takes for all natural bloons to appear plus 4 seconds. There may be inaccuracies in the data collected arising from these assumptions.

--------------------------------------
POSSIBLE FEATURES TO ADD IN THE FUTURE
--------------------------------------

1. Implementation of boat farms/druid farms/heli farms. 
2. More robust data visualization tools for comparing strategies.
3. More accurate simulation of eco'ing.
4. Tools for easily optimizing strategies. (This one doesn't seem feasible, but see examples for what can be done in a case-by-case basis.)
