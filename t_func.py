#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author： WenRichard
# ide： PyCharm

a = [[1,2], [3,4]]
a1, a2 = zip(*a)
print(a1)

b = {'a':1, 'b':2}
for i in b:
    print(i)