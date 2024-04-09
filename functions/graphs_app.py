import plotly.express as px
import plotly.graph_objects as go

title_font = {'size': 25}
font = {'size': 16}
yaxis_currency = dict(tickprefix='$')
yaxis_comma = dict(separatethousands=True)


def make_bar_chart_period(table):
    periods = [*range(1, 13)]
    fig = go.Figure(
        data=[
            go.Bar(name='Actual Charges', x=periods, y=table['claims_period_paid'], yaxis='y', offsetgroup=1),
            go.Bar(name='Budget Charges', x=periods, y=table['charge_budget'], yaxis='y', offsetgroup=2),
            go.Line(name='Cumulative Variance', x=periods, y=table['cum_charge_variance'],
                    yaxis='y2',
                    marker=dict(size=10),
                    line=dict(color='#DE2C62', width=4)
                    ),
        ],
        layout={
            'yaxis2': {'title': "Cumulative Variance", 'overlaying': 'y', 'side': 'right'},
            'yaxis': {'title': 'Period Amount'},
            'xaxis': {'dtick': 2}
        }
    )
    fig.update_layout(
        barmode='group',

        title=dict(
            text='Charges Variances',
            y=0.9,
            x=0.5,
            yanchor='top',
            xanchor='center'
        ),
        title_font=title_font,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.21,
            xanchor='center',
            x=0.5
        )
    )

    return fig


def make_profit_impact_bar(table):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(name='P&L',
               x=table['P&L Impact'],
               y=table.index,
               marker_color=table['Color'],
               orientation='h',
               ))
    fig.update_layout(
        title=dict(
            text='Profit & Loss',
            font={'size': 24},
            y=0.97,
            x=0.5,
            yanchor='top',
            xanchor='center',
        ),
        xaxis=yaxis_currency,
    )
    fig.update_yaxes(title='Period',
                     autorange='reversed',),
    fig.update_xaxes(
                     ticks='outside',
                     tickcolor='white',
                     )

    return fig


def claims_indicator(c_claims, p_claims):
    fig = go.Figure(go.Indicator(
        mode='delta',
        value=c_claims,
        delta={'reference': p_claims, 'relative': False, 'valueformat': ','}
    ))
    fig.update_traces(delta_font={'size': 13})
    fig.update_layout(height=30, width=70)
    if c_claims >= p_claims:
        fig.update_traces(delta_increasing_color='green')
    else:
        fig.update_traces(delta_decreasing_color='red')

    return fig


def paid_indicator(c_paid, p_paid):
    fig = go.Figure(go.Indicator(
        mode='delta',
        value=c_paid,
        delta={'reference': p_paid, 'relative': False, 'valueformat': ','}
    ))
    fig.update_traces(delta_font={'size': 13})
    fig.update_layout(height=30, width=70)
    if c_paid >= p_paid:
        fig.update_traces(delta_increasing_color='green')
    else:
        fig.update_traces(delta_decreasing_color='red')

    return fig


def average_indicator(c_ave_per_claim, p_average):
    fig = go.Figure(go.Indicator(
        mode='delta',
        value=c_ave_per_claim,
        delta={'reference': p_average, 'relative': False, 'valueformat': ',.2f'}
    ))
    fig.update_traces(delta_font={'size': 13})
    fig.update_layout(height=30, width=70)
    if c_ave_per_claim >= p_average:
        fig.update_traces(delta_increasing_color='green')
    else:
        fig.update_traces(delta_decreasing_color='red')

    return fig


def member_indicator(c_member, p_member):
    fig = go.Figure(go.Indicator(
        mode='delta',
        value=c_member,
        delta={'reference': p_member, 'relative': False, 'valueformat': ','}
    ))
    fig.update_traces(delta_font={'size': 13})
    fig.update_layout(height=30, width=70)
    if c_member >= p_member:
        fig.update_traces(delta_increasing_color='green')
    else:
        fig.update_traces(delta_decreasing_color='red')

    return fig


def make_icd_spec_heatmap(table):
    fig_table = get_icd_spec_pivot(table)

    fig = px.imshow(
        fig_table,
        aspect='auto',
    )
    fig.update_layout(
        title=dict(
            text='Injury_Disease by Specialty',
            y=1,
            x=0.5,
            yanchor='top',
            xanchor='center'
        ),
        title_font=title_font,
        xaxis_title=None,
        yaxis_title=None,
        font=font,
    )
    fig.update_traces(
        xgap=1,
        ygap=1,
        hoverongaps=False,
        hovertemplate="Id: %{x}"
                      "<br>Period: %{y}"
                      "<br>Claims : %{z}<extra></extra>"
    )

    return fig


def get_icd_spec_pivot(table):
    table = table.loc[:, ['icd_name', 'specialty_name', 'charge_allowed']]

    group_icd = table.groupby('icd_name', as_index=False)['charge_allowed'].count().nlargest(10, 'charge_allowed')
    icd_list = group_icd['icd_name'].to_list()
    table = table[table['icd_name'].isin(icd_list)]
    group_spec = table.groupby('specialty_name', as_index=False)['charge_allowed'].count().nlargest(10,
                                                                                                    'charge_allowed')
    spec_list = group_spec['specialty_name'].to_list()
    table = table[table['specialty_name'].isin(spec_list)]
    table = table.pivot_table(index='icd_name', columns='specialty_name', values='charge_allowed', aggfunc='count',
                              fill_value=0)

    return table


def make_hospital_icd_pie(hospital_table):
    hospital_table = hospital_table.groupby('ICD', as_index=False)['charge_allowed'].sum().sort_values(
        by='charge_allowed', ascending=False)
    hospital_table['cum_charges'] = hospital_table['charge_allowed'].cumsum()
    hospital_table['% of total'] = hospital_table['cum_charges'] / (hospital_table.iloc[-1, 2])
    hospital_table_cutoff = hospital_table[hospital_table['% of total'] < .8]

    fig = px.pie(
        hospital_table_cutoff,
        names='ICD',
        values='charge_allowed',
    )

    fig.update_layout(
        title=dict(
            text='Top Injury or Diseases',
            y=1.0,
            x=0.5,
            yanchor='top',
            xanchor='center'
        ),
        title_font=title_font,
    )

    return fig


def make_hospital_spec_pie(hospital_table):
    hospital_table = hospital_table.groupby('SPEC', as_index=False)['charge_allowed'].sum().sort_values(
        by='charge_allowed', ascending=False)
    hospital_table['cum_charges'] = hospital_table['charge_allowed'].cumsum()
    hospital_table['% of total'] = hospital_table['cum_charges'] / (hospital_table.iloc[-1, 2])
    hospital_table_cutoff = hospital_table[hospital_table['% of total'] < .8]

    fig = px.pie(
        hospital_table_cutoff,
        names='SPEC',
        values='charge_allowed',
    )

    fig.update_layout(
        title=dict(
            text='Top Specialty',
            y=1.0,
            x=0.5,
            yanchor='top',
            xanchor='center'
        ),
        title_font=title_font,
    )

    return fig


def make_icd_racing_chart(table, table_title):
    dict_keys = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve']
    periods = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    n_frame = {}

    for p, d in zip(periods, dict_keys):
        dataframe = table[(table['period'] == p)]
        dataframe = dataframe.nlargest(n=10, columns=['claim_count_ytd'])
        dataframe = dataframe.sort_values(by=['period', 'claim_count_ytd'])

        n_frame[d] = dataframe

    fig = go.Figure(
        data=[
            go.Bar(
                x=n_frame['one']['claim_count_ytd'],
                y=n_frame['one']['name'],
                orientation='h',
                text=n_frame['one']['claim_count_ytd'],
                textfont=font,
                texttemplate='%{text:,.0f}',
                textposition='inside',
                insidetextanchor='middle',
                width=0.8,
                # marker={'color': n_frame['one']['color_code']}
            )
        ],
        layout=go.Layout(
            xaxis=dict(range=[0, 8600],
                       autorange=False,
                       separatethousands=True,
                       title=dict(text='Claims Processed',
                                  font=font
                                  )
                       ),
            yaxis=dict(range=[-0.5, 9.5],
                       autorange=False,
                       tickfont=font
                       ),
            title=dict(text=f'{table_title} Claims: Period 1',
                       font=title_font,
                       x=0.5,
                       xanchor='center'
                       ),
            font=font,
            # Button
            updatemenus=[dict(type='buttons',
                              buttons=[dict(label='Play',
                                            method='animate',
                                            args=[None,
                                                  {'frame': {'duration': 1000, 'redraw': True},
                                                   'transition': {'duration': 250, 'easing': 'linear'}
                                                   }
                                                  ],
                                            ),
                                       ],
                              x=.9,
                              y=0.2,
                              font={'color': '#000000'},

                              )
                         ]
        ),
        frames=[
            go.Frame(
                data=[
                    go.Bar(
                        x=value['claim_count_ytd'],
                        y=value['name'],
                        orientation='h',
                        text=value['claim_count_ytd'],
                        # marker={'color': value['color_code']}
                    )
                ],
                layout=go.Layout(
                    xaxis=dict(range=[0, 8600],
                               autorange=False
                               ),
                    yaxis=dict(range=[-0.5, 9.5],
                               autorange=False,
                               tickfont=font
                               ),
                    title=dict(text=f'{table_title} Category: Period ' + str(value['period'].values[0]),
                               font=title_font
                               )
                )
            )
            for key, value in n_frame.items()
        ]
    )

    return fig


def make_icd_period_bar_chart(table, choice):
    fig = go.Figure(
        data=[
            go.Bar(name='Claims', x=table['period'], y=table['charge_allowed'])
        ]
    )
    fig.update_layout(
        title=dict(
            text=f"Claims Processed for {choice}",
            x=0.5,
            xanchor='center',
            font={'size': 19}
        ),
    )
    fig.update_xaxes(
        dtick=2
    )

    return fig


def make_icd_specialty_bar_chart(table, choice):
    fig = go.Figure(
        data=[
            go.Bar(name='Claims', x=table['charge_allowed'], y=table['specialty_name'], orientation='h')
        ]
    )
    fig.update_layout(
        title=dict(
            text=f"Specialty Claims Processed for {choice}",
            x=0.5,
            xanchor='center',
            font={'size': 19}
        ),
        xaxis=yaxis_comma
    )
    fig.update_yaxes(autorange='reversed')

    return fig
