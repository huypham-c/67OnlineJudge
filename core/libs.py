import operator
from typing import Any, Callable, List

class PriorityQueue:
    """
    Queue that brings the element with the highest priority to the front 
    using a Max-Heap data structure.

    It assumes that elements inserted are tuples where the first item (index 0) 
    is the priority score.

    Parameters
    ----------
    comparator : Callable, optional
        A function to define how to compare two priority keys. 
        Defaults to operator.lt.
    """

    def __init__(self, comparator: Callable = operator.lt):
        self.__heap = []
        self.__comparator = comparator

    def __len__(self) -> int:
        """
        Get the current number of elements in the queue.

        Returns
        -------
        int
            The size of the priority queue.
        """
        return len(self.__heap)

    def insert(self, entry: tuple):
        """
        Add a new element to the priority queue.

        Parameters
        ----------
        entry : tuple
            A tuple where the first element is the priority score.
        """
        self.__heap.append(entry)
        idx = len(self.__heap) - 1
        while idx > 0:
            parent_idx = (idx - 1) // 2
            if self.__comparator(self.__heap[parent_idx][0], self.__heap[idx][0]):
                self.__heap[parent_idx], self.__heap[idx] = self.__heap[idx], self.__heap[parent_idx]
                idx = parent_idx
            else:
                break

    def pop(self) -> tuple:
        """
        Extract the front element (highest priority).

        Returns
        -------
        tuple
            The element with the highest priority.

        Raises
        ------
        IndexError
            If the priority queue is empty.
        """
        if not self.__heap:
            raise IndexError('Pop from empty priority queue')
        
        if len(self.__heap) == 1:
            return self.__heap.pop()

        return_val = self.__heap[0]
        self.__heap[0] = self.__heap.pop()

        idx = 0
        n = len(self.__heap)
        while idx < n:
            chosen_idx = idx
            left_idx = 2 * idx + 1
            right_idx = 2 * idx + 2
            
            if left_idx < n and self.__comparator(self.__heap[chosen_idx][0], self.__heap[left_idx][0]):
                chosen_idx = left_idx
            if right_idx < n and self.__comparator(self.__heap[chosen_idx][0], self.__heap[right_idx][0]):
                chosen_idx = right_idx

            if chosen_idx == idx:
                break

            self.__heap[chosen_idx], self.__heap[idx] = self.__heap[idx], self.__heap[chosen_idx]
            idx = chosen_idx

        return return_val


class BST:
    """
    Binary Search Tree supporting generic comparable data.

    Parameters
    ----------
    comparator : Callable, optional
        A function to define how to compare two nodes. 
        Defaults to operator.lt (less than).
    """
    
    class _node:
        """
        Internal class representing a node containing generic data.

        Parameters
        ----------
        data : Any
            The data to be stored in the node.
        """
        def __init__(self, data: Any, color: bool = True):
            self.data = data
            self.color = color
            self.left = None
            self.right = None
            self.parent = None

    def __init__(self, comparator: Callable = operator.lt):
        self.NIL = self._node(data=None, color=False)
        self.root = self.NIL
        self.comparator = comparator
    
    def _transplant(self, u: _node, v: _node):
        if u.parent == None:
            self.root = v
        elif u == u.parent.left:
            u.parent.left = v
        else:
            u.parent.right = v
        v.parent = u.parent

    def _rotate_left(self, node: _node):
        right_child = node.right
        node.right = right_child.left
        if right_child.left != self.NIL:
            right_child.left.parent = node

        self._transplant(node, right_child)

        right_child.left = node
        node.parent = right_child

    def _rotate_right(self, node: _node):
        left_child = node.left
        node.left = left_child.right
        if left_child.right != self.NIL:
            left_child.right.parent = node

        self._transplant(node, left_child)

        left_child.right = node
        node.parent = left_child

    def _fix_insert(self, node: _node):
        while node.parent.color:
            if node.parent == node.parent.parent.left:
                unc = node.parent.parent.right
                if unc.color:
                    node.parent.color = False
                    unc.color = False
                    node.parent.parent.color = True
                    node = node.parent.parent
                else:
                    if node == node.parent.right:
                        node = node.parent
                        self._rotate_left(node)

                    node.parent.color = False
                    node.parent.parent.color = True
                    self._rotate_right(node.parent.parent)

            else:
                unc = node.parent.parent.left
                if unc.color:
                    node.parent.color = False
                    unc.color = False
                    node.parent.parent.color = True
                    node = node.parent.parent
                else:
                    if node == node.parent.left:
                        node = node.parent
                        self._rotate_right(node)

                    node.parent.color = False
                    node.parent.parent.color = True
                    self._rotate_left(node.parent.parent)

            if node == self.root:
                break

        self.root.color = False

    def insert(self, data: Any):
        """
        Add new data into the tree.

        Parameters
        ----------
        data : Any
            The data to be inserted.
        """
        node = self._node(data, color=True)
        node.parent = None
        node.left = self.NIL
        node.right = self.NIL

        y = None
        x = self.root

        while x != self.NIL:
            y = x
            if self.comparator(node.data, x.data):
                x = x.left
            else:
                x = x.right

        node.parent = y
        if y is None:
            self.root = node
        elif self.comparator(node.data, y.data):
            y.left = node
        else:
            y.right = node

        if node.parent is None:
            node.color = False
            return
        if node.parent.parent is None:
            return 
        
        self._fix_insert(node)

    def _search(self, node, data: Any) -> _node:
        if node is self.NIL or node.data == data:
            return node
        elif self.comparator(node.data, data):
            return self._search(node.right, data)
        else:
            return self._search(node.left, data)

    def search(self, data: Any) -> _node:
        """
        Search for a specific element in the tree.

        Parameters
        ----------
        data : Any
            The data to search for.

        Returns
        -------
        _node
            Return the node contains the data, return NIL node otherwise
        """
        return self._search(self.root, data)
    
    def _fix_delete(self, node: _node):
        while node != self.root and node.color == False:
            if node == node.parent.left:
                sibling = node.parent.right
                if sibling.color:
                    sibling.color = False
                    node.parent.color = True
                    self._rotate_left(node.parent)
                    sibling = node.parent.right
                else:
                    if not sibling.right.color:
                        if not sibling.left.color:
                            sibling.color = True
                            node = node.parent
                        else:
                            sibling.left.color = False
                            sibling.color = True
                            self._rotate_right(sibling)
                            sibling = node.parent.right
                    else:
                        sibling.color = node.parent.color
                        node.parent.color = False
                        sibling.right.color = False
                        self._rotate_left(node.parent)
                        node = self.root
            else:
                sibling = node.parent.left
                if sibling.color:
                    sibling.color = False
                    node.parent.color = True
                    self._rotate_right(node.parent)
                    sibling = node.parent.left
                else:
                    if not sibling.left.color:
                        if not sibling.right.color:
                            sibling.color = True
                            node = node.parent
                        else:
                            sibling.right.color = False
                            sibling.color = True
                            self._rotate_left(sibling)
                            sibling = node.parent.left
                    else:
                        sibling.color = node.parent.color
                        node.parent.color = False
                        sibling.left.color = False
                        self._rotate_right(node.parent)
                        node = self.root
        node.color = False

    def _delete(self, node: _node):
        y = node
        y_color = node.color

        if node.left == self.NIL:
            x = node.right
            self._transplant(node, node.right)
        elif node.right == self.NIL:
            x = node.left
            self._transplant(node, node.left)
        else:
            y = node.right
            while y.left != self.NIL:
                y = y.left
            y_color = y.color
            x = y.right

            if y.parent == node:
                x.parent = y #Because of the common NIL node bs
            else:
                self._transplant(y, y.right)
                y.right = node.right
                y.right.parent = y

            self._transplant(node, y)
            y.left = node.left
            y.left.parent = y
            y.color = node.color

        if not y_color:
            self._fix_delete(x)

    def delete(self, data: Any) -> bool:
        """
        Delete a node contains the data

        Parameters
        ----------
        data: Any
            The data to delete from the tree.

        Returns
        -------
        bool
            True if deletion is successful, False otherwise
        """
        
        node = self.search(data)
        
        if node == self.NIL:
            return False
        self._delete(node)
        return True

    def _inorder(self, node, result: List[Any]):
        if node != self.NIL:
            self._inorder(node.right, result)
            result.append(node.data)
            self._inorder(node.left, result)

    def get_sorted_elements(self) -> List[Any]:
        """
        Retrieve all elements in the tree in sorted order.

        Returns
        -------
        List[Any]
            A list containing all the sorted elements.
        """
        result = []
        self._inorder(self.root, result)
        return result
    


