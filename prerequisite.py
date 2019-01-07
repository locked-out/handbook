'''
ISSUES:
 -  Differentiate between
                80 WAM in COMP  or  SENG courses
        80 WAM in COMP courses  or  in final year
    Solution:
    Second example will likely only occur instead as
        80 WAM in COMP courses, or  in final year
    Use comma to mark the end of "in" keyword
    OR
    Use an actual logical statement parser:
        http://www.aclweb.org/anthology/P86-1013
        https://homes.cs.washington.edu/~lsz/papers/zc-uai05.pdf
        https://www.nltk.org/book/ch10.html
'''


import re


class tcol:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Classes for course graph

courses = {}


class Course:
    def __init__(self, code, prerequisite=None):
        self.code = code
        self.prerequisite = prerequisite

    def __repr__(self):
        return f'<Course {self.code}>'

    def how(self, done=[], depth=0):
        if self.prerequisite:
            print('  ' * depth + f'{tcol.OKGREEN}{self.code}{tcol.ENDC}')
            print('  ' * depth + str(self.prerequisite))
            print()

            for course in self.prerequisite.getCourses():
                if course not in done:
                    course.how(done, depth + 1)


class Prerequisite:
    def __init__(self, condition, course=None):
        self.condition = condition
        self.course = course

    def __str__(self):
        return self.condition

    def __repr__(self):
        return self.condition

    def collapse(self):
        return self

    def getCourses(self):
        return [self.course] if self.course else []

    def eval(self, doneCourses):
        if self.course:
            return self.course in doneCourses
        return True


class CompoundPrereq(Prerequisite):
    def __init__(self, *nodes):
        self.nodes = list(nodes)

    def __str__(self):
        return f'{tcol.HEADER}({tcol.ENDC}' + f' {tcol.OKBLUE}{self.op}{tcol.ENDC} '.join(map(str, self.nodes)) + f'{tcol.HEADER}){tcol.ENDC}'

    def __repr__(self):
        return '(' + f' {self.op} '.join(map(repr, self.nodes)) + ')'

    def collapse(self):
        for node in self.nodes:
            node.collapse()
            if isinstance(node, CompoundPrereq) and node.op == self.op:
                self.nodes.remove(node)
                self.nodes.extend(node.nodes)
        return self

    def getCourses(self):
        out = []
        for node in self.nodes:
            out.extend(node.getCourses())
        return out


class PrereqAnd(CompoundPrereq):
    op = "and"

    def eval(self, doneCourses):
        return all([i.eval(doneCourses) for i in self.nodes])


class PrereqOr(CompoundPrereq):
    op = "or"

    def eval(self, doneCourses):
        return any([i.eval(doneCourses) for i in self.nodes])


def tokenise(string, operators):
    tokens = []
    splits = []
    pattern = "|".join(operators)
    for m in re.finditer(pattern, string):
        splits.extend(m.span())

    start = 0
    for split in splits:
        subs = string[start:split].strip()
        if subs:
            tokens.append(subs)
        start = split
    subs = string[start:].strip()
    if subs:
        tokens.append(subs)
    return tokens


# Merges any decorative brackets: any brackets without conjunction either side
def cleanBrackets(tokens):
    out = tokens.copy()
    stack = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token == '(' or token == '[':
            stack.append(i)
        elif token == ')' or token == ']':
            match = stack.pop()
            if (match != 0 and tokens[match - 1] not in ('and', 'or', ',')):
                # if (i + 1 == len(tokens) or tokens[i + 1] not in ('and', 'or', ',')):
                lower = max(0, match - 1)
                upper = i
                if i + 1 < len(tokens):
                    upper = i + 1 if tokens[i + 1] not in nops else i
                conjoinedToken = ' '.join(tokens[lower:upper + 1])
                tokens[lower] = conjoinedToken
                for j in range(upper, lower, -1):
                    tokens.pop(j)
        i += 1
    return tokens


# Turns ', and' tokens into ') and ('
def cleanCommas(tokens):
    out = ['(']
    for i, token in enumerate(tokens):
        if token == ',' and i + 1 < len(tokens) and tokens[i + 1] in ('and', 'or'):
            out.extend((')', tokens.pop(i + 1), '('))
        else:
            out.append(token)
    out.append(')')
    return out


# Convert in-order tokens into postfix form
def shunt(tokens):
    out = []
    stack = []
    for token in tokens:
        if token == 'or' or token == 'and' or token == ',':
            stack.append(token)
        elif token == '(' or token == '[':
            stack.append(token)
        elif token == ')' or token == ']':
            top = stack.pop()
            while top != '(' and top != '[':
                out.append(top)
                top = stack.pop()
        else:
            out.append(token)

    while len(stack) > 0:
        out.append(stack.pop())

    return out


# Expand commas in postfix form
# "1 2 3 or ," become "1 2 3 or or"
def expandCommas(tokens):
    for i, token in enumerate(tokens):
        if token == ',':
            if tokens[i - 1] in ('and', 'or'):
                tokens[i] = tokens[i - 1]
            else:
                tokens[i] = 'and'
    return tokens


def printToks(tokens):
    for t in tokens:
        if t in nops:
            print(tcol.OKBLUE + t + tcol.ENDC, end=' ')
        else:
            print(tcol.UNDERLINE + t + tcol.ENDC, end=' ')
    print()


def formPrereqTree(tokens):
    stack = []
    for token in tokens:
        if token == "or" or token == "and":
            top1, top2 = stack.pop(), stack.pop()
            newNode = PrereqOr(top2, top1) if token == "or" else PrereqAnd(top2, top1)
            stack.append(newNode)
        else:
            prereq = Prerequisite(token)
            code = re.search(r"[a-zA-Z]{4}\d{4}", token)
            if code:
                code = code.group(0).upper()
                if code not in courses:
                    courses[code] = Course(code)
                prereq.course = courses[code]
            stack.append(prereq)

    if len(stack) != 1:
        print("Stack error", stack)
        return None
    return stack[0]

ops = ['(?<=\W)or(?=\W)', '(?<=\W)and(?=\W)', '\[', '\]', '\(', '\)', ',']
nops = ['or', 'and', '[', ']', '(', ')', ',']
with open("prerequisites.txt") as f:
    for line in f:
        subj, prereq = line.strip().rstrip(".").split('=', 1)
        extras = None
        try:
            prereq, extras = prereq.split('.', 1)
        except ValueError:
            try:
                prereq, extras = prereq.split(';', 1)
            except ValueError:
                pass
        if extras:
            print(tcol.WARNING + "extras  " + tcol.ENDC, end=' | ')
            print(extras)
        tokens = tokenise(prereq, ops)
        print(tcol.OKGREEN + subj + tcol.ENDC, end=' | ')
        printToks(tokens)

        tokens = cleanBrackets(tokens)
        tokens = cleanCommas(tokens)
        print(tcol.HEADER + "cleaned " + tcol.ENDC, end=' | ')
        printToks(tokens)

        shunted = shunt(tokens)
        print(tcol.HEADER + "shunted " + tcol.ENDC, end=' | ')
        printToks(shunted)

        shunted = expandCommas(shunted)
        print(tcol.HEADER + "expand  " + tcol.ENDC, end=' | ')
        printToks(shunted)

        tree = formPrereqTree(shunted)

        if tree:
            print(tcol.HEADER + "tree    " + tcol.ENDC, end=' | ')
            print(tree)

            tree.collapse()
            print(tcol.HEADER + "collapse" + tcol.ENDC, end=' | ')
            print(tree)

            if subj not in courses:
                courses[subj] = Course(subj)
            course = courses[subj]
            course.prerequisite = tree

        print()

print(" ".join(sorted(courses.keys())))

line = input('>')
while line:
    line = line.upper()
    done = [courses[i] for i in line.split(" ") if i in courses]
    print(f"{tcol.OKGREEN}Counted:{tcol.ENDC}", ' '.join([i.code for i in done]))
    for name, course in courses.items():
        if course.prerequisite and course.prerequisite.eval(done):
            # print(course.code)
            course.how(courses.values())
    line = input('>')
