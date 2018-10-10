# treematching

Using natural python reflixivity, all python data structures could be seen as trees of python objects.

The module **treematching** allow you to write patterns to match subtrees in any trees of python objects.

This could be usefull for trees coming from parsing (AST) but in a more common ways, from any trees coming from anywhere (JSON, DB, ...).

**treematching** provide you some objects (Type, Attrs, List, Dict, ...) to write your patterns.

For example:

```python
bt = Type('A',
            Attrs(
                Attr('c', Type('str', Value('lala'))),
                Attr('b', Type('str', Value('toto'))),
                Attr('a', Type('int', Value(32))),
            )
    )
e = MatchingBTree(bt)

tree = [B(a=32, b='toto', c='lala'), A(a=32, b='toto', c='lala')]

match = e.match(tree)
```
