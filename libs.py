import operator
import random

class FastString(str):
    """String that used Rabin Karp algorithm for fast substring matching, inherited from Python's str"""
    def __contains__(self, key: str) -> bool:
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
    """Queue that take the element with highest priority to the front of the queue"""
    def __init__(self, comparator = operator.lt):
        self.__heap = []
        self.__comparator = comparator

    def __len__(self):
        return len(self.__heap)

    def insert(self, entry):
        """Add a new element to the priority queue"""
        self.__heap.append(entry)
        idx = len(self.__heap) - 1
        while idx > 0:
            parent_idx = (idx - 1) // 2
            if self.__comparator(self.__heap[parent_idx][0], self.__heap[idx][0]):
                self.__heap[parent_idx], self.__heap[idx] = self.__heap[idx], self.__heap[parent_idx]
                idx = parent_idx
            else:
                break

    def pop(self):
        """Take the front element out and return that element"""
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
            if left_idx < n and self.__comparator(self.__heap[chosen_idx], self.__heap[left_idx]):
                chosen_idx = left_idx
            if right_idx < n and self.__comparator(self.__heap[chosen_idx], self.__heap[right_idx]):
                chosen_idx = right_idx

            if chosen_idx == idx:
                break

            self.__heap[chosen_idx], self.__heap[idx] = self.__heap[idx], self.__heap[chosen_idx]
            idx = chosen_idx

        return return_val

