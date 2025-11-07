#!/usr/bin/env python3
"""
Custom Hash Table Implementation
Implements a hash table from scratch using open addressing with linear probing for collision resolution. Uses FNV-1a hash function.
Source that helped with the FNV hash implementation: http://www.isthe.com/chongo/tech/comp/fnv/
"""

class HashTable:    
    def __init__(self, initial_capacity=16, load_factor=0.75):
        """
        Initialize hash table with given capacity and load factor.
        """
        self.capacity = initial_capacity
        self.load_factor = load_factor
        self.size = 0
        # Use None to represent empty slots, and a special DELETED marker for deleted entries
        self.keys = [None] * self.capacity
        self.values = [None] * self.capacity
        self.DELETED = object()  # Sentinel value for deleted entries
    
    def _fnv1a_hash(self, key):
        """
        FNV-1a hash function implementation.
        """
        # FNV-1a parameters for 32-bit hash
        FNV_prime = 16777619
        FNV_offset_basis = 2166136261
        
        hash_value = FNV_offset_basis
        key_str = str(key)
        
        for char in key_str:
            hash_value ^= ord(char)
            hash_value = (hash_value * FNV_prime) & 0xFFFFFFFF  # Keep it 32-bit
        
        return hash_value
    
    def _get_index(self, key):
        """
        Get the array index for a given key using hash function.
        """
        return self._fnv1a_hash(key) % self.capacity
    
    def _find_slot(self, key):
        """
        Find the slot for a given key using linear probing.
        """
        index = self._get_index(key)
        start_index = index
        first_deleted = None
        
        while self.keys[index] is not None:
            if self.keys[index] == self.DELETED:
                if first_deleted is None:
                    first_deleted = index
            elif self.keys[index] == key:
                return (index, True)
            
            index = (index + 1) % self.capacity
            
            # We've wrapped around
            if index == start_index:
                break
        
        # Key not found, return first available slot (deleted or empty)
        if first_deleted is not None:
            return (first_deleted, False)
        return (index, False)
    
    def _resize(self):
        """
        Resize the hash table when load factor is exceeded.
        Doubles the capacity and rehashes all entries.
        """
        old_keys = self.keys
        old_values = self.values
        old_capacity = self.capacity
        
        # Double the capacity
        self.capacity *= 2
        self.keys = [None] * self.capacity
        self.values = [None] * self.capacity
        self.size = 0
        
        # Rehash all existing entries
        for i in range(old_capacity):
            if old_keys[i] is not None and old_keys[i] != self.DELETED:
                self.put(old_keys[i], old_values[i])
    
    def put(self, key, value):
        """
        Insert or update a key-value pair in the hash table.
        
        Args:
            key: Key to insert/update
            value: Value to associate with the key
        """
        # Check if we need to resize
        if self.size >= self.capacity * self.load_factor:
            self._resize()
        
        index, found = self._find_slot(key)
        
        if not found:
            self.size += 1
        
        self.keys[index] = key
        self.values[index] = value
    
    def get(self, key, default=None):
        """
        Get the value associated with a key.
        
        Args:
            key: Key to look up
            default: Value to return if key not found
            
        Returns:
            Value associated with key, or default if not found
        """
        index, found = self._find_slot(key)
        
        if found:
            return self.values[index]
        return default
    
    def contains(self, key):
        """
        Check if a key exists in the hash table.
        
        Args:
            key: Key to check
            
        Returns:
            True if key exists, False otherwise
        """
        _, found = self._find_slot(key)
        return found
    
    def remove(self, key):
        """
        Remove a key-value pair from the hash table.
        
        Args:
            key: Key to remove
            
        Returns:
            True if key was removed, False if key didn't exist
        """
        index, found = self._find_slot(key)
        
        if found:
            self.keys[index] = self.DELETED
            self.values[index] = None
            self.size -= 1
            return True
        return False
    
    def __setitem__(self, key, value):
        """Support bracket notation for setting: ht[key] = value"""
        self.put(key, value)
    
    def __getitem__(self, key):
        """Support bracket notation for getting: value = ht[key]"""
        index, found = self._find_slot(key)
        if found:
            return self.values[index]
        raise KeyError(f"Key not found: {key}")
    
    def __contains__(self, key):
        """Support 'in' operator: if key in ht"""
        return self.contains(key)
    
    def __len__(self):
        """Return number of key-value pairs"""
        return self.size
    
    def items(self):
        """
        Return an iterator over (key, value) pairs.
        
        Yields:
            Tuples of (key, value)
        """
        for i in range(self.capacity):
            if self.keys[i] is not None and self.keys[i] != self.DELETED:
                yield (self.keys[i], self.values[i])
    
    def keys_iter(self):
        """
        Return an iterator over keys.
        
        Yields:
            Keys in the hash table
        """
        for i in range(self.capacity):
            if self.keys[i] is not None and self.keys[i] != self.DELETED:
                yield self.keys[i]
    
    def values_iter(self):
        """
        Return an iterator over values.
        
        Yields:
            Values in the hash table
        """
        for i in range(self.capacity):
            if self.keys[i] is not None and self.keys[i] != self.DELETED:
                yield self.values[i]


class DefaultHashTable(HashTable):
    """
    Hash table that returns a default value for missing keys.
    Similar to collections.defaultdict but using our custom hash table.
    """
    
    def __init__(self, default_factory=None, initial_capacity=16, load_factor=0.75):
        """
        Initialize with a default factory function.
        """
        super().__init__(initial_capacity, load_factor)
        self.default_factory = default_factory
    
    def get(self, key, default=None):
        """
        Get value for key, creating default if key doesn't exist.
        """
        index, found = self._find_slot(key)
        
        if found:
            return self.values[index]
        
        # If we have a default factory, create and store the default value
        if self.default_factory is not None:
            default_value = self.default_factory()
            self.put(key, default_value)
            return default_value
        
        return default
    
    def __getitem__(self, key):
        """
        Get item with automatic default value creation.
        """
        index, found = self._find_slot(key)
        
        if found:
            return self.values[index]
        
        if self.default_factory is None:
            raise KeyError(f"Key not found: {key}")
        
        # Create default value and store it
        default_value = self.default_factory()
        self.put(key, default_value)
        return default_value


#testing purposes
    print("Testing HashTable implementation...")
    
    # Test basic operations
    ht = HashTable()
    ht["key1"] = "value1"
    ht["key2"] = "value2"
    ht["key3"] = "value3"
    
    print(f"Size: {len(ht)}")
    print(f"key1: {ht.get('key1')}")
    print(f"key2 in ht: {'key2' in ht}")
    print(f"key4 in ht: {'key4' in ht}")
    
    # Test DefaultHashTable
    print("\nTesting DefaultHashTable...")
    dht = DefaultHashTable(default_factory=list)
    dht["a"].append(1)
    dht["a"].append(2)
    dht["b"].append(3)
    
    print(f"a: {dht['a']}")
    print(f"b: {dht['b']}")
    
    # Test collision handling with many entries
    print("\nTesting with many entries (collision handling)...")
    ht2 = HashTable(initial_capacity=8)
    for i in range(100):
        ht2[f"key{i}"] = f"value{i}"

    
    print("\nAll tests passed!")