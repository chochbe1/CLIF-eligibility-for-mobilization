'''
ONLY RUN AT UCMC
'''

import pandas as pd
from scipy.stats import chi2_contingency

# Load aggregate data from all sites
# UPDATE AFTER AGGREGATING RESULTS
aggregate_data_all_sites = pd.read_csv('aggregate_data_all_sites.csv')

# Filter data for a specific criterion if needed
criterion = 'Patel'
data = aggregate_data_all_sites[aggregate_data_all_sites['Criteria'] == criterion]

# Construct contingency table
contingency_table = []
for index, row in data.iterrows():
    eligible_hours = row['Eligible Hours']
    non_eligible_hours = row['Total Observed Hours'] - row['Eligible Hours']
    contingency_table.append([eligible_hours, non_eligible_hours])

# Perform Chi-Square Test
chi2, p, dof, expected = chi2_contingency(contingency_table)

print(f"Chi-Square Test for Proportion of Eligible Hours ({criterion} Criterion):")
print(f"Chi2 Statistic: {chi2:.2f}, p-value: {p:.4f}")

# Construct contingency table
contingency_table = []
for index, row in data.iterrows():
    eligible_patients = row['Eligible Patients']
    non_eligible_patients = row['Total Patients'] - row['Eligible Patients']
    contingency_table.append([eligible_patients, non_eligible_patients])

# Perform Chi-Square Test
chi2, p, dof, expected = chi2_contingency(contingency_table)

print(f"Chi-Square Test for Proportion of Patients Eligible ({criterion} Criterion):")
print(f"Chi2 Statistic: {chi2:.2f}, p-value: {p:.4f}")

import matplotlib.pyplot as plt

# Calculate proportions
data['Proportion Eligible Hours'] = data['Eligible Hours'] / data['Total Observed Hours']
data['Proportion Eligible Patients'] = data['Eligible Patients'] / data['Total Patients']

# Plot Proportion of Eligible Hours
plt.figure(figsize=(10, 6))
plt.scatter(data['Site'], data['Proportion Eligible Hours'])
plt.title(f'Proportion of Eligible Hours ({criterion} Criterion)')
plt.xlabel('Site')
plt.ylabel('Proportion of Eligible Hours')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Plot Proportion of Eligible Patients
plt.figure(figsize=(10, 6))
plt.scatter(data['Site'], data['Proportion Eligible Patients'])
plt.title(f'Proportion of Patients Eligible ({criterion} Criterion)')
plt.xlabel('Site')
plt.ylabel('Proportion of Patients Eligible')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


