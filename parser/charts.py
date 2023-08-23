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


def plot_cids_lookups(data: pd.DataFrame):
    # TODO: think if it's worthed to set constants
    # TODO: think on a way to solve the colors incovinience
    data = data.groupby(lk.PEER_DHT)[lk.CID_TYPE].value_counts().to_frame()
    data.reset_index(level=(lk.CID_TYPE,), inplace=True)

    pivot_data = data.pivot(columns=lk.CID_TYPE, values='count').fillna(0)

    __before = pivot_data['Normal']

    pivot_data['Normal'] = pivot_data['Secure'] + pivot_data['Normal']

    ax = None
    for col, color in zip(pivot_data, BARS_COLORS):
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

    ax.legend(title='CID types')
    plt.xticks(rotation=0, horizontalalignment="center")
    plt.ylabel('Number of CIDs lookups', fontweight='bold')
    plt.xlabel('DHT Types', fontweight='bold')
    plt.title('Number of CIDs lookups by DHT and CID type', fontweight='bold')

    # plt.show()
    save_fig('lookup-hist.pdf')

def read_data(filename : str) -> pd.DataFrame:
    data = pd.read_csv(filename)

    # some verfications
    # assert len(data[
    #     (data[lk.PEER_DHT] != data[lk.CID_TYPE]) & (data[lk.PROVIDERS] > 0)
    # ]) == 0, "something is VERY WRONG"

    # aux = data[data[lk.PEER_DHT].isin(['SECURE', 'NORMAL'])].copy()
    # aux[lk.PEER_DHT] = 'All'
    # aux[lk.CID_TYPE] = 'All'

    for old, new in [
        ('DEFAULT', 'Baseline'),
        ('SECURE', 'Secure'),
        ('NORMAL', 'Normal')
    ]:
        data.replace(old, new, inplace=True)

    return data
    # return pd.concat([data, aux], ignore_index=True)


def main():
    # data = read_data('lookups.csv')
    # plot_avg_success_resolve(data)
    # plot_success_rate(data)
    # plot_cids_lookups(data)
    data = read_data('snapshots.csv')
    max_snapshot = data[lk.SNAPSHOT_NR].max()
    print(data[
        (data[lk.SNAPSHOT_NR] == max_snapshot) & (data[lk.BUCKET_NR] == 0)
    ].groupby(lk.SRC_DHT)[lk.SNAPSHOT_NR].count() / 3)

# charts ideas:
#  - avg number of cid resolution by experiment
#  - evolution of routing table peers overall and them by bucket
# TODO: add experiment ID to every chart :)

if __name__ == '__main__':
    main()
