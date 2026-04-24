import operator
from typing import Any, Callable, List

class FastString(str):
    """
    String that uses the Rabin-Karp algorithm for fast substring matching, 
    inherited from Python's built-in str.
    """

    def __contains__(self, key: str) -> bool:
        """
        Check if a substring exists within the string using Rabin-Karp.

        Parameters
        ----------
        key : str
            The substring to search for.

        Returns
        -------
        bool
            True if the substring is found, False otherwise.
        """
        n = len(self)
        m = len(key)

        if m == 0: 
            return True
        if m > n:
            return False
        
        log_base = 8
        mask = 0xFFFFFFFF

        p_hash = 0
        t_hash = 0

        for i in range(m):
            p_hash = ((p_hash << log_base) + ord(key[i])) & mask
            t_hash = ((t_hash << log_base) + ord(self[i])) & mask

        for i in range(n - m + 1):
            if p_hash == t_hash:
                if self[i:i + m] == key:
                    return True
            if i < n - m:
                t_hash = ((t_hash - (ord(self[i]) << (log_base * (m - 1))) << log_base) + ord(self[i + m])) & mask
        
        return False
    

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
        def __init__(self, data: Any):
            self.data = data
            self.left = None
            self.right = None

    def __init__(self, comparator: Callable = operator.lt):
        self.root = None
        self.comparator = comparator

    def _insert(self, node, data: Any):
        if node is None:
            return self._node(data)
        elif node.data == data:
            return node
        elif self.comparator(node.data, data):
            node.right = self._insert(node.right, data)
        else:
            node.left = self._insert(node.left, data)
        return node

    def insert(self, data: Any):
        """
        Add new data into the tree.

        Parameters
        ----------
        data : Any
            The data to be inserted.
        """
        self.root = self._insert(self.root, data)

    def _search(self, node, data: Any) -> bool:
        if node is None:
            return False
        if node.data == data:
            return True
        elif self.comparator(node.data, data):
            return self._search(node.right, data)
        else:
            return self._search(node.left, data)

    def search(self, data: Any) -> bool:
        """
        Search for a specific element in the tree.

        Parameters
        ----------
        data : Any
            The data to search for.

        Returns
        -------
        bool
            True if the data exists in the tree, False otherwise.
        """
        return self._search(self.root, data)

    def _delete(self, node, data):
        if node is None:
            return None

        if node.data == data: 
            if node.left is None:
                return node.right
            if node.right is None:
                return node.left
            
            replacement = node.right

            while replacement is not None and replacement.left is not None:
                replacement = replacement.left
            
            node.data = replacement.data
            node.right = self._delete(node.right, replacement.data)

        elif self.comparator(node.data, data):
            node.right = self._delete(node.right, data)
        else:
            node.left = self._delete(node.left, data)

        return node

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
        
        if not self.search(data):
            return False
            
        self.root = self._delete(self.root, data)
        return True

    def _inorder(self, node, result: List[Any]):
        if node is not None:
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