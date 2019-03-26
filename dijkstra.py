
MAX_VALUE = 10000
COL = 5
ROW = 5
a = [[MAX_VALUE for i in range(COL)] for j in range(ROW)]
# 初始节点
a[0][0] = 0
a[0][1] = 4
a[0][2] = 2
a[1][2] = 3
a[1][3] = 2
a[2][1] = 1
a[2][3] = 4
a[2][4] = 5
a[4][3] = 1
# 初始节点, 以节点0为起点
# make queue
queue = [a[0][i] for i in range(ROW)]
# 标记已经被删除的元素
s = set()
# 保存结果
res = []
while len(s) != len(queue):
    # 查找最小矩离
    min_val = MAX_VALUE
    index = 0
    for i in range(COL):
        if i in s:
            # 已经被删除
            continue
        if queue[i] < min_val:
            min_val = queue[i]
            index = i

    for i in range(COL):
        if i in s:
            continue
        # decrease key
        queue[i] = min(queue[i], queue[index]+a[index][i])

    # 删除最小值, delete min
    s.add(index)
    res.append(index)
    print(queue)

print(res)
