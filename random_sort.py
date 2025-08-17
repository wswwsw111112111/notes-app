import random

# 生成1-200000之间的100000个随机整数
A = random.sample(range(1, 200001), 100000)

# 使用Python内置的排序函数对数组进行排序
B = sorted(A)

# 打印排序后的数组
print("排序后的数组B：")
print(B) 