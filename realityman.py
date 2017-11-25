import copy
import sys
from typing import *
from enum import Enum
from collections import defaultdict
from graph import ResolutionGraph


class UnifStatus(Enum):
    FAIL = 0
    SUCCESS = 1
    MULTI = 2
    EMPTY = 3
    INVALID = 4


class Parameter:
    def __init__(self, param_string: str) -> None:
        self.parse_param(param_string)

    def parse_param(self, param_string: str) -> None:
        self.param_string = param_string
        if len(param_string) == 1 and param_string.islower():  # Variable
            self.is_var = True
        elif param_string[0].isupper():  # Constant
            self.is_var = False
        else:
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

    def __eq__(self, other):
        if str(self) == str(other):
            return True
        return False

    def __hash__(self):
        return hash(str(self))

    def copy(self):
        return copy.deepcopy(self)

    def contains_only_constants(self) -> bool:
        for p in self.parameters:
            if p.is_var:
                return False
        return True

    def parse_literal_string(self, literal_string: str) -> None:
        self.literal_string = literal_string

        negation = literal_string[0] == "~"
        if negation:  # Chop off negation symbol
            literal_string = literal_string[1:]

        parameters: List[Parameter] = []
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

    def __repr__(self):
        return self.update_lit_string()


class Sentence:
    def __init__(self, sentence_string: str) -> None:
        self.disjoint_literals: List[Literal] = []
        self.contains_constant = False
        self.parse_sentence_string(sentence_string)

    def clone(self):
        return Sentence(self.update_sentence_string())

    def parse_sentence_string(self, sentence_string: str) -> None:
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

    def __repr__(self):
        return self.sentence_string

    def __eq__(self, other):
        if str(self) == str(other):
            return True
        return False

    def __hash__(self):
        return hash(str(self))

    def update_sentence_string(self) -> str:
        resultant_string = ""
        self.disjoint_literals.sort(key=lambda l: l.predicate)
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
                        return None, UnifStatus.INVALID

                literal.parameters[i] = Parameter(unifier_dict[str(p)])
                literal.update_lit_string()
                sent.contains_constant = True  # Most likely redundant
    sent.update_sentence_string()
    return sent, UnifStatus.SUCCESS


def resolve(sent1: Sentence,
            sent2: Sentence,
            predicate_matches: List[Tuple[int, int]],
            unifier: Dict[str, str],
            perfect_compliment: bool) -> Tuple[Any, UnifStatus]:
    s1_copy = sent1.clone()
    s2_copy = sent2.clone()
    # No need to unify predicates that will cancel out
    for index_tuple in predicate_matches:
        s1_copy.disjoint_literals[index_tuple[0]] = None
        s2_copy.disjoint_literals[index_tuple[1]] = None
    s1_copy.disjoint_literals = [x for x in s1_copy.disjoint_literals if x]
    s2_copy.disjoint_literals = [x for x in s2_copy.disjoint_literals if x]

    # Unify remaining literals
    s1_unified, s1_status = unify(s1_copy, unifier)
    s2_unified, s2_status = unify(s2_copy, unifier)

    # If the result is empty, double-check that we have a  compliment.
    # Otherwise, something unknown went wrong.
    if s1_status == UnifStatus.EMPTY and s2_status == UnifStatus.EMPTY:
        if not sent1.contains_only_constants() and not sent2.contains_only_constants():
            if perfect_compliment:
                return None, UnifStatus.SUCCESS
            else:
                return None, UnifStatus.FAIL
    # Invalid unification
    elif s1_status == UnifStatus.INVALID or s2_status == UnifStatus.INVALID:
        return None, UnifStatus.FAIL

    # Update string representations
    s1_str = s2_str = ""

    if s1_unified:
        s1_str = s1_unified.update_sentence_string()
    if s2_unified:
        s2_str = s2_unified.update_sentence_string()

    s1_empty = not bool(s1_str)
    s2_empty = not bool(s2_str)

    if s1_empty and s2_empty:
        return None, UnifStatus.SUCCESS
    elif s1_empty and not s2_empty:
        return Sentence(s2_str), UnifStatus.SUCCESS
    elif not s1_empty and s2_empty:
        return Sentence(s1_str), UnifStatus.SUCCESS
    else:
        return Sentence(s1_str + "|" + s2_str), UnifStatus.SUCCESS


def form_unifiers(s1: Sentence, s2: Sentence, matches: List[Tuple[int, int]]):
    unifiers = []
    # For each predicate match, form a separate unifier dictionary
    for m in matches:
        unif = {}
        for i, p1 in enumerate(s1.disjoint_literals[m[0]].parameters):
            p2 = s2.disjoint_literals[m[1]].parameters[i]
            # Unify variables to anything, but constants remain untouched
            if p1.is_var:
                if str(p1) != str(p2):
                    unif[str(p1)] = str(p2)
            elif p2.is_var:
                if str(p1) != str(p2):
                    unif[str(p2)] = str(p1)
        unifiers.append(unif)

    return unifiers


def unify_and_resolve(sent1: Sentence, sent2: Sentence) -> Tuple[Any, UnifStatus]:
    general_unifier: Dict[str, str] = {}
    predicate_matches: List[Tuple[int, int]] = []
    # Match predicates
    all_var_flag = True
    const_mismatch = False
    cross_match = False

    crosses: DefaultDict[int, List[int]] = defaultdict(list)
    # Go through each literal and find the ones are complimentary matches
    for i, lit1 in enumerate(sent1.disjoint_literals):
        for j, lit2 in enumerate(sent2.disjoint_literals):
            if lit1.predicate == lit2.predicate and lit1.negated != lit2.negated:
                # Check for existing match i.e. a "cross match"
                # When there are cross matches we have to do more work
                for match in predicate_matches:
                    if match[0] == i or match[1] == j:
                        cross_match = True
                        crosses[match[0]].append(match[1])
                        crosses[i].append(j)
                        predicate_matches.remove((match[0], match[1]))

                if not cross_match:
                    predicate_matches.append((i, j))

                # Set up unification of parameters
                for k in range(len(lit1.parameters)):
                    if lit1.parameters[k].is_var and not lit2.parameters[k].is_var:
                        if str(lit2.parameters[k]) not in general_unifier:
                            all_var_flag = False
                            if not cross_match:
                                general_unifier[str(lit1.parameters[k])] = str(
                                    lit2.parameters[k])
                    elif not lit1.parameters[k].is_var and lit2.parameters[k].is_var:
                        if str(lit2.parameters[k]) not in general_unifier:
                            all_var_flag = False
                            if not cross_match:
                                general_unifier[str(lit2.parameters[k])] = str(
                                    lit1.parameters[k])
                    elif lit1.parameters[k].is_var and lit2.parameters[k].is_var:
                        if str(lit1.parameters[k]) not in general_unifier and str(lit2.parameters[k]) not in general_unifier:
                            if str(lit1.parameters[k]) != str(lit2.parameters[k]):
                                if not cross_match:
                                    general_unifier[str(lit1.parameters[k])] = str(
                                        lit2.parameters[k])
                    else:  # Both compared parameters are constants
                        all_var_flag = False
                        if str(lit1.parameters[k]) != str(lit2.parameters[k]):
                            const_mismatch = True
                            break
            if const_mismatch:
                break
    # A perfect compliment is something like: ~A(x) and A(x)
    perfect_compliment = len(predicate_matches) == len(
        sent1.disjoint_literals) == 1
    imperfect_compliment = (all_var_flag and not perfect_compliment)

    if imperfect_compliment or const_mismatch:  # Failure
        return None, UnifStatus.FAIL

    # Cross match resolution strategy
    if cross_match:
        combos = []

        done: DefaultDict[Tuple[int, int], bool] = defaultdict(bool)
        # Form all possible combinations of cross matches
        for _ in range(len(crosses) * len(crosses[0])):
            available = [True for x in crosses]
            for l_index in crosses:
                for i, r_index in enumerate(crosses[l_index]):
                    if available[i] and not done[(l_index, r_index)]:
                        available[i] = False
                        done[(l_index, r_index)] = True
                        combos.append((l_index, r_index))
                        break

        # Form unifier dictionaries from combinations
        new_unifs = form_unifiers(sent1, sent2, combos)
        results = []
        # Try each combination
        for ind, p in enumerate(combos):
            p_matches = copy.deepcopy(predicate_matches)
            p_matches.append(p)
            unif = new_unifs[ind]

            result, status = resolve(
                sent1, sent2, p_matches, unif, perfect_compliment)
            # REVIEW If one fails, all fail
            if status == UnifStatus.FAIL:
                return None, UnifStatus.FAIL
            else:
                results.append(result)

        return (results), UnifStatus.MULTI

    else:
        # Remove complimentary matched predicates
        return resolve(sent1, sent2, predicate_matches, general_unifier, perfect_compliment)


def verify(s):
    old = copy.deepcopy(s)

    # Compact sentences that have somehow ended up with repeated predicates
    s.disjoint_literals = sorted(
        list(set(old.disjoint_literals)), key=lambda c: c.predicate)

    s.update_sentence_string()

    if len(s.disjoint_literals) > 0:
        return s
    else:
        return None


def update_kb(know_base, resultant_sentence):
    # Update the knowledge base with new sentence
    resultant_sentence = verify(resultant_sentence)

    if not resultant_sentence:
        return False
    in_kb_flag = False
    for s in know_base:
        if str(s) == str(resultant_sentence):
            in_kb_flag = True
    # Avoid adding duplicates
    if not in_kb_flag:
        know_base.append(resultant_sentence)
        return True
    return False


def prove_by_resolution(k_base: List[Sentence], query: Literal) -> bool:
    iterations = last = progress_counter = 0
    # Negate query, convert to sentence, and add it to knowledge base
    not_query = Sentence(query.copy().negate().update_lit_string())
    know_base = copy.deepcopy(k_base)
    know_base = [not_query] + know_base

    tried_pairs: Dict[Tuple[str, str], bool] = {}
    t_index = 0
    s_index = 1

    while True:
        iterations += 1
        # Maximum number of combinations we can possibly try
        saturated = len(know_base) * (len(know_base) - 1)
        if len(tried_pairs) % 2 != 0:  # This shouldn't occur! Pairs are added... well... in pairs
            raise ValueError("Invalid pair size!")
        if len(tried_pairs) >= saturated:
            print("[!] Tried all combinations! Query must be false.")
            return False

        try_resolve = True
        resolved_flag = False

        target_sentence = know_base[t_index]
        current_sentence = know_base[s_index]

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

        if resolved_flag or s_index == t_index:
            try_resolve = False

        if try_resolve:
            # Look for complimentary matching predicates
            for cur_lit in current_sentence.disjoint_literals:
                breakout = False
                for tar_lit in target_sentence.disjoint_literals:
                    if cur_lit.predicate == tar_lit.predicate and cur_lit.negated != tar_lit.negated:

                        result, status = unify_and_resolve(
                            current_sentence, target_sentence)
                        if status == UnifStatus.SUCCESS:
                            t_str = "[TARGET] " + str(target_sentence)
                            m_str = "[MATCH] " + str(current_sentence)
                            r_str = "[RESULT] " + str(result)
                            match_str = t_str + "\n" + m_str + "\n" + r_str + "\n\n"

                            # Used in case we want to write results to file
                            MATCHES.append(match_str)

                            if not result:  # Great success!
                                print(
                                    "[!] Contradiction found! Query is consistent with knowledge base.")
                                return True

                            ResGraph.add(current_sentence,
                                         target_sentence, result)
                            updated = update_kb(know_base, result)

                            if updated:
                                progress_counter += 1
                                diff = iterations - last
                                last = iterations

                                if diff >= CUTOFF:
                                    print("[!] Infinite loop detected.")
                                    return False

                            t_index = 0
                            s_index = 0

                            breakout = True
                            know_base = sorted(
                                know_base, key=lambda s:
                                len(s.disjoint_literals))
                            break
                        elif status == UnifStatus.MULTI:
                            # Multiple sentences returned
                            for r in result:
                                update_kb(know_base, r)
                                ResGraph.add(current_sentence,
                                             target_sentence, r)
                                t_index = 0
                                s_index = 0

                                breakout = True
                                know_base = sorted(
                                    know_base, key=lambda s:
                                    len(s.disjoint_literals))

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


def write_matches(ind=1):
    path = "match_logs/matches_input%dquery%d.txt" % (FILE_INDEX, ind)
    print("[!] Saving match output to:", path)
    with open(path, "w") as f:
        for k in k_base:
            f.write(str(k) + "\n")
        f.write(str(len(MATCHES)) + "\n")
        for m in MATCHES:
            f.write(m)


if __name__ == "__main__":
    CUTOFF = 100000
    for FILE_INDEX in range(1, 12):
        print("======= INPUT " + str(FILE_INDEX) + " =========")
        queries, k_base = parse_input("cases/input%d.txt" % FILE_INDEX)
        print("[!] %d queries and %d sentences" % (len(queries), len(k_base)))
        ResGraph = ResolutionGraph(FILE_INDEX)
        results = []

        ind = 0
        # Try each query
        for q in queries:
            ind += 1
            MATCHES: List[str] = []
            print("=>", q)
            printk(k_base)
            if prove_by_resolution(k_base, q):
                results.append("TRUE")
            else:
                results.append("FALSE")
            write_matches(ind)
            ResGraph.save()
            ResGraph = ResGraph.next_query()
        # Output results
        with open("output/output%d.txt" % FILE_INDEX, "w") as f:
            for r in results:
                f.write(r + "\n")
