class Tree:
    def __init__(self, name="root", data=None, children=[]):
        self.name = name
        self._data = data
        self.children = []
        for child in children:
            self.add_child(child)

    def __repr__(self):
        return self.name

    def add_child(self, node):
        self.children.append(node)

    def get_child(self, name):
        for child in self.children:
            if child.name == name:
                return child

    @property
    def data(self):
        """The data property."""
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

