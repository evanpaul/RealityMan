import copy
import sys
from typing import *


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
            self.is_var = True
        elif param_string[0].isupper():  # Constant
            self.is_var = False
        else:
            raise ValueError("Malformed parameter")

    def __repr__(self):
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

    def __repr__(self):
        param_string = ""
        for i, p in enumerate(self.parameters):
            if i == len(self.parameters) - 1:
                param_string += str(p)
            else:
                param_string += str(p) + ", "
        string = "%s\n[Negated]\t%r\n[Predicate]\t%s\n[Parameters]\t%s\n" % (
            self.literal_string, self.negated, self.predicate, param_string)
        return string


class Sentence:
    def __init__(self, sentence_string):
        self.disjoint_literals = []
        self.contains_constant = False
        self.parse_sentence_string(sentence_string)

    def parse_sentence_string(self, sentence_string):
        self.sentence_string = sentence_string
        disjoint_literals = sentence_string.split("|")

        for lit in disjoint_literals:
            self.disjoint_literals.append(Literal(lit.strip()))
        self.update_sentence_string()

    def __repr__(self):
        string = "%s" % self.sentence_string
        # for literal in self.disjoint_literals:
        #     string += str(literal)
        return string

    def update_sentence_string(self):
        resultant_string = ""
        for i, lit in enumerate(self.disjoint_literals):
            if lit.negated:
                resultant_string += "~"
            resultant_string += lit.predicate + "("

            for j, p in enumerate(lit.parameters):
                if not p.is_var:
                    self.contains_constant = True

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
    if not sentence.disjoint_literals:
        return None
    # print("[UNIFIED]")
    # print(unifier_dict)
    for literal in sentence.disjoint_literals:
        for i, p in enumerate(literal.parameters):
            if str(p) in unifier_dict:
                # print(literal.parameters[i], "=>", unifier_dict[str(p)])
                literal.parameters[i] = unifier_dict[str(p)]
                literal.update_lit_string()
                sentence.contains_constant = True
                # print(literal)
    sentence.update_sentence_string()
    return sentence


def unify_and_resolve(sent1, sent2):
    unifier = {}
    matches = []

    # Match predicates
    flag = False
    for i, lit1 in enumerate(sent1.disjoint_literals):
        for j, lit2 in enumerate(sent2.disjoint_literals):
            if lit1.predicate == lit2.predicate and lit1.negated != lit2.negated:
                matches.append((i, j))

                assert(len(lit1.parameters) == len(lit2.parameters))

                # REVIEW Set up unification of parameters
                for k in range(len(lit1.parameters)):
                    if lit1.parameters[k].is_var and not lit2.parameters[k].is_var:
                        print("[1]")
                        flag = True
                        unifier[str(lit1.parameters[k])] = str(
                            lit2.parameters[k])
                    elif not lit1.parameters[k].is_var and lit2.parameters[k].is_var:
                        flag = True
                        print("[2]")
                        unifier[str(lit2.parameters[k])] = str(
                            lit1.parameters[k])
                    elif lit1.parameters[k].is_var and lit2.parameters[k].is_var:
                        print("[OY]")
                        pass
                    else:  # both are constants
                        pass

    if not flag:
        return sent1, flag

    s1_copy = copy.deepcopy(sent1)
    s2_copy = copy.deepcopy(sent2)

    for index_tuple in matches:
        s1_copy.disjoint_literals[index_tuple[0]] = None
        s2_copy.disjoint_literals[index_tuple[1]] = None
    s1_copy.disjoint_literals = [x for x in s1_copy.disjoint_literals if x]
    s2_copy.disjoint_literals = [x for x in s2_copy.disjoint_literals if x]
    # print(s1_copy.disjoint_literals)
    # print(s2_copy.disjoint_literals)

    # Remove literals and unify remaining
    s1_copy = unify(s1_copy, unifier)
    s2_copy = unify(s2_copy, unifier)

    s1_str = s2_str = ""

    if s1_copy:
        s1_str = s1_copy.update_sentence_string()
    if s2_copy:
        s2_str = s2_copy.update_sentence_string()

    s1_empty = not bool(s1_str)
    s2_empty = not bool(s2_str)

    if s1_empty and s2_empty:
        return None, flag
    elif s1_empty and not s2_empty:
        return Sentence(s2_str), flag
    elif not s1_empty and s2_empty:
        return Sentence(s1_str), flag
    else:
        return Sentence(s1_str + "|" + s2_str), flag


def prove_by_resolution(k_base, query):
    not_query = Sentence(query.copy().negate().update_lit_string())
    KB = copy.deepcopy(k_base)
    KB = [not_query] + KB
    # Does a rule exist in the KB that we can resolve with?
    # print(len(KB), "sentences in the KB")
    s_index = t_index = 0
    while KB:
        try_resolve = True
        print(s_index, t_index)
        # print(s_index, loop_flag)
        target_sentence = KB[t_index]
        current_sentence = KB[s_index]
        # No need to check for resolution if they're the same

        if not target_sentence.contains_constant and not current_sentence.contains_constant:
            try_resolve = False
        # print("=" * 10, "COMPARE", "=" * 10)
        # print(current_sentence)
        # print(target_sentence)
        if try_resolve:
            for cur_lit in current_sentence.disjoint_literals:
                breakout = False
                for tar_lit in target_sentence.disjoint_literals:
                    # TODO: Update target
                    if cur_lit.predicate == tar_lit.predicate and cur_lit.negated != tar_lit.negated:
                        # print("Found match!")
                        print("[TARGET]", end=" ")
                        print(target_sentence)
                        print("[MATCH]", end=" ")
                        print(current_sentence)
                        resultant_sentence, status = unify_and_resolve(
                            current_sentence, target_sentence)
                        if status:
                            print("[AFTER]", end=" ")
                            print(resultant_sentence)
                            if not resultant_sentence:  # Great success!
                                return True
                            # Update the knowledge base with our new, unified
                            # sentence
                            KB[s_index] = resultant_sentence
                            del KB[t_index]
                            # target_sentence = resultant_sentence
                            t_index = s_index = 0
                            breakout = True
                            break
                if breakout:
                    break
            if breakout:
                continue

        s_index += 1

        if s_index == t_index:
            s_index += 1

        # print(s_index, t_index, len(KB))
        if s_index >= len(KB) - 1:
            s_index = 0
            t_index += 1
            target = KB[t_index]

            if t_index == len(KB) - 1:
                print("===KB===")
                for k in KB:
                    print(k)
                print("========")
                return False
            loop_flag = True


''' What do I do about this
[TARGET] ~R(x) | H(x)
[MATCH] ~D(x,y) | ~H(y)
[AFTER]~D(x,y)|~R(x)
'''


if __name__ == "__main__":
    CASES = "cases/"
    for i in range(1, 2):
        print("======= INPUT " + str(i) + " =========")
        queries, k_base = parse_input(CASES + "input" + str(i) + ".txt")
        print("[!] %d queries and %d sentences" % (len(queries), len(k_base)))
        results = []
        for q in queries:
            if prove_by_resolution(k_base, q):
                results.append("TRUE")
            else:
                results.append("FALSE")
        # Compare results to expected values
        with open(CASES + "output" + str(i) + ".txt", "r") as f:
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
