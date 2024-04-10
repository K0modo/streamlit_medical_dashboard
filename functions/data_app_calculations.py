import functions.data_settings as ds
import numpy as np


class CorporateTables:
    def __init__(self, dataframe):
        self.table = dataframe

    def make_charge_impact_table(self):
        self.table['budget_charges'] = self.table['day_count'] * ds.AVG_PER_DAY
        self.table['Charges Variance'] = self.table['claims_period_paid'] - self.table['budget_charges']
        self.table['P&L Impact'] = round(self.table['Charges Variance'] * ds.WRAP_RATE, 0)
        self.table['Color'] = np.where(self.table['P&L Impact'] < 0, '#DE2C62', '#0083B8')
        self.table.set_index('period', inplace=True)
        self.table.index.names = ['Period']
        self.table.drop(['day_count', 'claims_period_paid', 'budget_charges'], axis=1, inplace=True)

        return self.table

    def make_period_budget_table(self):
        self.table['charge_budget'] = round(self.table['day_count'] * ds.AVG_PER_DAY, 0)
        self.table['charge_variance'] = round(self.table['charge_budget'] - self.table['claims_period_paid'])
        self.table['cum_charge_variance'] = self.table['charge_variance'].cumsum()

        return self.table


class ClaimData:
    def __init__(self, dataframe, current_period):
        self.table = dataframe
        self.a_claims = dataframe.loc[current_period - 1, 'claims_period_count_cum']
        self.a_paid = dataframe.loc[current_period - 1, 'claims_period_paid_cum']
        self.a_ave_per_claim = self.a_paid / self.a_claims
        self.c_claims = dataframe.loc[current_period - 1, 'claims_period_count']
        self.c_paid = dataframe.loc[current_period - 1, 'claims_period_paid']
        self.c_ave_per_claim = self.c_paid / self.c_claims

    def get_select_claims(self, period):
        p_claims = self.table.loc[period - 1, 'claims_period_count']

        return p_claims

    def get_select_paid(self, period):
        p_paid = self.table.loc[period - 1, 'claims_period_paid']

        return p_paid


class ICDGroupData:
    def __init__(self, dataframe):
        self.icd_table = None
        self.row_list = None
        self.table = dataframe

        self.group_table = self.table.groupby('icd_name', as_index=False).agg(Claims=('charge_allowed', 'count'),
                                                                              Charges=('charge_allowed', 'sum'),
                                                                              Average=('charge_allowed', 'mean'),
                                                                              Max=('charge_allowed', 'max')
                                                                              )
        self.group_pivot = self.table.pivot_table(index='icd_name',
                                                  columns='period',
                                                  values='charge_allowed',
                                                  aggfunc='count',
                                                  fill_value=0
                                                  )
        self.joined_table_pivot = self.group_table.merge(self.group_pivot, how='left', left_on=['icd_name'],
                                                         right_index=True)

    def create_group_claims_list(self):
        self.row_list = []

        for i in self.group_pivot.index:
            row = self.group_pivot.loc[i, :].to_list()
            self.row_list.append(row)

        return self.row_list

    def join_claims_list_joined_table(self):
        self.joined_table_pivot['icd_chart_data'] = self.create_group_claims_list()

        return self.joined_table_pivot

    def build_icd_table(self):
        self.icd_table = self.join_claims_list_joined_table()
        self.icd_table = self.icd_table.loc[:, ['icd_name', 'Claims', 'Charges', 'Average', 'Max', 'icd_chart_data']]

        return self.icd_table


class SpecialtyGroupData:
    def __init__(self, dataframe):
        self.row_list = None
        self.specialty_table = None
        self.table = dataframe

        self.group_table = self.table.groupby('specialty_name', as_index=False).agg(Claims=('charge_allowed', 'count'),
                                                                                    Charges=('charge_allowed', 'sum'),
                                                                                    Average=('charge_allowed', 'mean'),
                                                                                    Max=('charge_allowed', 'max')
                                                                                    )
        self.group_pivot = self.table.pivot_table(index='specialty_name',
                                                  columns='period',
                                                  values='charge_allowed',
                                                  aggfunc='count',
                                                  fill_value=0
                                                  )
        self.joined_table_pivot = self.group_table.merge(self.group_pivot, how='left', left_on=['specialty_name'],
                                                         right_index=True)

    def create_group_claims_list(self):
        self.row_list = []

        for i in self.group_pivot.index:
            row = self.group_pivot.loc[i, :].to_list()
            self.row_list.append(row)

        return self.row_list

    def join_claims_list_joined_table(self):
        self.joined_table_pivot['specialty_chart_data'] = self.create_group_claims_list()

        return self.joined_table_pivot

    def build_specialty_table(self):
        self.specialty_table = self.join_claims_list_joined_table()
        self.specialty_table = self.specialty_table.loc[:,
                               ['specialty_name', 'Claims', 'Charges', 'Average', 'Max', 'specialty_chart_data']]

        return self.specialty_table


class ICDData:
    def __init__(self, dataframe, choice):
        self.table = dataframe
        self.choice = choice
        self.table_group = (self.table.groupby('icd_name', as_index=False)
                            .agg(Claims=('charge_allowed', 'count'),
                                 Charges=('charge_allowed', 'sum'),
                                 Average=('charge_allowed', 'mean')
                                 )
                            )
        self.table_group = self.table_group[self.table_group['icd_name'] == self.choice]
        self.claims = self.table_group.iloc[0, 1]
        self.charges = self.table_group.iloc[0, 2]
        self.average = self.table_group.iloc[0, 3]

    def get_member_count(self):
        member_table = self.table.loc[:, ['mem_acct_id', 'icd_name']]
        member_count = member_table[member_table['icd_name'] == self.choice].iloc[:, 0].nunique()

        return member_count

    def get_period_claim_count(self):
        period_table = self.table.groupby(['period', 'icd_name'], as_index=False)['charge_allowed'].count()
        period_table = period_table[period_table['icd_name'] == self.choice]

        return period_table

    def get_specialty_claims(self):
        specialty_table = self.table[self.table['icd_name'] == self.choice]
        specialty_table = (specialty_table.groupby('specialty_name', as_index=False)['charge_allowed']
                           .count()
                           .nlargest(10, 'charge_allowed')
                           )

        return specialty_table
