class Logger():
    def __init__(self, name = "obj"):
        self.times = []
        self.sources = []
        self.descriptions = []

    def export(self, filename = 'log', path = 'logs/'):
        with open(path + filename + '.txt', 'w') as f:
            for i in range(len(self.times)):
                f.write("[" + self.times[i] + "] (" + self.sources[i] + ") : " + self.descriptions[i])
                f.write('\n')

    def writeTo(self, time, source, description = "None"):
        self.times.append(time)
        self.sources.append(source)
        self.descriptions.append(description)

    def __call__(self, n):
        return (self.times[n], self.sources[n], self.descriptions[n])