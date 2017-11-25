from graphviz import Digraph


class ResolutionGraph:
    def __init__(self, file_num, query_num=1):
        self.query_num = query_num
        self.new = True
        self.graph = Digraph(comment='Resolution Graph', format="png")
        self.file_num = file_num

    def next_query(self):
        return ResolutionGraph(self.file_num, self.query_num + 1)

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

    def save(self):
        path = 'graphs/input%dquery%d' % (self.file_num, self.query_num)
        print("[!] Saving resolution graph to:", path)
        self.graph.render(path, view=False)
