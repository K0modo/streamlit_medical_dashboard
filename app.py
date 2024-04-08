import streamlit as st
from functions.data_app_calculations import CorporateTables, ClaimData
from functions import graphs_app as graphs

# MOVE TO MODEL FILE
st.set_page_config(
    page_title="Tynan Member Dashboard",
    page_icon=':bar_chart:',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.markdown("""
<style>

.st-emotion-cache-434r0z {
    padding-top:2rem;
    padding-bottom:2rem;
}

.st-emotion-cache-wyrmhr {
    padding-top:0;
    padding-bottom:0;
}

</style>
""", unsafe_allow_html=True)

conn = st.connection('db_tynan', type='sql')

avg_per_day = 130000
reserve_rate = 0.07
overhead_rate = 0.11
admin_rate = 0.1
profit_rate = .07
wrap_rate = round((((1 + overhead_rate) * (1 + admin_rate)) * (1 + profit_rate) - 1), 2)
period_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

### Title Row
st.markdown("<h2 style='text-align: center;'>Tynan Analytics Dashboard</h2>", unsafe_allow_html=True)

###  Statistics Rows
col = st.columns(8)

with col[0]:
    select_period = st.selectbox("Select Period:", period_list)

col = st.columns((2, 2, 2, 2, 2))

with col[0]:
    annual_stats = conn.query("Select * from v_period_summary")
    annual_data = ClaimData(annual_stats)
    p_claims = annual_data.get_select_claims(select_period)
    p_paid = annual_data.get_select_paid(select_period)
    p_average = p_paid / p_claims

    st.markdown("Metric:")
    st.markdown("Annual:")
    st.markdown("Current:")
    st.markdown(f'Period: {select_period}')
    st.markdown("Difference")

with col[1]:
    st.markdown("Claims Processed")
    st.markdown(f'{annual_data.a_claims:,}')
    st.markdown(f'{annual_data.c_claims:,}')
    st.markdown(f'{p_claims:,}')

    fig = graphs.claims_indicator(annual_data.c_claims, p_claims)
    st.plotly_chart(fig, use_container_width=False)

with col[2]:
    st.markdown("Claim Charges")
    st.markdown(f'$ {annual_data.a_paid:,.0f}')
    st.markdown(f'$ {annual_data.c_paid:,.0f}')
    st.markdown(f'$ {p_paid:,.0f}')

    fig = graphs.paid_indicator(annual_data.c_paid, p_paid)
    st.plotly_chart(fig, use_container_width=False)

with col[3]:
    st.markdown("Average Charges")
    st.markdown(f'$ {annual_data.a_ave_per_claim:,.2f}')
    st.markdown(f'$ {annual_data.c_ave_per_claim:,.2f}')
    st.markdown(f'$ {p_average:,.2f}')

    fig = graphs.average_indicator(annual_data.c_ave_per_claim, p_average)
    st.plotly_chart(fig, use_container_width=False)

with col[4]:
    a_members = conn.query("Select Count(DISTINCT mem_acct_id) from v_consolidated_codes")
    member_stats = conn.query("Select period, daily_member_sum from v_member_summary")
    member_stats = member_stats.set_index('period')
    c_member = member_stats.loc[12, 'daily_member_sum']
    p_member = member_stats.loc[select_period, 'daily_member_sum']

    st.markdown("Members")
    st.markdown(f'{a_members.iloc[0, 0]:,}')
    st.markdown(f'{c_member}')
    st.markdown(f'{p_member}')

    fig = graphs.member_indicator(c_member, p_member)
    st.plotly_chart(fig, use_container_width=False)

st.markdown("")
st.markdown("")

###  RACING CHARTS
st.markdown("<h3 style='text-align: center;'>Claims Processed Top 10</h3>", unsafe_allow_html=True)
col = st.columns((4, 4))

with col[0]:
    table_title = 'Injury_Disease'
    icd_racing_table = conn.query("Select name, period, claim_count_ytd from v_icd_racing")
    icd_racing_chart = graphs.make_icd_racing_chart(icd_racing_table, table_title)
    st.plotly_chart(icd_racing_chart, use_container_width=True)

with col[1]:
    table_title = 'Provider Specialty'
    specialty_racing_table = conn.query(
        "Select name, period, claim_count_ytd from v_specialty_racing where "
        "name != 'Hospital_Clinic'")
    specialty_racing_chart = graphs.make_icd_racing_chart(specialty_racing_table, table_title)
    st.plotly_chart(specialty_racing_chart, use_container_width=True)

st.markdown("")
st.markdown("")

### ICD Table

with st.expander("ICD TABLE"):
    col = st.columns([2, 7, 1])

    with col[1]:
        query = conn.query("""
            Select period, injury_disease_id, t_injury_disease.name as icd_name, specialty_id, t_specialty.name as specialty_name, 
                    charge_allowed from v_consolidated_codes as vcc
            inner join t_injury_disease
            on vcc.injury_disease_id = t_injury_disease.id
            left join t_specialty
            on vcc.specialty_id = t_specialty.id
            """)

        query_df = query.copy()

        query_group_icd = query_df.groupby('icd_name', as_index=False).agg(Claims=('charge_allowed', 'count'),
                                                                           Charges=('charge_allowed', 'sum'),
                                                                           Average=('charge_allowed', 'mean'),
                                                                           Max=('charge_allowed', 'max')
                                                                           )

        query_df_pivot = query_df.pivot_table(index='icd_name',
                                              columns='period',
                                              values='charge_allowed',
                                              aggfunc='count',
                                              fill_value=0
                                              )

        row_list = []
        for i in query_df_pivot.index:
            row = query_df_pivot.loc[i, :].to_list()
            row_list.append(row)

        query_merged = query_group_icd.merge(query_df_pivot,
                                             how='left',
                                             left_on=['icd_name'],
                                             right_index=True
                                             )

        query_merged['icd_chart_data'] = row_list

        query_final = query_merged.loc[:, ['icd_name', 'Claims', 'Charges', 'Average', 'Max', 'icd_chart_data']]

        st.dataframe(query_final,
                     column_config={
                         'icd_name': "Injury or Disease",
                         'icd_chart_data': st.column_config.BarChartColumn(
                             "Prior Periods",
                             y_min=0,
                             y_max=200
                         )
                     },
                     hide_index=True)

### SPECIALTY Table

with st.expander("PROVIDER SPECIALTY TABLE"):
    col = st.columns([2, 7, 1])
    query_df = query.copy()

    with col[1]:
        query_group_spec = (
            query_df.groupby('specialty_name', as_index=False).agg(Claims=('charge_allowed', 'count'),
                                                                   Charges=('charge_allowed', 'sum'),
                                                                   Average=('charge_allowed', 'mean'),
                                                                   Max=('charge_allowed', 'max'))
        )

        query_df_pivot = query_df.pivot_table(
            index='specialty_name',
            columns='period',
            values='charge_allowed',
            aggfunc='count',
            fill_value=0
        )

        row_list = []
        for i in query_df_pivot.index:
            row = query_df_pivot.loc[i, :].to_list()
            row_list.append(row)

        query_merged = query_group_spec.merge(query_df_pivot,
                                              how='left',
                                              left_on=['specialty_name'],
                                              right_index=True
                                              )

        query_merged['specialty_chart_data'] = row_list

        query_final = query_merged.loc[:, ['specialty_name', 'Claims', 'Charges', 'Average', 'Max',
                                           'specialty_chart_data']]

        st.dataframe(query_final,
                     column_config={
                         'specialty_name': "Provider Specialty",
                         'specialty_chart_data': st.column_config.BarChartColumn(
                             "Prior Periods",
                             y_min=0,
                             y_max=200
                         )
                     },
                     hide_index=True)

with st.expander("HEATMAP"):
    col = st.columns([1, 7, 1])

    with col[1]:
        query_df_heat = query_df[query_df['specialty_id'] != 209]
        heatmap_chart = graphs.make_icd_spec_heatmap(query_df_heat)
        st.plotly_chart(heatmap_chart, use_container_width=True)

st.markdown("")
st.markdown("")
st.markdown("<h3 style='text-align: center;'>Summary of Charges</h3>", unsafe_allow_html=True)

### SUMMARY OF CHARGES CHART & TABLE

col = st.columns((4.5, 0.5, 1, 0.5))

with col[0]:
    st.markdown('')
    st.markdown('')
    df_period_table = conn.query("Select period,  claims_period_paid, day_count from v_period_summary")
    budget_table = df_period_table.copy()
    budget_table = CorporateTables(budget_table)
    budget_table = budget_table.make_period_budget_table()
    budget_chart = graphs.make_bar_chart_period(budget_table)
    st.plotly_chart(budget_chart, use_container_width=True)

with col[2]:
    st.markdown(" ")
    st.markdown(" ")
    st.markdown(" ")
    st.markdown(" ")
    charge_impact_table = df_period_table.copy()
    charge_impact_table = CorporateTables(charge_impact_table)
    charge_impact_table = charge_impact_table.make_charge_impact_table()
    charge_impact_chart = graphs.make_profit_impact_bar(charge_impact_table)
    st.plotly_chart(charge_impact_chart, use_container_width=True)
