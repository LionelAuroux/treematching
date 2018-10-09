# treematching

Allow you to match any python tree hiearchy with python matching objects.

An EDSL (Embedded Domain Specific Language) in python provide you some objects (Type, Attrs, List, Dict, ...) and you write a pattern
with it to match python data.

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
