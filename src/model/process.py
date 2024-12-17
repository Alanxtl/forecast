import numpy as np
from pandas import get_dummies
import pandas as pd 

def process(all):
    data = all.copy()
    # data['Target'] = data['Target'].apply(lambda x: ast.literal_eval(x)[0] if x != '[]' else 0)

    # 计算变化百分比
    # data['Target'] = (data['Target'] - data['Commit Count']) / data['Commit Count']

    # 创建新列，根据变化比例进行分类
    # def categorize_change(row):
    #     if abs(row['Target']) > 0.3:  # 超过30%
    #         return 1 if row['Target'] > 0 else 0
    #     else:
    #         return 2  # 未超过30%

    # data = get_dummies(data, columns=['Target'])


    # data['code_per_file'] = data['Code Lines'] / data['Code Files']
    # data = data[data['Target'] < 400]
    data = data[data['Develop Time'] > 0]

    # data['code_line_delta'] = data['Added Code Lines'] - data['Removed Code Lines']
    # data['code_per_commit'] = (data['Added Code Lines'] + abs(data['Removed Code Lines'])) / data['Commit Count']

    data["Fork Count"] = data["Fork Count"].apply(lambda x: x if x != 0 else 1)
    data["Modified File Count (Average)"] = data["Modified File Count (Average)"].astype(int)

    data["PR Length"] = data["PR Length"].astype(int)
    data["PR Length"] = data["PR Length"].replace(0, np.nan)
    data["Created PRs"] = data["Created PRs"].replace(0, np.nan)
    data["Closed PRs"] = data["Closed PRs"].replace(0, np.nan)
    data["Created Issues"] = data["Created Issues"].replace(0, np.nan)
    data["Closed Issues"] = data["Closed Issues"].replace(0, np.nan)

    data = data.replace(np.inf, np.nan)

    data = data.apply(lambda x: x.fillna(x.mean()), axis=0)
    data["PR Length"] = data["PR Length"].astype(int)
    data["Created PRs"] = data["Created PRs"].astype(int)
    data["Closed PRs"] = data["Closed PRs"].astype(int)
    data["Created Issues"] = data["Created Issues"].astype(int)
    data["Closed Issues"] = data["Closed Issues"].astype(int)
    data["Label Counts (Average)"] = data["Label Counts (Average)"].astype(int)
    data["Target"] = data["Target"].astype(int)

    # data['Target'] = data['Target'] // 100
    # from sklearn.preprocessing import LabelEncoder
    # label_encoder = LabelEncoder()
    # data['Target'] = label_encoder.fit_transform(data['Target'])

    # # data["PR Length"] = data["PR Length"].astype(int)

    data = data.drop(columns=['Core Developers Focus Rate',
                              'Bot Commit', 'Reopened Issues',
                              'Markdown Files', 'Markdown Lines',
                              'Code Files', 'Code Lines', 'Code Comments'])

    data = data.drop(columns=['Commit Count'])

    return data, data.drop(columns=['Target'])

def open_dataset(directory):
    df = pd.read_csv(directory)

    df['Target'] = df['Commit Count'].shift(-1)
    df['Target'] = df['Target'].fillna(df['Commit Count'])

    return df