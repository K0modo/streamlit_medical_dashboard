import functions.data_settings as ds
import numpy as np


class CorporateTables:
    def __init__(self, dataframe):
        self.table = dataframe

    def make_charge_impact_table(self):
        self.table['budget_charges'] = self.table['day_count'] * ds.AVG_PER_DAY
        self.table['Charges Variance'] = self.table['claims_period_paid'] - self.table['budget_charges']
        self.table['P&L Impact'] = round(self.table['Charges Variance'] * ds.WRAP_RATE, 0)
        self.table['Color'] = np.where(self.table['P&L Impact']<0,'#DE2C62', '#0083B8')
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
    def __init__(self, dataframe):
        self.table = dataframe
        self.a_claims = dataframe.loc[11, 'claims_period_count_cum']
        self.a_paid = dataframe.loc[11, 'claims_period_paid_cum']
        self.a_ave_per_claim = self.a_paid / self.a_claims
        self.c_claims = dataframe.loc[11, 'claims_period_count']
        self.c_paid = dataframe.loc[11, 'claims_period_paid']
        self.c_ave_per_claim = self.c_paid / self.c_claims

    def get_select_claims(self, period):
        self.p_claims = self.table.loc[period, 'claims_period_count']

        return self.p_claims

    def get_select_paid(self, period):
        self.p_paid = self.table.loc[period, 'claims_period_paid']

        return self.p_paid

    def get_select_average(self):
        self.p_average = self.p_paid / self.p_claims

        return self.p_average
