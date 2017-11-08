def parse_input(fname):
    with open(fname, "r") as f:
        lines = f.read().split("\n")

        num_queries = int(lines[0])
        queries = lines[1:num_queries + 1]

        num_sent = int(lines[num_queries + 1])
        sentences = lines[num_queries + 2:num_queries + num_sent + 2]

    # Instantiate objects for parsing and component representation
    parsed_queries = []
    for q in queries:
        parsed_queries.append(Literal(q))

    parsed_sentences = []
    for s in sentences:
        parsed_sentences.append(Sentence(s))

    return parsed_queries, parsed_sentences


class Literal:
    def __init__(self, literal_string):
        self.parse_literal_string(literal_string)

    def parse_literal_string(self, literal_string):
        self.literal_string = literal_string

        negation = literal_string[0] == "~"
        if negation:  # Chop off negation symbol
            literal_string = literal_string[1:]

        constants = []
        for index, char in enumerate(literal_string):
            if char == "(":  # End of predicate name
                predicate = literal_string[:index]
                const_start_i = index + 1
            elif char == ")":  # End of constant name
                const = literal_string[const_start_i:index]
                constants.append(const)
            elif char == ",":  # New constant
                const = literal_string[const_start_i:index]
                const_start_i = index + 1
                constants.append(const)

        self.negated = negation
        self.predicate = predicate
        self.constants = constants

    def __str__(self):
        const_string = ""
        for i, c in enumerate(self.constants):
            if i == len(self.constants) - 1:
                const_string += c
            else:
                const_string += c + ", "
        string = "\t%s\n[Negated]\t%r\n[Predicate]\t%s\n[Constants]\t%s\n" % (
            self.literal_string, self.negated, self.predicate, const_string)
        return string


class Sentence:
    def __init__(self, sentence_string):
        self.literals = []
        self.parse_sentence_string(sentence_string)

    def parse_sentence_string(self, sentence_string):
        self.sentence_string = sentence_string
        literals = sentence_string.split("|")

        for lit in literals:
            self.literals.append(Literal(lit))

    def __str__(self):
        string = "\t=== %s ===\n" % self.sentence_string
        for literal in self.literals:
            string += str(literal)
        return string


if __name__ == "__main__":
    queries, sentences = parse_input("input1.txt")
    print("[QUERIES]")
    for q in queries:
        print(q)
    print("[SENTENCES]")
    for s in sentences:
        print(s)
