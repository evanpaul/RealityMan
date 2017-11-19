import copy
import sys
from typing import *
from enum import Enum


class UnifStatus(Enum):
    SUCCESS = 1
    EMPTY = 2
    INVALID = 3


class Parameter:
    def __init__(self, param_string: str) -> None:
        self.parse_param(param_string)

    def parse_param(self, param_string: str):
        self.param_string = param_string
        if len(param_string) == 1 and param_string.islower():  # Variable
            self.is_var = True
        elif param_string[0].isupper():  # Constant
            self.is_var = False
        else:
            # TODO: Remove before submitting: assume variable?
            raise ValueError("Malformed parameter")

    def __repr__(self) -> str:
        return self.param_string


class Literal:
    def __init__(self, literal_string: str) -> None:
        self.parse_literal_string(literal_string)

    def negate(self):
        self.negated = not self.negated
        self.update_lit_string()
        return self

    def copy(self):
        return copy.deepcopy(self)

    def contains_only_constants(self) -> bool:
        for p in self.parameters:
            if p.is_var:
                return False
        return True

    def parse_literal_string(self, literal_string: str):
        self.literal_string = literal_string

        negation = literal_string[0] == "~"
        if negation:  # Chop off negation symbol
            literal_string = literal_string[1:]

        parameters = []  # type: List[Parameter]
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

    def update_lit_string(self) -> str:
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

    def __repr__(self) -> str:
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
    def __init__(self, sentence_string: str) -> None:
        self.disjoint_literals = []  # type: List[Literal]
        self.contains_constant = False
        self.parse_sentence_string(sentence_string)

    def clone(self):
        return Sentence(self.update_sentence_string())

    def parse_sentence_string(self, sentence_string: str):
        self.sentence_string = sentence_string
        disjoint_literals = sentence_string.split("|")

        for lit in disjoint_literals:
            if lit:
                self.disjoint_literals.append(Literal(lit.strip()))
        self.disjoint_literals = sorted(
            self.disjoint_literals, key=lambda l: l.predicate)
        self.update_sentence_string()

    def contains_only_constants(self) -> bool:
        for l in self.disjoint_literals:
            if not l.contains_only_constants():
                return False
        return True

    def __repr__(self) -> str:
        return self.sentence_string

    def update_sentence_string(self) -> str:
        resultant_string = ""
        if self.disjoint_literals:
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

    def to_literal(self) -> Literal:
        assert len(self.disjoint_literals) == 1

        return self.disjoint_literals[0]


def printk(kb: List[Sentence]):
    print("=======KB=======")
    i = 0
    for s in kb:
        print(str(i) + ") " + str(s))
        i += 1
    print("===============")


def parse_input(fname: str) -> Tuple[List[Literal], List[Sentence]]:
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


def unify(sentence: Sentence, unifier_dict: Dict[str, str]) -> Tuple[Sentence, UnifStatus]:
    sent = sentence.clone()
    # Typically occurs when sentence is one literal long, but happens whenever
    # a sentence is fully complimented
    if not sent.disjoint_literals:
        return None, UnifStatus.EMPTY

    for literal in sent.disjoint_literals:
        for i, p in enumerate(literal.parameters):
            if str(p) in unifier_dict:
                for _ in literal.parameters:
                    # Disallow resolving s.t. a predicate contains two
                    # equivalent constants
                    if str(_) == unifier_dict[str(p)]:
                        # Invalid resolution
                        print("[INVALID]")
                        print(literal)
                        print(unifier_dict)
                        print("[/]")
                        return None, UnifStatus.INVALID

                literal.parameters[i] = Parameter(unifier_dict[str(p)])
                literal.update_lit_string()
                sent.contains_constant = True  # Most likely redundant
    sent.update_sentence_string()
    return sent, UnifStatus.SUCCESS


'''
[TARGET] Ancestor(Charley,Billy)
[MATCH] ~Ancestor(Charley,z)|Ancestor(Liz,z)
[RESULT] Ancestor(Liz,Billy)

[TARGET] Ancestor(x,y)|~Parent(x,y)
[MATCH] ~Ancestor(Charley,z)|Ancestor(Liz,z)
[RESULT] Ancestor(Liz,z)|~Parent(Charley,y)


[TARGET] ~Ancestor(Liz,Joe)
[MATCH] Ancestor(Liz,z)|~Parent(Charley,y)
[RESULT] ~Parent(Charley,y)
'''


def unify_and_resolve(sent1: Sentence, sent2: Sentence) -> Tuple[Sentence, bool]:
    unifier = {}  # type: Dict[str, str]
    predicate_matches = []  # type: List[Tuple[int, int]]

    # Match predicates
    all_var_flag = True
    const_mismatch = False

    # Go through each literal and find the ones are complimentary matches
    for i, lit1 in enumerate(sent1.disjoint_literals):
        for j, lit2 in enumerate(sent2.disjoint_literals):
            if lit1.predicate == lit2.predicate and lit1.negated != lit2.negated:
                predicate_matches.append((i, j))

                assert(len(lit1.parameters) == len(lit2.parameters))

                # Set up unification of parameters
                for k in range(len(lit1.parameters)):
                    if lit1.parameters[k].is_var and not lit2.parameters[k].is_var:
                        all_var_flag = False
                        unifier[str(lit1.parameters[k])] = str(
                            lit2.parameters[k])
                    elif not lit1.parameters[k].is_var and lit2.parameters[k].is_var:
                        all_var_flag = False
                        unifier[str(lit2.parameters[k])] = str(
                            lit1.parameters[k])
                    elif lit1.parameters[k].is_var and lit2.parameters[k].is_var:
                        pass
                    else:  # both are constants
                        all_var_flag = False
                        if str(lit1.parameters[k]) != str(lit2.parameters[k]):
                            const_mismatch = True
                            break
            if const_mismatch:
                break

    perfect_compliment = len(predicate_matches) == len(sent1.disjoint_literals)
    imperfect_compliment = (all_var_flag and not perfect_compliment)

    if imperfect_compliment or const_mismatch:  # Failure
        return None, False


    s1_copy = sent1.clone()
    s2_copy = sent2.clone()

    # Remove complimentary matched predicates
    for index_tuple in predicate_matches:
        s1_copy.disjoint_literals[index_tuple[0]] = None
        s2_copy.disjoint_literals[index_tuple[1]] = None
    s1_copy.disjoint_literals = [x for x in s1_copy.disjoint_literals if x]
    s2_copy.disjoint_literals = [x for x in s2_copy.disjoint_literals if x]

    # Unify remaining literals
    s1_unified, s1_status = unify(s1_copy, unifier)
    s2_unified, s2_status = unify(s2_copy, unifier)

    if s1_status == UnifStatus.EMPTY and s2_status == UnifStatus.EMPTY:
        if not sent1.contains_only_constants() and not sent2.contains_only_constants():
            # REVIEW I have not seen this case occur yet
            print("HEY, LISTEN!")
            print("-----")
            print(sent1)
            print(sent2)
            print("-----")
            input("...")

            return sent1, False
        else:
            # REVIEW This seems to happen only when we are about to find a
            # contradiction
            print("=======")
            print(sent1.disjoint_literals)
            print(sent2.disjoint_literals)
            print("=======")
            input("...")

    elif s1_status == UnifStatus.INVALID or s2_status == UnifStatus.INVALID:
        # REVIEW This seems to only happen when trying to resolve a predicate
        # with more than one of the same constant
        print("=== Either invalid? ===")
        print(sent1, sent1.contains_only_constants())
        print(sent2, sent2.contains_only_constants())
        print("===>")
        print(s1_unified)
        print(s2_unified)
        print("=======================")

        return None, False

    s1_str = s2_str = ""

    # Update strings
    if s1_unified:
        s1_str = s1_unified.update_sentence_string()
    if s2_unified:
        s2_str = s2_unified.update_sentence_string()

    s1_empty = not bool(s1_str)
    s2_empty = not bool(s2_str)

    if s1_empty and s2_empty:
        return None, True
    elif s1_empty and not s2_empty:
        return Sentence(s2_str), True
    elif not s1_empty and s2_empty:
        return Sentence(s1_str), True
    else:
        return Sentence(s1_str + "|" + s2_str), True


def prove_by_resolution(k_base: List[Sentence], query: Literal) -> bool:
    # Negate query, convert to sentence, and add it to knowledge base
    not_query = Sentence(query.copy().negate().update_lit_string())
    know_base = copy.deepcopy(k_base)
    know_base = [not_query] + know_base

    tried_pairs = {}  # type: Dict[Tuple[str, str], bool]
    t_index = 0
    s_index = 1

    while True:
        # Maximum number of combinations we can possibly try
        saturated = len(know_base) * (len(know_base) - 1)
        # print(s_index, t_index, len(tried_pairs), saturated, len(know_base))
        if len(tried_pairs) % 2 != 0:  # This shouldn't occur! Pairs are added... well... in pairs
            print(tried_pairs)
            sys.exit()  # TODO Remove before submitting!
        if len(tried_pairs) >= saturated:
            print("Tried all combinations! Must be false")
            return False
        try_resolve = True
        resolved_flag = False

        target_sentence = know_base[t_index]
        current_sentence = know_base[s_index]
        # Can't unify variables, and we assume KB is already consistent
        no_const_flag = not target_sentence.contains_constant and not current_sentence.contains_constant

        # Check if we've alraedy tried this pair
        if s_index != t_index:
            try:
                # REVIEW Realistically we only need to check one of these since
                # they should both have the same values
                if tried_pairs[(str(current_sentence), str(target_sentence))] or tried_pairs[(str(target_sentence), str(current_sentence))]:
                    resolved_flag = True
            except KeyError:  # Sloppy, but happens when a key is not in dict
                tried_pairs[(str(current_sentence),
                             str(target_sentence))] = True
                tried_pairs[(str(target_sentence),
                             str(current_sentence))] = True

        if no_const_flag or resolved_flag or s_index == t_index:
            try_resolve = False

        if try_resolve:
            # Look for complimentary matching predicates
            for cur_lit in current_sentence.disjoint_literals:
                breakout = False
                for tar_lit in target_sentence.disjoint_literals:
                    if cur_lit.predicate == tar_lit.predicate and cur_lit.negated != tar_lit.negated:

                        resultant_sentence, status = unify_and_resolve(
                            current_sentence, target_sentence)
                        if status:
                            t_str = "[TARGET] " + str(target_sentence)
                            m_str = "[MATCH] " + str(current_sentence)
                            r_str = "[RESULT] " + str(resultant_sentence)
                            match_str = t_str + "\n" + m_str + "\n" + r_str + "\n\n"

                            # Used in case we want to write results to file
                            MATCHES.append(match_str)
                            print(match_str)

                            if not resultant_sentence:  # Great success!
                                print(
                                    "[!] Contradiction found! Query is consistent with knowledge base.")
                                return True
                            # Update the knowledge base with new sentence
                            in_kb_flag = False
                            for s in know_base:
                                if str(s) == str(resultant_sentence):
                                    in_kb_flag = True
                            # Avoid adding duplicates
                            if not in_kb_flag:
                                know_base.append(resultant_sentence)
                                printk(know_base)
                                # input("...")
                            # REVIEW Which works fastest?
                            t_index = 0
                            s_index = 0

                            breakout = True
                            know_base = sorted(
                                know_base, key=lambda s:
                                len(s.disjoint_literals))

                            break
                if breakout:
                    break
            if breakout:
                continue

        s_index += 1

        if s_index >= len(know_base):
            s_index = 0
            t_index += 1

        if t_index >= len(know_base):
            t_index = 0

    return False


def write_matches(ind=0):
    with open("matches%d.txt" % ind, "w") as f:
        for k in k_base:
            f.write(str(k) + "\n")
        f.write(str(len(MATCHES)) + "\n")
        for m in MATCHES:
            f.write(m)


if __name__ == "__main__":
    CASES = "cases/"
    for i in range(1, 12):
        if i != 2:  # TODO Inputs 2 & 11 currently don't work. Remove before submission!
            continue
        print("======= INPUT " + str(i) + " =========")
        queries, k_base = parse_input(CASES + "input" + str(i) + ".txt")
        print("[!] %d queries and %d sentences" % (len(queries), len(k_base)))

        results = []
        ind = 0
        # Try each query
        try:
            for q in queries:
                MATCHES = []  # type: List[str]
                print(q)
                printk(k_base)
                if prove_by_resolution(k_base, q):
                    results.append("TRUE")
                else:
                    results.append("FALSE")
                write_matches(ind+1)
                ind += 1
        except KeyboardInterrupt:
            write_matches(ind)
            print(results)
            sys.exit()

        # Compare results to expected values
        with open(CASES + "output" + str(i) + ".txt", "r") as f:
            actual = f.read().split('\n')
            for a in actual:
                if not a:
                    actual.remove(a)
            # print(actual)
            assert(len(results) == len(actual))  # TODO Remove all asserts
            print("========== INPUT " + str(i) + " RESULTS ============")

            for j in range(len(results)):
                if actual[j] == results[j]:
                    print(":)", end="")
                else:
                    print(":(", end="")
                print("\tActual:", actual[j], "\tResult:", results[j])
        input("...")
