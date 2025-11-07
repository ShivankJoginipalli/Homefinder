class default_dict:
    def __init__(self, defaultType=None):
        self.defaultType = defaultType
        self.data = {}
    def __getitem__(self, key):
        if key not in self.data:
            if self.defaultType is None:
                print("Key not found")
                return
            self.data[key] = self.defaultType()
        return self.data[key]
    def __setitem__(self, key, value):
        self.data[key] = value
    def __isin__(self,key):
        return key in self.data
    def __get__(self, key, default = None):
        if key in self.data:
            return self.data[key]
        return default
    def __len__(self):
        return len(self.data)
    def __iter__(self):
        return iter(self.data)
    def __items__(self):
        return self.data.items()
    def __keys__(self):
        return self.data.keys()
    def __values__(self):
        return self.data.values()