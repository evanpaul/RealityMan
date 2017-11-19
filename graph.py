from graphviz import Digraph


class ResolutionGraph:
    i = 0

    def __init__(self):
        ResolutionGraph._incr()
        self.new = True
        self.graph = Digraph(comment='Resolution Graph', format="png")

    @staticmethod
    def _incr():
        ResolutionGraph.i += 1

    def add(self, parent1, parent2, child):
        p1 = str(parent1)
        p2 = str(parent2)

        if self.new:
            self.new = False
            if p1[0] == "~":
                self.graph.node(p1, shape="doublecircle", color="blue")
            else:
                self.graph.node(p2, shape="doublecircle", color="blue")

        if child:
            c = str(child)
            self.graph.node(c)
        else:
            c = "{}"
            self.graph.node(c, shape='star', color="red")

        self.graph.edge(p1, c)
        self.graph.edge(p2, c)

    def view(self):
        self.graph.render('graphs/graph%d' % ResolutionGraph.i, view=False)


#
# dot.node('A', 'King Arthur')
# dot.node('B', 'Sir Bedevere the Wise')
# dot.node('L', 'Sir Lancelot the Brave')
#
# dot.edges(['AB', 'AL'])
# dot.edge('B', 'L', constraint='false')
# dot.render('test-output/round-table.gv', view=True)  # doctest: +SKIP
# 'test-output/round-table.gv.pdf'
