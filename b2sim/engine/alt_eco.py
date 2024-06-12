# Generalized alt eco class definition for 

class AltEco():
    def __init__(self, purchase_time = 0, T5 = False, eco_type = "sniper"):
        # When was the alt eco purchased?
        self.purchase_time = purchase_time

        if eco_type == "sniper":
            self.info = {
                "Initial Delay": 20,
                "Use Delay": 40,
                "T4 Payout": 2000,
                "T5 Payout": 5000,
                "T5 Cost": 14000
            }
        elif eco_type == "druid":
            self.info = {
                "Initial Delay": 15,
                "Use Delay": 40,
                "T4 Payout": 1000,
                "T5 Payout": 1500,
                "T5 Cost": 35000
            }
        elif eco_type == "heli":
            self.info = {
                "Initial Delay": 20,
                "Use Delay": 60,
                "T4 Payout": 4000,
                "T5 Payout": 8000,
                "T5 Cost": 30000
            }
        # How long after purchase does it take until I can use the alt eco for the first time?
        self.initial_delay = self.info["Initial Delay"]

        # After the first usage, how long do I have to wait in between uses?
        self.use_delay = self.info["Use Delay"]

        # How much cash do I get each time?
        if T5:
            self.payout_amount = self.info["T5 Payout"]
        else:
            self.payout_amount = self.info["T4 Payout"]
        self.T5 = T5

        # How much do I need to upgrade this alt eco to a T5?
        self.upgrade_cost = self.info["T5 Cost"]

        # Revenue/Expense tracking
        self.revenue = 0
        self.expenses = 0

        self.h_revenue = 0

        # Rather than remove an alt-eco from the simulator when sold, we will just mark its sell time and tell the simulator not to consider payments from this alt-eco anymore
        self.sell_time = None
    
    def upgrade(self):
        if not self.T5:
            self.T5 = True
            self.payout_amount = self.info["T5 Payout"]
            self.expenses += self.info["T5 Cost"]

    def update(self):
        if self.T5:
            self.payout_amount = self.info["T5 Payout"]
        else:
            self.payout_amount = self.info["T4 Payout"]

class Sniper(AltEco):
    def __init__(self, purchase_time = 0, T5 = False):
        AltEco.__init__(self, purchase_time, T5, "sniper")

class Heli(AltEco):
    def __init__(self, purchase_time = 0, T5 = False):
        AltEco.__init__(self, purchase_time, T5, "heli")

class Druid(AltEco):
    def __init__(self, purchase_time = 0, T5 = False):
        AltEco.__init__(purchase_time, T5, "alt-eco")
        if T5:
            self.end_of_round_payout = 2500
        else:
            self.end_of_round_payout = 0
        self.T5 = T5
    
    def upgrade(self):
        if not self.T5:
            self.end_of_round_payout = 2500
        
        return super().upgrade()