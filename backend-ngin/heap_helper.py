class MinHeap:
    def __init__(self):
        self.a = []
    def __len__(self):
        return len(self.a)
    def push(self, item):
        self.a.append(item)
        i = len(self.a) - 1
        while i > 0:
            p = (i - 1) // 2
            if self.a[i] < self.a[p]:
                self.a[i], self.a[p] = self.a[p], self.a[i]
                i = p
            else:
                break
    def pop(self):
        if not self.a:
            return None
        top = self.a[0]
        last = self.a.pop()
        if self.a:
            self.a[0] = last
            i = 0
            n = len(self.a)
            while True:
                l = 2*i + 1
                r = 2*i + 2
                s = i
                if l < n and self.a[l] < self.a[s]:
                    s = l
                if r < n and self.a[r] < self.a[s]:
                    s = r
                if s == i:
                    break
                self.a[i], self.a[s] = self.a[s], self.a[i]
                i = s
        return top