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
    data = data[data[lk.PROVIDERS] > 0]

    data = data.groupby([lk.PEER_DHT, lk.CID_TYPE])[lk.LOOKUP_TIME].agg(resolve_time='mean')

    print(data)
    data.reset_index(level=(lk.CID_TYPE,), inplace=True)
    pivot_data = data.pivot(columns=lk.CID_TYPE, values='resolve_time').fillna(0)

    ax = pivot_data.plot(
        kind='bar', color=BARS_COLORS[1:],
        figsize=(14, 6),
    )

    for cnt in ax.containers:
        ax.bar_label(cnt, labels=[f"{round(v, 2)} ms" if v > 0.0 else '' for v in cnt.datavalues])

    # ax = filtered.groupby(lk.PEER_DHT)[lk.LOOKUP_TIME].mean().plot(
    #     kind='bar',
    #     figsize=(12, 8),
    #     color=BARS_COLORS,
    #     xlabel='',
    # )

    # # FIXME: better understand this thing

    plt.xticks(rotation=0, horizontalalignment="center")
    plt.xlabel('DHT version', fontweight='bold')
    plt.ylabel('time (ms)', fontweight='bold')
    plt.title('Average Resolve time (ms)', fontweight='bold')
    plt.legend(title='CID types')

    # plt.show()
    save_fig('avg-resolve.pdf')


def plot_success_rate(data: pd.DataFrame):

    data = data.groupby([lk.PEER_DHT, lk.CID_TYPE])[lk.PROVIDERS].aggregate(
        ['sum', 'count']
    )
    data.reset_index(level=(lk.CID_TYPE,), inplace=True)

    data['success rate'] = data['sum'] / data['count'] * 100

    pivot_data = data.pivot(columns=lk.CID_TYPE, values='success rate').fillna(0)

    ax = pivot_data.plot(
        kind='bar',
        figsize=(14, 6),
        color=BARS_COLORS[:],
    )

    print(pivot_data)

    for cnt in ax.containers:
        ax.bar_label(cnt, labels=[f"{round(v, 2)} %" if v > 0.0 else '' for v in cnt.datavalues])

    # aux['srante'] = aux['sum'] / aux['count'] * 100
    # ax = aux['srante'].plot(
    #     kind='bar',
    #     figsize=(12, 8),
    #     color=BARS_COLORS,
    #     xlabel='',
    # )

    # # FIXME: better understand this thing
    # cnt = ax.containers[0]
    # ax.bar_label(cnt, labels=[f"{round(v, 2)}%" for v in cnt.datavalues])

    plt.xticks(rotation=0, horizontalalignment="center")
    plt.xlabel('DHT version', fontweight='bold')
    plt.ylabel('success rate (%)', fontweight='bold')
    plt.title('Success rate of resolved CIDs', fontweight='bold')
    plt.legend(title='CID types', loc='lower right')

    # # Display the histogram
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

def calc_rt_evolution(snapshots: pd.DataFrame) -> pd.DataFrame:
    data = snapshots.groupby([sp.SRC_PID, sp.SNAPSHOT_NR, sp.SRC_DHT, sp.EXP_ID])[sp.DST_DHT].value_counts().to_frame()
    # print(data)

    # Some nodes dies during the experiment, for motives I have no control of # those that die right at 
    # the begining of the experiment are remove from the data when generating the csv but those that die 
    # during hte experiment are not so I ran this to notice how many did so. (in order to see if their 
    # data would statistically ruin the results). 
    #
    # +-----------------------------------------------------------+
    # | The results I got were (format: exp-id => died/didn't):   |
    # |   - 0 => 1/599                                            |
    # |   - 1 => 1/600                                            |
    # |   - 2 => 1/597                                            |
    # +-----------------------------------------------------------+
    #
    # max_snap = snapshots[sp.SNAPSHOT_NR].max()
    # for exp_id in range(3):
    #     filtered = snapshots[ snapshots[sp.EXP_ID] == exp_id ]
    #     aux = filtered.groupby(sp.SRC_PID)[sp.SNAPSHOT_NR].max().to_frame()
    #     print(aux.columns)
    #     print(f'exp: {exp_id}; mad-node/total-nodes: {len(aux[aux[sp.SNAPSHOT_NR] != max_snap])}/{len(aux)}')

    # get each type as a row
    data.reset_index(level=(sp.DST_DHT), inplace=True)
    pivot_data = data.pivot(columns=sp.DST_DHT, values='count').fillna(0)
    # print(pivot_data)

    # turn each row number as  (axis=1 stands for apply to each row)
    pivot_data = pivot_data.apply(lambda x: round(x / x.sum() * 100, 2), axis=1)
    pivot_data.reset_index(inplace=True)
    
    pivot_data.drop(columns=[sp.SRC_DHT, sp.SRC_PID, sp.EXP_ID], inplace=True)
    pivot_data = pivot_data.groupby(sp.SNAPSHOT_NR).mean()
    # print(pivot_data)

    for dht_type in pivot_data.columns:
        aux = pivot_data[dht_type]
        if len(aux) > 0 :
            plt.plot(pivot_data.index, aux, label=dht_type)

    return pivot_data


def plot_rt_evolution(snapshots: pd.DataFrame):

    def build_chart(data : pd.DataFrame, title: str, xlabel : str, ylabel : str):
        plt.ylim(0, 100)
        plt.xlim(0, data.index.max()) # 0 to max snapshot-number
        plt.legend()

        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

    for node_type in ['Secure', 'Normal']:
        snaps    = snapshots[snapshots[sp.SRC_DHT] == node_type]
        dht_evol = calc_rt_evolution(snaps)
        build_chart(
            dht_evol,
            f'Evolution of the routing table of {node_type} Nodes',
            'Time (minutes) from the start of the experiment',
            'Percentage (%) of nodes in the routing table'
        )
        save_fig(f'{node_type}-rt-end.pdf')

        for bucket in snaps[sp.BUCKET_NR].unique():
            build_chart(
                calc_rt_evolution(snaps[ snaps[sp.BUCKET_NR] == bucket ]),
                f'Evolution of the bucket {bucket} of {node_type} Nodes',
                'Time (minutes) from the start of the experiment',
                'Percentage (%) of nodes in the bucket'
            )

            save_fig(f'{node_type}-rt-evol-bucket-{bucket}.pdf')



def calc_rt_state(snapshots: pd.DataFrame) -> pd.DataFrame:
    data = snapshots.groupby([
        sp.SRC_PID, sp.SNAPSHOT_NR, sp.SRC_DHT, sp.EXP_ID
    ])[sp.DST_DHT].value_counts().to_frame('version-frequency')

    data.reset_index(level=(sp.DST_DHT), inplace=True)

    # get each type as a row turn each dht version type number into a row
    pivot_data = data.pivot(columns=sp.DST_DHT, values='version-frequency').fillna(0)

    # calculate the percentage of each freuqency
    pivot_data = pivot_data.apply(lambda x: round(x / x.sum() * 100, 2), axis=1)
    pivot_data.reset_index(inplace=True)
    
    # drop the collumns that doesn't matter more
    pivot_data.drop(columns=[sp.SRC_PID, sp.EXP_ID, sp.SNAPSHOT_NR], inplace=True)

    # get the average of each percentage by SRC_DHT
    pivot_data = pivot_data.groupby(sp.SRC_DHT).mean()

    
    return pivot_data

def plot_end_rt_state(snapshots: pd.DataFrame):
    last_snap = snapshots[sp.SNAPSHOT_NR].unique().max()
    snapshots = snapshots[ 
          (snapshots[sp.SNAPSHOT_NR] == last_snap) 
        & (snapshots[sp.SRC_DHT].isin(['Secure', 'Normal']))
    ]

    def built_chart(data: pd.DataFrame, title: str, filename: str):
        ax = data.plot(
            kind='bar',
            figsize=(12, 6),
            color=['C3', BARS_COLORS[2], BARS_COLORS[3]]
        )

        for cnt in ax.containers:
            ax.bar_label(cnt, labels=[f"{round(v, 2)} %" if v > 0.0 else '' for v in cnt.datavalues])

        plt.xticks(rotation=0, horizontalalignment="center")
        plt.title(title, fontweight='bold')
        # plt.title('Percentage of nodes of each DHT version known by each', fontweight='bold')
        plt.xlabel('DHT version', fontweight='bold')
        plt.ylabel('percentage of the nodes in DHT', fontweight='bold')
        plt.legend(title='CID types')
        save_fig(filename)

    data = calc_rt_state(snapshots)
    built_chart(data, 'Percentage of nodes neibours in the Routing table', 'rt-end-state.pdf')

    for bucket in snapshots[sp.BUCKET_NR].unique():
        aux = snapshots[snapshots[sp.BUCKET_NR] == bucket]
        data = calc_rt_state(aux)
        built_chart(
            data, 
            f'Percentage of nodes neibours in the bucket {bucket}', 
            f'rt-end-state-bucket-{bucket}.pdf'
        )






def read_data(filename : str) -> pd.DataFrame:
    data = pd.read_csv(filename)

    # some verfications
    # assert len(data[
    #     (data[lk.PEER_DHT] != data[lk.CID_TYPE]) & (data[lk.PROVIDERS] > 0)
    # ]) == 0, "something is VERY WRONG"

    # NOTE: Akos said is not relevant at all having all here
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
    #return pd.concat([data, aux], ignore_index=True)


def main():
    data = read_data('lookups.csv')
    plot_avg_success_resolve(data)
    plot_success_rate(data)
    # plot_cids_lookups(data)
    # TODO: do the number of queries in the publish and resolve

    # snapshots = read_data('snapshots.csv')
    # # plot_rt_evolution(snapshots)
    # plot_end_rt_state(snapshots)


# TODO: charts by bucket and by experiment
# charts ideas:
#  - avg number of cid resolution by experiment
#  - experiment to check why normal nodes are more frequent than secure
#  x evolution of routing table peers overall and them by bucket 
if __name__ == '__main__':
    main()