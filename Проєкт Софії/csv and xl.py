import pandas as pd

data = {
    'Month':   ['Jan','Feb','Mar','Apr','May'],
    'Revenue': [108.12, 111.49, 126.45, 138.27, 162.51],
    'Cost':    [ 63.91,  65.74,  79.27,  79.66,  96.99]
}
df = pd.DataFrame(data)

df.to_csv('pretty_data.csv', index=False)

df.to_excel('pretty_data.xlsx', index=False)
