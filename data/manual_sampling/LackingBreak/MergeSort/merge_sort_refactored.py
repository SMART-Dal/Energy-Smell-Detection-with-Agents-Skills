import random

def merge_sort(l: list):
    if len(l) == 1:
        return l
    half = len(l) // 2
    left, right = l[:half], l[half:]
    sorted_left = merge_sort(left)
    sorted_right = merge_sort(right)

    curr_left_idx, curr_right_idx = 0, 0
    new_sorted = []
    while curr_left_idx < len(sorted_left) or curr_right_idx < len(sorted_right):
        if curr_left_idx >= len(sorted_left):
            new_sorted.extend(sorted_right[curr_right_idx:])
            break
        
        if curr_right_idx >= len(sorted_right):
            new_sorted.extend(sorted_left[curr_left_idx:])
            break

        curr_left_value = sorted_left[curr_left_idx]
        curr_right_value = sorted_right[curr_right_idx]
        
        if curr_left_value < curr_right_value:
            new_sorted.append(curr_left_value)
            curr_left_idx += 1
        else:
            new_sorted.append(curr_right_value)
            curr_right_idx += 1

    return new_sorted


random.seed(42)
temp = [random.randint(0, int(1e7)) for i in range(int(1e6))]
for i in range(5):
    a = merge_sort(temp)
