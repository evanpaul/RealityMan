import copy
import sys

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
    def negate(self):
        self.negation = not self.negated
        return self
    def copy(self):
        return copy.deepcopy(self)
    def parse_literal_string(self, literal_string):
        self.literal_string = literal_string

        negation = literal_string[0] == "~"
        if negation:  # Chop off negation symbol
            literal_string = literal_string[1:]

        # TODO Change this to "parameters"
        # Make a class that holds values and can either be a constant or var
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
        self.disjoint_literals = []
        self.parse_sentence_string(sentence_string)

    def parse_sentence_string(self, sentence_string):
        disjoint_literals = sentence_string.split("|")

        for lit in disjoint_literals:
            self.disjoint_literals.append(Literal(lit))

    def __str__(self):
        string = "============\n"
        for literal in self.disjoint_literals:
            string += str(literal)
        return string

# TODO Probably need something to distinguish between constants and variables
# so that we don't unify a constant to another constant
def unify_and_combine(sentence, q_lit):
    unifier = {}
    new_sentence = copy.deepcopy(sentence)
    for i, literal in enumerate(new_sentence.disjoint_literals):
        if literal.predicate == q_lit.predicate:
            index = i
            constants = copy.deepcopy(literal.constants)

            j = 0
            for c in constants:
                unifier[c] = q_lit.constants[j] # REVIEW This assumes constant ordering is proper
                j += 1
            break
    new_sentence.disjoint_literals.pop(index)
    # If it's empty, we've successfully found a contradiction
    if not new_sentence.disjoint_literals:
        return None
    # Unify variables
    for lit in new_sentence.disjoint_literals:
        for k, const in enumerate(lit.constants):
            if const in unifier:
                lit.constants[k] = unifier[const]
    return new_sentence




def prove_by_resolution(k_base, query):
    not_query = query.copy().negate()
    KB = copy.deepcopy(k_base)
    target = not_query
    # Does a rule exist in the KB that we can resolve with?
    print(len(KB), "sentences in the KB")
    s_index = 0
    loop_flag = False
    while KB:
        sent = KB[s_index]
        for lit in sent.disjoint_literals:
            # TODO: Update target
            if lit.predicate == target.predicate and lit.negated != target.negated:
                loop_flag = False # Progress?
                print("Found match!")
                print("[TARGET]")
                print(target)
                print("[MATCH]")
                print(lit)
                resultant_sentence = unify_and_combine(sent, query)
                print("[BEFORE]")
                print(sent)
                print("[AFTER]")
                print(resultant_sentence)
                if not resultant_sentence: # Great success!
                    return True
                else: # Update the knowledge base with our new, unified sentence
                    KB[s_index] = resultant_sentence
                break
        if s_index == len(KB) - 1:
            s_index = 0
            if loop_flag:
                return False
            loop_flag = True



if __name__ == "__main__":
    queries, k_base = parse_input("input1.txt")
    # print("[QUERIES]")
    # for q in queries:
    #     print(q)
    # print("[SENTENCES]")
    # for s in sentences:
    #     print(s)
    prove_by_resolution(k_base, queries[3])
