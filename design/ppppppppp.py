import ast

data = "[10,20],[30,40]"

middle_data = f"[{data}]"

result = ast.literal_eval(middle_data)
print(result)