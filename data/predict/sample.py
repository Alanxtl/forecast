import pandas as pd

def read(file_path):
    df = pd.read_csv(file_path)

    random_sample = df.sample(n=150)

    second_column = random_sample.iloc[:, 1] 

    second_column.to_csv(f'{file_path}_out.csv', index=False)

if __name__ == "__main__":
    list = ["./" + i + ".csv" for i in ["50-100", "100-1k", "1k-5k", "5k-10k", "10k-15k"]]

    for i in list:
        read(i)
