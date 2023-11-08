class Tree:
    def __init__(self, name="root", strength=None, children=[]):
        self.name = name
        self._strength = strength
        self.children = []
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

    def add_child(self, node):
        self.children.append(node)

    def get_child(self, name):
        for child in self.children:
            if child.name == name:
                return child

    @property
    def strength(self):
        """The strength property."""
        return self._strength

    @strength.setter
    def strength(self, value):
        self._strength = value

    def n_nodes(self):
        if not self.children:
            return 1
        else:
            return 1 + sum([child.n_nodes() for child in self.children])
