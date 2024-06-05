list = [['default_product_1', 500, 500, 25.0], ['default_product_2', 1000, 1000, 100.0], ['default_product_3', 1500, 1000, 150.0], ['default_product_4', 500, 1000, 50.0]]
print(list)

def dict_to_list(list):
    dict_product_types = {}
    for i in range(len(list)):
        dict_product_types[list[i][0]] = dict(length=list[i][1], width=list[i][2], weight=list[i][3])
    return dict_product_types

print(dict_to_list(list))