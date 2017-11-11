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


class Parameter:
    def __init__(self, param_string):
        self.parse_param(param_string)

    def parse_param(self, param_string):
        self.param_string = param_string
        if len(param_string) == 1 and param_string.islower():  # Variable
            self.var = True
        elif param_string[0].isupper():  # Constant
            self.var = False
        else:
            raise ValueError("Malformed parameter")

    def is_var(self):
        return self.var

    def __str__(self):
        return self.param_string


class Literal:
    def __init__(self, literal_string):
        # REVIEW Does this ever need to be updated?
        self.parse_literal_string(literal_string)

    def negate(self):
        self.negation = not self.negated
        self.update_lit_string()
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
        parameters = []
        for index, char in enumerate(literal_string):
            if char == "(":  # End of predicate name
                predicate = literal_string[:index]
                param_start_i = index + 1
            elif char == ")":  # End of parameter name
                param = literal_string[param_start_i:index]
                parameters.append(Parameter(param))
            elif char == ",":  # New parameter
                param = literal_string[param_start_i:index]
                param_start_i = index + 1
                parameters.append(Parameter(param))

        self.negated = negation
        self.predicate = predicate
        self.parameters = parameters

    def update_lit_string(self):
        result = ""
        if self.negated:
            result += "~"
        result += self.predicate + "("
        for i, p in enumerate(self.parameters):
            result += str(p)
            if i != len(self.parameters) - 1:
                result += ","
        result += ")"

        self.literal_string = result

        return self.literal_string

    def __str__(self):
        param_string = ""
        for i, p in enumerate(self.parameters):
            if i == len(self.parameters) - 1:
                param_string += str(p)
            else:
                param_string += str(p) + ", "
        string = "\t%s\n[Negated]\t%r\n[Predicate]\t%s\n[Parameters]\t%s\n" % (
            self.literal_string, self.negated, self.predicate, param_string)
        return string


class Sentence:
    def __init__(self, sentence_string):
        self.disjoint_literals = []
        self.parse_sentence_string(sentence_string)

    def parse_sentence_string(self, sentence_string):
        self.sentence_string = sentence_string
        disjoint_literals = sentence_string.split("|")

        for lit in disjoint_literals:
            self.disjoint_literals.append(Literal(lit))

    def __str__(self):
        string = "=== %s ===\n" % self.sentence_string
        for literal in self.disjoint_literals:
            string += str(literal)
        return string

    def update_sentence_string(self):
        resultant_string = ""
        for i, lit in enumerate(self.disjoint_literals):
            if lit.negated:
                resultant_string += "~"
            resultant_string += lit.predicate + "("

            for j, p in enumerate(lit.parameters):
                resultant_string += str(p)

                if j != len(lit.parameters) - 1:
                    resultant_string += ","

            resultant_string += ")"
            if i != len(self.disjoint_literals) - 1:
                resultant_string += "|"
        self.sentence_string = resultant_string
        return resultant_string

    def to_literal(self):
        assert len(self.disjoint_literals) == 1

        return self.disjoint_literals[0]


# REVIEW Don't need to return, right?
def unify(sentence, unifier_dict):
    for literal in sentence.disjoint_literals:
        if not literal:
            sentence.disjoint_literals.remove(literal)
        else:
            for i, p in enumerate(literal.parameters):
                if p in unifier_dict:
                    literal.parameters[i] = unifier[p]


def unify_and_resolve(sent1, sent2):
    unifier = {}
    matches = []

    # Match predicates
    for i, lit1 in enumerate(sent1.disjoint_literals):
        for j, lit2 in enumerate(sent2.disjoint_literals):
            if lit1.predicate == lit2.predicate and lit1.negated != lit2.negated:
                matches.append((i, j))

                assert(len(lit1.parameters) == len(lit2.parameters))

                # REVIEW Set up unification of parameters
                for k in range(len(lit1.parameters)):
                    if lit1.parameters[k].is_var() and not lit2.parameters[k].is_var():
                        unifier[lit1.parameters[k]] = lit2.parameters[k]
                    elif not lit1.parameters[k].is_var() and lit2.parameters[k].is_var():
                        unifier[lit2.parameters[k]] = lit1.parameters[k]
                    elif lit1.parameters[k].is_var() and lit2.parameters[k].is_var():
                        pass
                    else:  # both are constants
                        pass
    s1_copy = copy.deepcopy(sent1)
    s2_copy = copy.deepcopy(sent2)

    for index_tuple in matches:
        s1_copy.disjoint_literals[index_tuple[0]] = None
        s2_copy.disjoint_literals[index_tuple[1]] = None

    # Remove literals and unify remaining
    unify(s1_copy, unifier)
    unify(s2_copy, unifier)

    s1_str = s1_copy.update_sentence_string()
    s2_str = s2_copy.update_sentence_string()

    s1_empty = not bool(s1_str)
    s2_empty = not bool(s2_str)

    if s1_empty and s2_empty:
        return None
    elif s1_empty and not s2_empty:
        return Sentence(s2_str)
    elif not s1_empty and s2_empty:
        return Sentence(s1_str)
    else:
        return Sentence(s1_str + "|" + s2_str)


def prove_by_resolution(k_base, query):
    not_query = query.copy().negate()
    KB = copy.deepcopy(k_base)
    target_sentence = Sentence(not_query.update_lit_string())
    # Does a rule exist in the KB that we can resolve with?
    # print(len(KB), "sentences in the KB")
    s_index = 0
    loop_flag = False
    while KB:
        # print(s_index, loop_flag)
        current_sentence = KB[s_index]
        # No need to check for resolution if they're the same
        if current_sentence == target_sentence:
            s_index += 1
            continue

        # print("=" * 10, "COMPARE", "=" * 10)
        # print(current_sentence)
        # print(target_sentence)

        for cur_lit in current_sentence.disjoint_literals:
            breakout = False
            for tar_lit in target_sentence.disjoint_literals:
                # TODO: Update target
                if cur_lit.predicate == tar_lit.predicate and cur_lit.negated != tar_lit.negated:
                    loop_flag = False  # Progress?
                    # print("Found match!")
                    # print("[TARGET]")
                    # print(target_sentence)
                    # print("[MATCH]")
                    # print(current_sentence)
                    resultant_sentence = unify_and_resolve(
                        current_sentence, target_sentence)
                    # print("[BEFORE]")
                    # print(current_sentence)
                    # print("[AFTER]")
                    # print(resultant_sentence)
                    if not resultant_sentence:  # Great success!
                        return True
                    # Update the knowledge base with our new, unified sentence
                    KB[s_index] = resultant_sentence
                    target_sentence = resultant_sentence
                    s_index = -1
                    breakout = True
                    break
            if breakout:
                break

        if s_index == len(KB) - 1:
            s_index = 0
            if loop_flag:
                return False
            loop_flag = True
        s_index += 1


if __name__ == "__main__":
    for i in range(1, 4):
        print("======= INPUT " + str(i) + " =========")
        queries, k_base = parse_input("input" + str(i) + ".txt")
        results = []
        for q in queries:
            if prove_by_resolution(k_base, q):
                results.append("TRUE")
            else:
                results.append("FALSE")
        with open("output" + str(i) + ".txt", "r") as f:
            actual = f.read().split('\n')
            for a in actual:
                if not a:
                    actual.remove(a)
            # print(actual)
            assert(len(results) == len(actual))

            for j in range(len(results)):
                if actual[j] == results[j]:
                    print(":)", end="")
                else:
                    print(":(", end="")
                print("\tActual:", actual[j], "Result:", results[j])
