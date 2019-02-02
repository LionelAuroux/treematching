#!/usr/bin/env python3
"""
25 minutes de conf

------------
    comparatively easily 
    techniques, could (virgules à enlever)
    explainning (un seul N)
    how behavior treeS work
    how to adapth THEM
------------


expliquez les behaviors Tree:
- forme d'automate + simple pour mixer les states de manière moins formel et moins lourde programmatiquement

+ status de la tache: FAIL, SUCCESS, RUNNING
    Décrit de manière synchrone des processus qui peuvent être asynchrone
+ 3 concepts:
    - Task
    - Sequence: Each
    - Selector: Any
+ Bonne abstraction

BT stocke la structure:
    pour le matching, il faut stocker les positions et le status

- BT pour matching, exemple avec une string

1 + 2 * 3

Seq(
    Seq(
        Num,
        Selector(
            Seq(
                '*',
                Num
            ),
            True
        )
    ),
    Selector(
        Seq(
            '+',
            Seq(
                Num,
                Selector(
                    Seq(
                        '*',
                        Num
                    ),
                    True
                )
            ),
        ),
        True
    )
)

Task Expr:
Selector(
    Num,
    Seq(Expr, '+', Expr),
    Seq(Expr, '*', Expr),
)

1 + 2 * 3
^
Task Expr:
Selector(
    Num, // success
    Seq(Expr, '+', Expr), // running
    Seq(Expr, '*', Expr), // running
)

1 + 2 * 3
  ^
Task Expr:
Selector(
    Num, // fail
    Seq(Expr, '+', Expr), // running
    Seq(Expr, '*', Expr), // fail
)

1 + 2 * 3
    ^
Task Expr:
Selector(
    Num, // success
    Seq(Expr, '+', Expr), // running
    Seq(Expr, '*', Expr), // running
)

// matching

- Séparation de la structure du BT, et des états de matching

1 pattern = 1 BT

- Matching d'arbre

Top-Down

Bottom-Up

Tree rewrite

Exemples à base du module "treematching"

"""

from copy import copy
from enum import IntEnum

Status = IntEnum('Status', ['Failure', 'Success', 'Running'])

class Task:
    def tick(self, udata) -> Status:
        return Status.Success

class Tree:
    def __init__(self, *child):
        self.child = child

class Selector(Tree):
    def tick(self, udata) -> Status:
        for child in self.child:
            childstatus = child.tick(udata)
            if childstatus == Status.Running:
                return Status.Running
            elif childstatus == Status.Success:
                return Status.Success
        return Status.Failure

class Sequence(Tree):
    def tick(self, udata) -> Status:
        for child in self.child:
            print("TCH %d" % id(child))
            childstatus = child.tick(udata)
            if childstatus == Status.Running:
                return Status.Running
            elif childstatus == Status.Failure:
                return Status.Failure
        return Status.Success

class Try(Tree):
    def tick(self, udata) -> Status:
        for child in self.child:
            while True:
                status = child.tick(udata)
                if status != Status.Running:
                    break

class Until(Tree):
    def tick(self, udata) -> Status:
        status = Status.Success
        while status == Status.Success:
            status = self.child.tick(udata)
            if status != Status.Running:
                break
        return status

class Parallel(Tree):
    def tick(self, udata) -> Status:
        if not hasattr(self, 'udatas'):
            self.udatas = [None] * len(self.child)
            self.status = [Status.Running] * len(self.child)
            for idx in range(len(self.udatas)):
                self.udatas[idx] = copy(udata)
        for idx, child in enumerate(self.child):
            if self.status[idx] == Status.Running:
                self.status[idx] = child.tick(self.udatas[idx])
        if not sum(map(lambda _: _ == Status.Running, self.status)):
            if sum(map(lambda _: _ == Status.Success, self.status)):
                return Status.Success
            return Status.Failure
        return Status.Running

# udata.src
# udata.len
# udata.pos

class ReadNum(Task):
    def tick(self, udata) -> Status:
        if udata.pos == udata.len:
            return Status.Success
        print("Test %s" % udata.src[udata.pos])
        if udata.src[udata.pos].isdigit():
            print("INC")
            udata.pos += 1
            return Status.Running
        return Status.Failure

class ReadOp(Task):
    def __init__(self, op):
        self.op = op
    
    def tick(self, udata) -> Status:
        if udata.pos == udata.len:
            return Status.Success
        l = len(self.op)
        sub = udata.src[udata.pos : udata.pos + l]
        print("Test OP %s" % sub)
        if sub == self.op:
            udata.pos += l
            print("INC %d" % l)
            return Status.Running
        return Status.Failure

bt = Try(
        Sequence(
            Try(ReadNum()),
            ReadOp('+'),
            Try(ReadNum())
        )
    )
class P: pass
d = P()
d.src = "1+23"
d.len = len(d.src)
d.pos = 0

bt.tick(d)
