# Recommendation System

This repository contains a python-based recommendation system. The script connects to a MySQL database, fetches data, conducts frequent itemset mining, and then generates recommendation rules based on the results. These rules are then stored back into the MySQL database. 

## File Structure

The repository contains the following key python script:
```
Recommendation_System/
│
├── README.md # The file you're currently reading
│
├── recommendation_system.py # Main Python script file which contains the implementation of the recommendation system
│
├── credentials.py # File containing credentials for the database connection
│
├── requirements.txt # Contains a list of python dependencies required to run the project
│
├── .gitignore # Specifies intentionally untracked files to ignore when using Git
│
└── data/ # Directory that contains all the data-related files
│
├── raw/ # Directory that contains the raw, untouched data
│ └── initial_data.csv
│
└── processed/ # Directory that contains cleaned and processed data
└── cleaned_data.csv
```
## Prerequisites

Ensure that the following libraries are installed in your Python environment:

- pandas
- mysql-connector-python
- collections
- sys
- operator
- time
- sqlalchemy
- credentials (custom module)

## Installation and Running the Script

1. Clone the repository to your local machine.
2. Make sure you have all the required libraries installed in your Python environment.
3. You should have a file named `credentials.py` in your project folder with variables `host`, `database`, `user`, and `password` for connecting to your MySQL database.
4. Run the `recommendation_engine.py` script.

Here's a small snippet of how to run the script:

```python
obj = RecommendationEngineASS(credentials.host,  credentials.database, credentials.user, credentials.password)    
obj.connectDB()
c_data, data = obj.getDF()
```
# Methodology
1. The script establishes a connection to the MySQL database using the provided credentials.
2. It fetches the relevant data from the database, which includes details of customers' purchases.
3. It cleans and processes the data, then uses the Apriori algorithm to find frequent itemsets among the purchased items.

```
frequent_itemsets[1] = dict((fproduct_id,)),row['Quantity']) for product_id,row in num_favor_by_product.iterrows() if row['Quantity'] > min_support)

for k in range(2,3):
    cur_frequent_itemsets = obj.find_frequent_itemsets(bought_by_users,frequent_itemsets[k-1],min_support) ```
    
4. Using these frequent itemsets, the script generates rules that define what items customers are likely to buy together.
```
for itemset_length,itemset_counts in frequent_itemsets.items():
    for itemset in itemset_counts.keys():
        for conclusion in itemset:
            premise = itemset - set((conclusion,))
            candidate_rules.append((premise,conclusion))
```

5. It then computes the confidence for these rules and filters out those with a confidence level below a certain threshold.
```
rule_confidence = {candidate_rule: correct_counts[candidate_rule] / float(correct_counts[candidate_rule] + incorrect_counts[candidate_rule])
                    for candidate_rule in candidate_rules}
min_confidence = 0.4
rule_confidence = {rule: confidence for rule,confidence in rule_confidence.items() if confidence > min_confidence}
```

6. The resulting high-confidence rules are then stored back into the MySQL database.
```
df = pd.DataFrame(columns=["id", "if_bought", "then_also", "created_at", "updated_at"])
for i in range(len(test_confidence)):
    premise,conclusion = sort_confidence[i][0]
    premise_name = ", ".join(str(idx) for idx in premise)
    conclusion_name = str(conclusion)
    df.loc[len(df)] = [len(df)+1,premise_name,conclusion_name,pd.to_datetime('now').strftime("%Y-%m-%d %H:%M:%S"),pd.to_datetime('now').strftime("%Y-%m-%d %H:%M:%S")]
obj.insertToDB(credentials.host,  credentials.database, credentials.user, credentials.password ,df.sort_values('id') )
```

## Results

The recommendation system generates a set of association rules based on the products purchased by users. Each rule signifies a particular association between products. For example, a rule such as `{Product A} -> {Product B}` implies that if a customer buys Product A, they are likely to also buy Product B.

This model's accuracy can be determined by the confidence level of these rules. The higher the confidence level, the more accurate the rule.

```python
sort_confidence = sorted(rule_confidence.items(),key=itemgetter(1),reverse = True)
for index in range(5):  # Top 5 rules
    premise, conclusion = sort_confidence[index][0]
    premise_names = ", ".join(get_product_name(idx) for idx in premise)
    conclusion_name = get_product_name(conclusion)
    print(f"Rule #{index+1}: If a person buys {premise_names}, they will also buy {conclusion_name}")
    print(f"- Confidence: {sort_confidence[index][1]*100:.2f}%")
```

All the generated rules are stored in a MySQL database for easy access and usage in any other application.

The effectiveness of the recommendation system can be seen in the form of increased sales, greater customer satisfaction, and increased relevance of suggested products to customers.

Please remember, results may vary based on the data, minimum support, and confidence levels set. Experimenting with different configurations will yield different sets of rules and thus, different recommendation behaviors.

# Future Improvements
For future enhancements, one could consider:

1. Incorporating user feedback to validate recommendations and continuously improve the system.
2. Utilizing other types of data such as user demographic information or product details to make more personalized recommendations.
3. Experimenting with different machine learning models and comparing their performance.
