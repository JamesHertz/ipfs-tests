#! /usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import utils as hd

def plot_avg_success_resolve(data : pd.DataFrame):

    filtered = data[ data[hd.PROVIDERS] > 0 ]
    filtered.groupby(hd.PEER_DHT)[hd.LOOKUP_TIME].mean().plot(
        kind='barh',
        figsize=(12,8),
        color=['C1', 'C2'],
        title='Successful Average Result time (ms)',
        ylabel='',
        xlabel='time (ms)'
    )

    plt.savefig('avg-result.pdf')
    plt.clf() # clear drawn charts for others :)


def plot_success_rate(data : pd.DataFrame):

    aux = data[
        data[hd.PEER_DHT] == data[hd.CID_TYPE]
    ].groupby(hd.PEER_DHT)[hd.PROVIDERS].aggregate(
        ['sum', 'count']
    )

    aux['srante'] = aux['sum'] / aux['count'] * 100
    aux['srante'].plot(
        kind='barh',
        figsize=(12,8),
        color=['C1', 'C2'],
        title='Success rate of resolved CIDs',
        ylabel='',
        xlabel='success rate (%)'
    )

    # Display the histogram
    # plt.show()
    plt.savefig('success-rate.pdf')
    plt.clf() # clear drawn charts for others :)


# Read the CSV file
def main():
    data = pd.read_csv("data.csv")

    assert len(data[ 
        (data[hd.PEER_DHT] != data[hd.CID_TYPE]) & (data[hd.PROVIDERS] > 0)
    ]) == 0, "something is VERY WRONG"
    plot_avg_success_resolve(data)
    plot_success_rate(data)


if __name__ == '__main__':
    main()