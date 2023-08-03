#! /usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import utils as hd

BARS_COLORS = ['C10', 'C9', 'C1', 'C2']

def save_fig(filename : str):
    # TODO: check if directory charts exists, if not created it :)
    plt.savefig(f'charts/{filename}')
    plt.clf() # clear drawn charts for others :)

def plot_avg_success_resolve(data : pd.DataFrame):
    filtered = data[ data[hd.PROVIDERS] > 0 ]
    ax = filtered.groupby(hd.PEER_DHT)[hd.LOOKUP_TIME].mean().plot(
        kind='bar',
        figsize=(12,8),
        color=BARS_COLORS,
        xlabel='',
    )

    # FIXME: better understand this thing
    cnt = ax.containers[0]
    ax.bar_label(cnt, labels=[ f"{round(v, 2)} ms"  for v in cnt.datavalues])
    
    plt.xticks(rotation=0, horizontalalignment="center")
    plt.ylabel('time (ms)', fontweight='bold')
    plt.title('Successful Average Result time (ms)', fontweight='bold')

    # plt.show()
    save_fig('avg-result.pdf')


def plot_success_rate(data : pd.DataFrame):

    aux = data[
        data[hd.PEER_DHT] == data[hd.CID_TYPE]
    ].groupby(hd.PEER_DHT)[hd.PROVIDERS].aggregate(
        ['sum', 'count']
    )

    aux['srante'] = aux['sum'] / aux['count'] * 100
    ax = aux['srante'].plot(
        kind='bar',
        figsize=(12,8),
        color=BARS_COLORS,
        xlabel='',
    )


    # FIXME: better understand this thing
    cnt = ax.containers[0]
    ax.bar_label(cnt, labels=[ f"{round(v, 2)}%"  for v in cnt.datavalues])

    plt.xticks(rotation=0, horizontalalignment="center")
    plt.ylabel('success rate (%)', fontweight='bold')
    plt.title('Success rate of resolved CIDs', fontweight='bold')

    # Display the histogram
    # plt.show()
    save_fig('success-rate.pdf')

def plot_resolved_cids(data : pd.DataFrame):
    # TODO: think if it's worthed to set constants
    data = data.groupby(hd.PEER_DHT)[hd.CID_TYPE].value_counts().to_frame()
    data.reset_index(level=(hd.CID_TYPE,), inplace=True)

    pivot_data = data.pivot(columns=hd.CID_TYPE, values='count').fillna(0)

    __before = pivot_data['Normal']

    pivot_data['Normal'] = pivot_data['Secure'] + pivot_data['Normal']

    ax = None
    for col, color in zip(pivot_data, BARS_COLORS):
        tmp = pivot_data.plot(
            kind='bar', 
            color=color,
            figsize=(12,8),
            y=col,
            ax=ax
        ) 
        if ax is None:
            ax = tmp

    # fix what I did :)
    pivot_data['Normal'] =  pivot_data['Normal'] - pivot_data['Secure']

    assert (__before == pivot_data['Normal']).all(), 'Normal data not properly restored'

    for cont, col in zip(ax.containers, pivot_data):
        ax.bar_label(cont, labels=['{:,}'.format(int(x)) if x != 0.0 else '' for x in pivot_data[col]])
    

    ax.legend(title='CID types')
    plt.xticks(rotation=0, horizontalalignment="center")
    plt.ylabel('Number of CIDs lookups', fontweight='bold')
    plt.xlabel('DHT Types', fontweight='bold')
    plt.title('Number of CIDs lookups by DHT type and CID type', fontweight='bold')

    # plt.show()
    save_fig('cid-hist.pdf')

# change some values so as to have better 
# naming in the charts
RENAMES = [
    ('DEFAULT', 'Baseline'), 
    ('SECURE', 'Secure'), 
    ('NORMAL', 'Normal')
]


def read_data() -> pd.DataFrame:
    data = pd.read_csv("data.csv")

    # some verfications
    assert len(data[ 
        (data[hd.PEER_DHT] != data[hd.CID_TYPE]) & (data[hd.PROVIDERS] > 0)
    ]) == 0, "something is VERY WRONG"


    aux = data[ data[hd.PEER_DHT].isin(['SECURE', 'NORMAL']) ].copy()
    aux[hd.PEER_DHT] = 'All'
    aux[hd.CID_TYPE] = 'All'

    return pd.concat([data, aux], ignore_index=True)

def main():
    # data = pd.read_csv("data.csv")
    # TODO: change the order to Baseline, Normal, Secure, All
    data = read_data()
    for old, new in RENAMES:
        data.replace(old, new, inplace=True)

    plot_avg_success_resolve(data)
    plot_success_rate(data)
    plot_resolved_cids(data)


if __name__ == '__main__':
    main()