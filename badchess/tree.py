from typing import Optional


class Tree:
    def __init__(self, name="root", strength=0, children=[]):
        self.name = name
        self._strength = strength
        self.children: list["Tree"] = []
        for child in children:
            self.add_child(child)

    def __repr__(self):
        return f"({self.name} with {len(self.children)} children), strength: {self._strength}"

    def display_tree(self):
        return self._display_tree()

    def _display_tree(self, depth=0, current_depth=0):
        indent = current_depth * "\t"

        if not self.children:
            return f"{indent}{current_depth} {self.__repr__()}"
        else:
            return f"{indent}{current_depth} {self.__repr__()}\n" + f"\n".join(
                [
                    child._display_tree(depth=depth, current_depth=current_depth + 1)
                    for child in self.children
                ]
            )

    def add_child(self, node: "Tree"):
        self.children.append(node)

    def get_child(self, name) -> Optional["Tree"]:
        for child in self.children:
            if child.name == name:
                return child

    @property
    def strength(self) -> float:
        """The strength property."""
        return self._strength

    @strength.setter
    def strength(self, value: float):
        self._strength = value

    def n_nodes(self) -> int:
        if not self.children:
            return 1
        else:
            return 1 + sum([child.n_nodes() for child in self.children])
