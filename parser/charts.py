#! /usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
# import utils as lk

from utils import Lookups as lk
from utils import Snapshots as sp 

BARS_COLORS = ['C10', 'C9', 'C1', 'C2']


def save_fig(filename: str):
    # TODO: check if directory charts exists, if not created it :)
    plt.savefig(f'charts/{filename}')
    plt.clf()  # clear drawn charts for others :)


def plot_avg_success_resolve(data: pd.DataFrame):
    filtered = data[data[lk.PROVIDERS] > 0]
    ax = filtered.groupby(lk.PEER_DHT)[lk.LOOKUP_TIME].mean().plot(
        kind='bar',
        figsize=(12, 8),
        color=BARS_COLORS,
        xlabel='',
    )

    # FIXME: better understand this thing
    cnt = ax.containers[0]
    ax.bar_label(cnt, labels=[f"{round(v, 2)} ms" for v in cnt.datavalues])

    plt.xticks(rotation=0, horizontalalignment="center")
    plt.ylabel('time (ms)', fontweight='bold')
    plt.title('Average Successful Resolve time (ms)', fontweight='bold')

    # plt.show()
    save_fig('avg-resolve.pdf')


def plot_success_rate(data: pd.DataFrame):

    aux = data[
        data[lk.PEER_DHT] == data[lk.CID_TYPE]
    ].groupby(lk.PEER_DHT)[lk.PROVIDERS].aggregate(
        ['sum', 'count']
    )

    aux['srante'] = aux['sum'] / aux['count'] * 100
    ax = aux['srante'].plot(
        kind='bar',
        figsize=(12, 8),
        color=BARS_COLORS,
        xlabel='',
    )

    # FIXME: better understand this thing
    cnt = ax.containers[0]
    ax.bar_label(cnt, labels=[f"{round(v, 2)}%" for v in cnt.datavalues])

    plt.xticks(rotation=0, horizontalalignment="center")
    plt.ylabel('success rate (%)', fontweight='bold')
    plt.title('Success rate of resolved CIDs', fontweight='bold')

    # Display the histogram
    # plt.show()
    save_fig('success-rate.pdf')


# turn this into an average per node :) 
def plot_cids_lookups(data: pd.DataFrame):
    # TODO: think if it's worthed to set constants
    # TODO: think on a way to solve the colors incovinience
    data = data[ data[lk.PEER_DHT] != 'All' ]
    # total_resolves = len(data)
    # print(total_resolves)
    print('-----------------------')
    print(data)
    data = data.groupby(lk.PEER_DHT)[lk.CID_TYPE].value_counts().to_frame()
    print('-----------------------')
    print(data)
    data.reset_index(level=(lk.CID_TYPE,), inplace=True)

    pivot_data = data.pivot(columns=lk.CID_TYPE, values='count').fillna(0)
    # print(pivot_data)
    # for col in pivot_data:
    #     pivot_data[col] = (100 * pivot_data[col] / total_resolves) 

    print('-----------------------')
    print(pivot_data)
    __before = pivot_data['Normal']

    pivot_data['Normal'] = pivot_data['Secure'] + pivot_data['Normal']

    ax = None
    for col, color in zip(pivot_data, BARS_COLORS[1:]):
        tmp = pivot_data.plot(
            kind='bar',
            color=color,
            figsize=(12, 8),
            y=col,
            ax=ax
        )
        if ax is None:
            ax = tmp

    # fix what I did :)
    pivot_data['Normal'] = pivot_data['Normal'] - pivot_data['Secure']

    assert (__before == pivot_data['Normal']).all(
    ), 'Normal data not properly restored'

    for cont, col in zip(ax.containers, pivot_data):
        ax.bar_label(cont, labels=['{:,}'.format(
            int(x)) if x != 0.0 else '' for x in pivot_data[col]])
            # round(x, 2)) if x != 0.0 else '' for x in pivot_data[col]])

    ax.legend(title='CID types')
    plt.xticks(rotation=0, horizontalalignment="center")
    plt.ylabel('Number of CIDs lookups', fontweight='bold')
    plt.xlabel('DHT Types', fontweight='bold')
    plt.title('Number of CIDs lookups by DHT and CID type', fontweight='bold')

    # plt.show()
    # save_fig('lookup-hist.pdf')


def plot_xxx(data: pd.DataFrame):
    pass

def read_data(filename : str) -> pd.DataFrame:
    data = pd.read_csv(filename)

    # some verfications
    # assert len(data[
    #     (data[lk.PEER_DHT] != data[lk.CID_TYPE]) & (data[lk.PROVIDERS] > 0)
    # ]) == 0, "something is VERY WRONG"

    aux = data[data[lk.PEER_DHT].isin(['SECURE', 'NORMAL'])].copy()
    aux[lk.PEER_DHT] = 'All'
    aux[lk.CID_TYPE] = 'All'

    for old, new in [
        ('DEFAULT', 'Baseline'),
        ('SECURE', 'Secure'),
        ('NORMAL', 'Normal')
    ]:
        data.replace(old, new, inplace=True)

    # return data
    return pd.concat([data, aux], ignore_index=True)


def main():
    # data = read_data('lookups.csv')
    # plot_xxx(data)
    # plot_avg_success_resolve(data)
    # plot_success_rate(data)
    # plot_cids_lookups(data)


    # data = read_data('snapshots.csv')
    # max_snapshot = data[lk.SNAPSHOT_NR].max()
    # print(data[
    #     (data[lk.SNAPSHOT_NR] == max_snapshot) & (data[lk.BUCKET_NR] == 0)
    # ].groupby(lk.SRC_DHT)[lk.SNAPSHOT_NR].count() / 3)


    # TODO: clean some rows
    snapshots = pd.read_csv('snapshots.csv')

    first_exp = snapshots[ (snapshots[sp.EXP_ID] == 0) & (snapshots[sp.BUCKET_NR] == 0) ]#.set_index([sp.SRC_PID, sp.SNAPSHOT_NR])

    data = first_exp.groupby([sp.SRC_PID, sp.SNAPSHOT_NR, sp.SRC_DHT])[sp.DST_DHT].value_counts().to_frame()
    # data = first_exp.groupby([sp.SRC_PID, sp.SNAPSHOT_NR, sp.SRC_DHT])[sp.DST_DHT].value_counts().to_frame()
    print(data)
    print('-------------------------')

    data.reset_index(level=(sp.DST_DHT), inplace=True)
    pivot_data = data.pivot(columns=sp.DST_DHT, values='count').fillna(0)
    print(pivot_data)

    # hi copilot now I have 3 columns, a b and c. I want to change the value of each to the percentage of the sum of the three columns.
    # the frame is saved in pivot_data
    # thank you that worked just fine :)
    pivot_data = pivot_data.apply(lambda x: round(x / x.sum() * 100, 2), axis=1)
    pivot_data.reset_index(inplace=True)

    print('-------------------------')
    print(pivot_data)

    secure_nodes = pivot_data[ pivot_data[sp.SRC_DHT] == 'SECURE'].copy()
    # Hi copioot, I have 5 collumns a, b, c, d, e. I want to group by a and calculate the mean of b, c and d.
    # I want to drop the collumn e since I don't need it.
    # the frame is saved in secure_nodes
    # thank you that worked just fine :)
    print('-------------------------')
    print(secure_nodes)
    secure_nodes.drop(columns=[sp.SRC_DHT, sp.SRC_PID], inplace=True)
    secure_nodes = secure_nodes.groupby(sp.SNAPSHOT_NR).mean()
    print('-------------------------')
    print(secure_nodes)


# TODO: charts by bucket and by experiment
# charts ideas:
#  - avg number of cid resolution by experiment
#  - evolution of routing table peers overall and them by bucket
if __name__ == '__main__':
    main()