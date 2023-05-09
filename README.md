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

# Code Features

1. **Simultaneous simulation of eco, farms, and alt-eco:** When given an eco send to use and some arrangement of farms and alt-eco, the simulator accurately tracks the progression of the player's cash and eco over time. The results of the simulator are nearly true to the game.
2. **Easy operation:** Simply input your initial cash and eco, the round to start on, and the purchases you intend to make and the eco flowchart you intend to follow over the course of the match. The code runs in one click and delivers results in seconds.
3. **Complete Farm support:** The simulator supports IMF Loans and Monkeyopolis. Also, the simulator supports compound purchases, such as selling into Monkey Wall Street.
4. **Strategy Comparison:** You can compare multiple different strategies, see how cash and eco progresses over time for each one, and decide what strategy you like better with the \texttt{compareStrategies()} function.
5. **Advanced Optimization Potential:** The code's fast run time means that it operates well when used in black-box optimization problems.

# Feature Requests

- Druid and Heli alt-ecos
- Ability to change the stall factor mid simulation
- Robust logging when comparing different strategies
- Optimization of the buy queue to prevent redundant computations
