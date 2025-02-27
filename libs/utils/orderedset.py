from collections import OrderedDict
from collections.abc import MutableSet
from typing import Any, Iterable, Iterator, Optional, TypeVar

_T = TypeVar("_T")


class OrderedSet(MutableSet[_T]):
    def __init__(self, iterable: Optional[Iterable[_T]] = None) -> None:
        self._d: OrderedDict[_T, None] = (
            OrderedDict((element, None) for element in iterable)
            if iterable
            else OrderedDict()
        )

    def update(self, *args: Iterable[_T], **kwargs: Any) -> None:
        if kwargs:
            raise TypeError("update() takes no keyword arguments")

        for s in args:
            for e in s:
                self.add(e)

    def add(self, elem: _T) -> None:
        self._d[elem] = None

    def discard(self, elem: _T) -> None:
        self._d.pop(elem, None)

    def __contains__(self, x: object) -> bool:
        return x in self._d

    def __iter__(self) -> Iterator[_T]:
        for ele in self._d:
            yield ele

    def __len__(self) -> int:
        return len(self._d)

    def __repr__(self) -> str:
        return "OrderedSet([%s])" % (", ".join(map(repr, self._d.keys())))

    def __str__(self) -> str:
        return "{%s}" % (", ".join(map(repr, self._d.keys())))
