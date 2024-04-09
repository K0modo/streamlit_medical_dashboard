import streamlit as st
from functions.data_app_calculations import CorporateTables, ClaimData, ICDData
from functions import graphs_app as graphs
import functions.data_settings as ds

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


### Title Row
st.markdown("<h2 style='text-align: center;'>Tynan Analytics Dashboard</h2>", unsafe_allow_html=True)

### SUMMARY OF CHARGES CHART & TABLE
st.markdown("")
st.markdown("<h3 style='text-align: center;'>Annual Budget Variance Summary</h3>", unsafe_allow_html=True)
st.markdown("")

col = st.columns((4, 1, 3, .5))

with col[0]:
    query_1 = conn.query("Select * from v_period_summary")
    corporate_tables = CorporateTables(query_1)

    variance_table = corporate_tables.make_period_budget_table()
    variance_chart = graphs.make_bar_chart_period(variance_table)
    st.plotly_chart(variance_chart, use_container_width=True)

with col[2]:
    st.markdown(" ")
    st.markdown(" ")

    charge_impact_table = corporate_tables.make_charge_impact_table()
    charge_impact_chart = graphs.make_profit_impact_bar(charge_impact_table)
    st.plotly_chart(charge_impact_chart, use_container_width=True)


###  Statistics Rows
st.markdown("")
col = st.columns((1, 1, 1))

with col[1]:
    st.subheader("Summary of Claims")

col = st.columns(8)

with col[0]:
    select_period = st.selectbox("Select Period:", ds.PERIOD_LIST)

col = st.columns((2, 2, 2, 2, 2))

with col[0]:
    annual_stats = conn.query("Select * from v_period_summary")

    annual_data = ClaimData(annual_stats, ds.CURRENT_PERIOD)
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

with st.expander("TOP 10 CLAIMS PROCESSED"):

    col = st.columns((4, 0.5, 4))

    with col[0]:
        table_title = 'Injury_Disease'
        icd_racing_table = conn.query("Select name, period, claim_count_ytd from v_icd_racing")
        icd_racing_chart = graphs.make_icd_racing_chart(icd_racing_table, table_title)
        st.plotly_chart(icd_racing_chart, use_container_width=True)

    with col[2]:
        table_title = 'Provider Specialty'
        specialty_racing_table = conn.query(
            "Select name, period, claim_count_ytd from v_specialty_racing where "
            "name != 'Hospital_Clinic'")
        specialty_racing_chart = graphs.make_icd_racing_chart(specialty_racing_table, table_title)
        st.plotly_chart(specialty_racing_chart, use_container_width=True)

st.markdown("")

### ICD Table

with st.expander("ICD TABLE"):
    col = st.columns([2, 7, 1])

    with col[1]:
        query = conn.query("""
            Select period, mem_acct_id, injury_disease_id, t_injury_disease.name as icd_name, specialty_id, 
            t_specialty.name as specialty_name, 
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

st.markdown("")

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

st.markdown("")

with st.expander("HEATMAP"):
    col = st.columns([1, 7, 1])

    with col[1]:
        query_df_heat = query_df[query_df['specialty_id'] != 209]
        heatmap_chart = graphs.make_icd_spec_heatmap(query_df_heat)
        st.plotly_chart(heatmap_chart, use_container_width=True)

st.markdown("")

with st.expander("ICD SELECTION"):

    query_df = query.copy()
    icd_options = query_df['icd_name'].drop_duplicates().sort_values()

    col = st.columns(5)

    with col[0]:
        choice = st.selectbox('Select an Injury or Disease', icd_options)
        st.markdown("")

        icd_stats = ICDData(query_df, choice)

    col = st.columns((2, 2, 2, 2, 2))

    with col[0]:
        st.markdown("Selection")
        st.markdown(choice)

    with col[1]:
        st.markdown("Claims Processed")
        st.markdown(f'{icd_stats.claims:,}')

    with col[2]:
        st.markdown("Claim Charges")
        st.markdown(f'$ {icd_stats.charges:,.0f}')

    with col[3]:
        st.markdown("Average Charges")
        st.markdown(f'$ {icd_stats.average:,.2f}')

    with col[4]:
        st.markdown("Members")
        st.markdown(f'{icd_stats.get_member_count()}')

    st.markdown("")

    col = st.columns((3, 1, 4))

    with col[0]:
        icd_choices = icd_stats.get_period_claim_count()
        fig = graphs.make_icd_period_bar_chart(icd_choices, choice)
        st.plotly_chart(fig, use_container_width=True)

    with col[2]:
        choice_from_icd_choice = icd_stats.get_specialty_claims()
        fig = graphs.make_icd_specialty_bar_chart(choice_from_icd_choice, choice)
        st.plotly_chart(fig, use_container_width=True)
